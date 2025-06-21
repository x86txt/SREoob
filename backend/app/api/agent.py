from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging
from datetime import datetime

from ..config import Settings, get_settings
from ..database import record_check, get_sites, get_agent_by_hash, update_agent_status, add_agent, get_agents, delete_agent
from ..monitor import get_monitor

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
ph = PasswordHasher()

# Connected agents registry
connected_agents: Dict[str, WebSocket] = {}

# Pydantic models for agent communication
class AgentRegistration(BaseModel):
    agent_id: str
    hostname: str
    version: str = "1.0"
    capabilities: List[str] = ["http", "ping"]

class AgentCheckResult(BaseModel):
    site_id: int
    status: str  # "up" or "down"
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: Optional[str] = None

class WebSocketMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None

# Agent authentication dependency
async def authenticate_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    api_key = credentials.credentials
    api_key_hash = ph.hash(api_key)
    
    # Check if agent exists in database
    agent = await get_agent_by_hash(api_key_hash)
    if not agent:
        # Try to verify against all stored hashes (for backward compatibility)
        agents = await get_agents()
        for stored_agent in agents:
            try:
                ph.verify(stored_agent['api_key_hash'], api_key)
                # Update agent status to online
                await update_agent_status(stored_agent['api_key_hash'], 'online')
                return api_key
            except VerifyMismatchError:
                continue
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update agent status to online
    await update_agent_status(agent['api_key_hash'], 'online')
    return api_key

# Alternative authentication for WebSocket (via query param or header)
async def authenticate_agent_websocket(websocket: WebSocket) -> bool:
    # Try to get API key from query parameters first
    api_key = websocket.query_params.get("api_key")
    
    # If not in query params, try headers
    if not api_key:
        api_key = websocket.headers.get("x-api-key") or websocket.headers.get("authorization")
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # Remove "Bearer " prefix
    
    if not api_key:
        return False
    
    # Check against all stored agent hashes
    agents = await get_agents()
    for agent in agents:
        try:
            ph.verify(agent['api_key_hash'], api_key)
            # Update agent status to online
            await update_agent_status(agent['api_key_hash'], 'online')
            return True
        except VerifyMismatchError:
            continue
    
    return False

@router.post("/agent/register")
async def register_agent(
    registration: AgentRegistration,
    api_key: str = Depends(authenticate_agent)
):
    """Register a new monitoring agent."""
    logger.info(f"Agent registered: {registration.agent_id} from {registration.hostname}")
    
    return {
        "message": "Agent registered successfully",
        "agent_id": registration.agent_id,
        "server_time": datetime.utcnow().isoformat(),
        "capabilities": registration.capabilities
    }

@router.get("/agent/sites")
async def get_agent_sites(api_key: str = Depends(authenticate_agent)):
    """Get list of sites for agent monitoring."""
    sites = await get_sites()
    return sites

@router.post("/agent/checks")
async def submit_check_results(
    results: List[AgentCheckResult],
    api_key: str = Depends(authenticate_agent)
):
    """Submit check results from agent."""
    submitted_count = 0
    errors = []
    
    for result in results:
        try:
            # Use current time if not provided
            checked_at = result.checked_at or datetime.utcnow().isoformat()
            
            await record_check(
                site_id=result.site_id,
                status=result.status,
                response_time=result.response_time,
                status_code=result.status_code,
                error_message=result.error_message
            )
            submitted_count += 1
            logger.debug(f"Recorded check result for site {result.site_id}: {result.status}")
            
        except Exception as e:
            error_msg = f"Failed to record check for site {result.site_id}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    response = {
        "submitted": submitted_count,
        "total": len(results)
    }
    
    if errors:
        response["errors"] = errors
    
    return response

@router.websocket("/agent/ws")
async def agent_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication."""
    
    # Authenticate the WebSocket connection
    if not await authenticate_agent_websocket(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return
    
    await websocket.accept()
    
    # Get agent ID from query params or generate one
    agent_id = websocket.query_params.get("agent_id", f"agent_{id(websocket)}")
    connected_agents[agent_id] = websocket
    
    logger.info(f"Agent {agent_id} connected via WebSocket")
    
    try:
        # Send initial site list
        sites = await get_sites()
        await websocket.send_text(json.dumps({
            "type": "sites_updated",
            "data": sites
        }))
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_agent_message(websocket, agent_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from agent {agent_id}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }))
            except Exception as e:
                logger.error(f"Error handling message from agent {agent_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "data": {"message": "Internal server error"}
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up
        if agent_id in connected_agents:
            del connected_agents[agent_id]
        logger.info(f"Agent {agent_id} disconnected")

async def handle_agent_message(websocket: WebSocket, agent_id: str, message: dict):
    """Handle incoming WebSocket messages from agents."""
    msg_type = message.get("type")
    data = message.get("data", {})
    
    if msg_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({"type": "pong"}))
        
    elif msg_type == "check_result":
        # Handle check result submission
        try:
            result = AgentCheckResult(**data)
            await record_check(
                site_id=result.site_id,
                status=result.status,
                response_time=result.response_time,
                status_code=result.status_code,
                error_message=result.error_message
            )
            
            # Send acknowledgment
            await websocket.send_text(json.dumps({
                "type": "check_result_ack",
                "data": {"site_id": result.site_id, "status": "recorded"}
            }))
            
        except Exception as e:
            logger.error(f"Failed to process check result from agent {agent_id}: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": f"Failed to process check result: {str(e)}"}
            }))
            
    elif msg_type == "request_sites":
        # Send current site list
        sites = await get_sites()
        await websocket.send_text(json.dumps({
            "type": "sites_updated", 
            "data": sites
        }))
        
    else:
        logger.warning(f"Unknown message type '{msg_type}' from agent {agent_id}")

# Utility function to broadcast messages to all connected agents
async def broadcast_to_agents(message: dict):
    """Broadcast a message to all connected agents."""
    if not connected_agents:
        return
    
    message_text = json.dumps(message)
    disconnected_agents = []
    
    for agent_id, websocket in connected_agents.items():
        try:
            await websocket.send_text(message_text)
        except Exception as e:
            logger.warning(f"Failed to send message to agent {agent_id}: {e}")
            disconnected_agents.append(agent_id)
    
    # Clean up disconnected agents
    for agent_id in disconnected_agents:
        if agent_id in connected_agents:
            del connected_agents[agent_id]

# Function to notify agents when sites are updated
async def notify_agents_sites_updated():
    """Notify all connected agents that sites have been updated."""
    sites = await get_sites()
    await broadcast_to_agents({
        "type": "sites_updated",
        "data": sites
    })

@router.get("/agent/status")
async def get_agent_status(api_key: str = Depends(authenticate_agent)):
    """Get status of connected agents."""
    return {
        "connected_agents": len(connected_agents),
        "agent_ids": list(connected_agents.keys())
    } 