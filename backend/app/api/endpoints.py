from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from ..models import SiteCreate, SiteStatus, SiteCheck, MonitorStats
from ..database import (
    add_site, get_sites, get_site_status, get_site_history, 
    delete_site as db_delete_site, DATABASE_PATH,
    add_agent, get_agents, delete_agent
)
from ..monitor import get_monitor
from ..config import Settings, get_settings
import aiosqlite
import ssl
import socket
from urllib.parse import urlparse
from pydantic import BaseModel, constr, validator
import re
import hashlib

router = APIRouter()
ph = PasswordHasher()

# Pydantic models
class SiteCreate(BaseModel):
    url: str
    name: constr(min_length=1)
    scan_interval: str

    @validator('scan_interval')
    def validate_scan_interval(cls, v, values, **kwargs):
        settings: Settings = get_settings()
        min_seconds = settings.MIN_SCAN_INTERVAL_SECONDS
        max_seconds = settings.MAX_SCAN_INTERVAL_SECONDS
        
        try:
            match = re.match(r'^(\d+(?:\.\d+)?)([smh])$', v.strip().lower())
            if not match:
                raise ValueError("Invalid format. Use 's', 'm', 'h' (e.g., '30s', '5m', '1h').")

            value, unit = match.groups()
            value = float(value)

            if unit == 's':
                seconds = value
            elif unit == 'm':
                seconds = value * 60
            elif unit == 'h':
                seconds = value * 3600
            
            if not (min_seconds <= seconds <= max_seconds):
                raise ValueError(f"Scan interval must be between {min_seconds}s and {max_seconds}s.")
            
        except ValueError as e:
            raise ValueError(str(e))
        
        return v

class ManualCheckRequest(BaseModel):
    site_ids: Optional[List[int]] = None

class AgentCreate(BaseModel):
    name: constr(min_length=1)
    api_key: constr(min_length=64)
    description: Optional[str] = None

    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v) < 64:
            raise ValueError("API key must be at least 64 characters long")
        return v

@router.post("/sites", response_model=dict)
async def create_site(site: SiteCreate):
    """Add a new site to monitor."""
    try:
        site_id = await add_site(str(site.url), site.name, site.scan_interval)
        # Refresh monitoring to pick up the new site
        from ..monitor import monitor
        await monitor.refresh_monitoring()
        return {"id": site_id, "message": "Site added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sites", response_model=List[dict])
async def list_sites():
    """Get all sites being monitored."""
    return await get_sites()

@router.get("/sites/status", response_model=List[dict])
async def get_sites_status():
    """Get current status of all sites being monitored with security information."""
    sites_status = await get_site_status()
    
    # Enhance each site with security information
    enhanced_sites = []
    for site in sites_status:
        # Detect if this is an agent (check if URL uses port 8081 or has agent-like characteristics)
        url = site.get('url', '')
        is_agent = (
            ':8081' in url or 
            'agent' in url.lower() or 
            site.get('name', '').lower().startswith('agent')
        )
        
        try:
            if is_agent:
                # Get agent-specific security info
                security_info = await get_agent_security_info(url)
            else:
                # Get regular site security info
                security_info = await get_site_security_info(url)
            
            # Merge security info with site data
            enhanced_site = {**site, **security_info}
            enhanced_sites.append(enhanced_site)
            
        except Exception as e:
            print(f"Failed to get security info for {url}: {e}")
            # Add default security info on error
            enhanced_site = {
                **site,
                'connection_type': 'agent' if is_agent else 'resource',
                'protocol': 'unknown',
                'is_encrypted': False,
                'connection_status': 'error'
            }
            enhanced_sites.append(enhanced_site)
    
    return enhanced_sites

@router.get("/sites/{site_id}/history", response_model=List[dict])
async def get_site_check_history(site_id: int, limit: int = 100):
    """Get check history for a specific site."""
    if limit > 1000:
        limit = 1000
    return await get_site_history(site_id, limit)

@router.delete("/sites/{site_id}", response_model=dict)
async def delete_site(site_id: int):
    """Delete a site and stop monitoring it."""
    try:
        await db_delete_site(site_id)
        # Refresh monitoring to stop monitoring the deleted site
        from ..monitor import monitor
        await monitor.refresh_monitoring()
        return {"message": "Site deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/check/manual", response_model=dict)
async def manual_check(request: ManualCheckRequest):
    """Manually trigger a check of specified sites, or all sites if none are specified."""
    try:
        monitor = get_monitor()
        # If site_ids is None, check_sites_by_id will check all sites
        results = await monitor.check_sites_by_id(request.site_ids)
        return {"message": f"Checked {len(results)} sites", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=dict)
async def get_monitoring_stats():
    """Get monitoring statistics."""
    try:
        stats = await get_monitor().get_stats()
        return {
            "total_sites": stats["total_sites"],
            "sites_up": stats["sites_up"],
            "sites_down": stats["sites_down"],
            "average_response_time": stats["average_response_time"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_app_config(settings: Settings = Depends(get_settings)):
    return {
        "scan_interval": {
            "min_seconds": settings.MIN_SCAN_INTERVAL_SECONDS,
            "max_seconds": settings.MAX_SCAN_INTERVAL_SECONDS,
            "range_description": settings.scan_interval_range_description,
            "development_mode": settings.DEVELOPMENT_MODE
        }
    }

@router.get("/sites/analytics", response_model=dict)
async def get_sites_analytics(
    site_ids: str = None,  # Comma-separated site IDs, or "all" for all sites
    hours: float = 1,        # Number of hours back to fetch data (supports fractions)
    interval_minutes: float = 5  # Data point interval in minutes (supports fractions)
):
    """Get historical response time data for charting."""
    try:
        from datetime import datetime, timedelta, timezone
        import json
        
        # Parse site IDs
        if site_ids and site_ids.lower() != "all":
            selected_site_ids = [int(sid.strip()) for sid in site_ids.split(",")]
        else:
            # Get all site IDs
            sites = await get_sites()
            selected_site_ids = [site['id'] for site in sites]
        
        if not selected_site_ids:
            return {"data": [], "sites": []}
        
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Use smaller intervals for very short time ranges
        if hours < 0.0167:  # Less than 1 minute
            # For very short ranges, use 1-second intervals to catch any available data
            interval_seconds = 1
        elif hours < 0.0833:  # Less than 5 minutes
            # For short ranges, use appropriate intervals
            interval_seconds = max(1, int(hours * 3600 / 30))  # ~30 data points
        else:
            interval_seconds = int(interval_minutes * 60)  # Convert minutes to seconds
        
        # Get site information for the selected sites
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # Get detailed site information including latest status
            placeholders = ','.join(['?' for _ in selected_site_ids])
            sites_cursor = await db.execute(f"""
                SELECT 
                    s.id,
                    s.name,
                    s.url,
                    s.scan_interval,
                    sc.status,
                    sc.response_time,
                    sc.status_code,
                    sc.error_message,
                    sc.checked_at
                FROM sites s
                LEFT JOIN site_checks sc ON s.id = sc.site_id
                WHERE s.id IN ({placeholders})
                  AND (sc.checked_at = (
                      SELECT MAX(checked_at) 
                      FROM site_checks 
                      WHERE site_id = s.id
                  ) OR sc.checked_at IS NULL)
                ORDER BY s.name
            """, selected_site_ids)
            
            sites_rows = await sites_cursor.fetchall()
            sites_info = {}
            
            # Parse URLs to extract hostname and IP info
            from urllib.parse import urlparse
            import socket
            
            for row in sites_rows:
                site_data = dict(row)
                
                # Parse URL to get hostname
                try:
                    parsed_url = urlparse(site_data['url'])
                    hostname = parsed_url.hostname or parsed_url.netloc
                    
                    # Try to resolve IP address
                    try:
                        ip_address = socket.gethostbyname(hostname) if hostname else None
                    except (socket.gaierror, socket.error):
                        ip_address = None
                        
                except Exception:
                    hostname = site_data['url']
                    ip_address = None
                
                sites_info[site_data['id']] = {
                    'name': site_data['name'],
                    'url': site_data['url'],
                    'hostname': hostname,
                    'ip_address': ip_address,
                    'last_status': site_data['status'],
                    'last_response_time': site_data['response_time'],
                    'last_status_code': site_data['status_code'],
                    'last_checked_at': site_data['checked_at'],
                    'scan_interval': site_data['scan_interval']
                }
            
            # Get historical data
            data_cursor = await db.execute("""
                SELECT 
                    site_id,
                    response_time,
                    status,
                    checked_at,
                    datetime(checked_at) as timestamp
                FROM site_checks 
                WHERE site_id IN ({}) 
                  AND datetime(checked_at) >= datetime(?) 
                  AND datetime(checked_at) <= datetime(?)
                  AND response_time IS NOT NULL
                ORDER BY checked_at ASC
            """.format(placeholders), selected_site_ids + [start_time.isoformat(), end_time.isoformat()])
            
            checks = await data_cursor.fetchall()
            
        # Group data by time intervals
        from collections import defaultdict
        import math
        
        # Create time buckets
        time_buckets = defaultdict(lambda: defaultdict(list))
        
        for check in checks:
            # Parse timestamp and ensure it's timezone-aware
            timestamp_str = check['timestamp']
            try:
                check_time = datetime.fromisoformat(timestamp_str)
                # If no timezone info, assume UTC (which SQLite uses)
                if check_time.tzinfo is None:
                    check_time = check_time.replace(tzinfo=timezone.utc)
            except ValueError:
                # Handle different timestamp formats
                check_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            
            # Round to nearest interval
            bucket_timestamp = start_time + timedelta(
                seconds=math.floor((check_time - start_time).total_seconds() / interval_seconds) * interval_seconds
            )
            bucket_key = bucket_timestamp.isoformat()
            
            if check['response_time'] is not None and check['status'] == 'up':
                time_buckets[bucket_key][check['site_id']].append(check['response_time'])
        
        # Format data for chart with interpolation
        chart_data = []
        current_time = start_time
        
        # First pass: collect actual data points
        actual_data_points = {}
        while current_time <= end_time:
            bucket_key = current_time.isoformat()
            data_point = {
                "timestamp": current_time.strftime("%H:%M"),
                "full_timestamp": current_time.isoformat()
            }
            
            # Add actual response times for each site
            has_data = False
            for site_id in selected_site_ids:
                response_times = time_buckets.get(bucket_key, {}).get(site_id, [])
                
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    data_point[f"site_{site_id}"] = round(avg_response_time * 1000, 2)  # Convert to ms
                    has_data = True
                    # Store for interpolation
                    if site_id not in actual_data_points:
                        actual_data_points[site_id] = []
                    actual_data_points[site_id].append((current_time, avg_response_time * 1000))
            
            if has_data:
                chart_data.append(data_point)
            
            current_time += timedelta(seconds=interval_seconds)
        
        # Interpolate missing data points for smooth charts
        if interval_seconds <= 5:  # Only interpolate for very fine-grained time ranges
            interpolated_data = []
            current_time = start_time
            
            while current_time <= end_time:
                data_point = {
                    "timestamp": current_time.strftime("%H:%M:%S") if interval_seconds <= 60 else current_time.strftime("%H:%M"),
                    "full_timestamp": current_time.isoformat()
                }
                
                for site_id in selected_site_ids:
                    if site_id in actual_data_points and len(actual_data_points[site_id]) >= 2:
                        # Find surrounding data points for interpolation
                        site_points = actual_data_points[site_id]
                        
                        # Find the two closest points
                        before = None
                        after = None
                        for i, (point_time, value) in enumerate(site_points):
                            if point_time <= current_time:
                                before = (point_time, value)
                            if point_time >= current_time and after is None:
                                after = (point_time, value)
                                break
                        
                        # Interpolate value
                        if before and after and before[0] != after[0]:
                            # Linear interpolation
                            time_diff = (after[0] - before[0]).total_seconds()
                            current_diff = (current_time - before[0]).total_seconds()
                            ratio = current_diff / time_diff
                            interpolated_value = before[1] + (after[1] - before[1]) * ratio
                            data_point[f"site_{site_id}"] = round(interpolated_value, 2)
                        elif before:
                            # Use last known value
                            data_point[f"site_{site_id}"] = before[1]
                        elif after:
                            # Use next known value
                            data_point[f"site_{site_id}"] = after[1]
                
                interpolated_data.append(data_point)
                current_time += timedelta(seconds=1)  # 1-second resolution for smooth display
            
            chart_data = interpolated_data[:300]  # Limit to 300 points for performance
        
        # Calculate overall average for all sites combined
        if len(selected_site_ids) >= 1:
            for point in chart_data:
                site_values = [point.get(f"site_{site_id}") for site_id in selected_site_ids 
                              if point.get(f"site_{site_id}") is not None]
                if site_values:
                    point["average"] = round(sum(site_values) / len(site_values), 2)
                else:
                    point["average"] = None
        
        return {
            "data": chart_data,
            "sites": [
                {
                    "id": site_id, 
                    "name": sites_info.get(site_id, {}).get('name', f'Site {site_id}'),
                    "url": sites_info.get(site_id, {}).get('url'),
                    "hostname": sites_info.get(site_id, {}).get('hostname'),
                    "ip_address": sites_info.get(site_id, {}).get('ip_address'),
                    "last_status": sites_info.get(site_id, {}).get('last_status'),
                    "last_response_time": sites_info.get(site_id, {}).get('last_response_time'),
                    "last_status_code": sites_info.get(site_id, {}).get('last_status_code'),
                    "last_checked_at": sites_info.get(site_id, {}).get('last_checked_at'),
                    "scan_interval": sites_info.get(site_id, {}).get('scan_interval')
                }
                for site_id in selected_site_ids
            ],
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{site_id}/refresh-security", response_model=dict)
async def refresh_agent_security(site_id: int):
    """Manually refresh security information for a specific agent."""
    try:
        # Get the site information
        sites = await get_sites()
        site = next((s for s in sites if s['id'] == site_id), None)
        
        if not site:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        url = site['url']
        is_agent = (
            ':8081' in url or 
            'agent' in url.lower() or 
            site.get('name', '').lower().startswith('agent')
        )
        
        if is_agent:
            security_info = await get_agent_security_info(url)
        else:
            security_info = await get_site_security_info(url)
        
        return {
            "message": "Security information refreshed successfully",
            "site_id": site_id,
            "security_info": security_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_site_security_info(url: str) -> dict:
    """Get SSL/TLS security information for a site."""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        security_info = {
            'protocol': parsed_url.scheme,
            'is_encrypted': parsed_url.scheme in ['https', 'wss'],
            'hostname': hostname,
            'port': port,
            'tls_version': None,
            'cipher_suite': None,
            'key_strength': None,
            'http_version': None
        }
        
        if security_info['is_encrypted'] and hostname:
            try:
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect to get SSL info
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        # Get SSL information
                        security_info.update({
                            'tls_version': ssock.version(),
                            'cipher_suite': ssock.cipher()[0] if ssock.cipher() else None,
                            'key_strength': ssock.cipher()[2] if ssock.cipher() else None,
                        })
                        
                        # Detect HTTP version (basic detection)
                        if parsed_url.scheme == 'https':
                            try:
                                import httpx
                                async with httpx.AsyncClient(timeout=5) as client:
                                    response = await client.get(url)
                                    security_info['http_version'] = f"HTTP/{response.http_version}"
                            except:
                                security_info['http_version'] = 'HTTP/1.1'  # fallback
                        
            except Exception as e:
                print(f"Failed to get security info for {url}: {e}")
        
        return security_info
        
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return {
            'protocol': 'unknown',
            'is_encrypted': False,
            'hostname': url,
            'port': None,
            'tls_version': None,
            'cipher_suite': None,
            'key_strength': None,
            'http_version': None
        }

async def get_agent_security_info(url: str, agent_port: str = "8081") -> dict:
    """Get security information for agent connections with fallback protocol detection."""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname or parsed_url.netloc
        
        security_info = {
            'connection_type': 'agent',
            'agent_port': agent_port,
            'hostname': hostname,
            'ip_address': None,
            'protocol': None,
            'is_encrypted': False,
            'tls_version': None,
            'cipher_suite': None,
            'key_strength': None,
            'http_version': None,
            'connection_status': 'disconnected',
            'fallback_used': False
        }
        
        # Try to resolve IP address
        try:
            if hostname:
                security_info['ip_address'] = socket.gethostbyname(hostname)
        except (socket.gaierror, socket.error):
            pass
        
        # Try WSS first (WebSocket Secure)
        try:
            wss_url = f"wss://{hostname}:{agent_port}/agent/ws"
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, int(agent_port)), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    security_info.update({
                        'protocol': 'wss',
                        'is_encrypted': True,
                        'tls_version': ssock.version(),
                        'cipher_suite': ssock.cipher()[0] if ssock.cipher() else None,
                        'key_strength': ssock.cipher()[2] if ssock.cipher() else None,
                        'connection_status': 'connected',
                        'fallback_used': False
                    })
                    return security_info
        except Exception as e:
            print(f"WSS connection failed for agent {hostname}:{agent_port}: {e}")
        
        # Fallback to HTTPS with HTTP/2 detection
        try:
            https_url = f"https://{hostname}:{agent_port}/api/sites"
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, int(agent_port)), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Try to detect HTTP version
                    try:
                        import httpx
                        async with httpx.AsyncClient(timeout=5, http2=True) as client:
                            response = await client.get(https_url)
                            http_version = f"HTTP/{response.http_version}"
                    except:
                        http_version = "HTTP/1.1"  # fallback
                    
                    security_info.update({
                        'protocol': 'https',
                        'is_encrypted': True,
                        'tls_version': ssock.version(),
                        'cipher_suite': ssock.cipher()[0] if ssock.cipher() else None,
                        'key_strength': ssock.cipher()[2] if ssock.cipher() else None,
                        'http_version': http_version,
                        'connection_status': 'connected',
                        'fallback_used': True
                    })
                    return security_info
        except Exception as e:
            print(f"HTTPS fallback failed for agent {hostname}:{agent_port}: {e}")
        
        # Final fallback to HTTP/1.1
        try:
            http_url = f"http://{hostname}:{agent_port}/api/sites"
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(http_url)
                security_info.update({
                    'protocol': 'http',
                    'is_encrypted': False,
                    'http_version': "HTTP/1.1",
                    'connection_status': 'connected',
                    'fallback_used': True
                })
        except Exception as e:
            print(f"HTTP fallback failed for agent {hostname}:{agent_port}: {e}")
            security_info['connection_status'] = 'failed'
        
        return security_info
        
    except Exception as e:
        print(f"Error getting agent security info for {url}: {e}")
        return {
            'connection_type': 'agent',
            'agent_port': agent_port,
            'hostname': url,
            'ip_address': None,
            'protocol': 'unknown',
            'is_encrypted': False,
            'tls_version': None,
            'cipher_suite': None,
            'key_strength': None,
            'http_version': None,
            'connection_status': 'error',
            'fallback_used': False
        }

# Agent Management Endpoints

@router.get("/agents", response_model=List[dict])
async def list_agents():
    """Get all registered agents."""
    agents = await get_agents()
    # Don't return the actual API key hash for security
    return [
        {
            "id": agent["id"],
            "name": agent["name"],
            "description": agent["description"],
            "status": agent["status"],
            "last_seen": agent["last_seen"],
            "created_at": agent["created_at"]
        }
        for agent in agents
    ]

@router.post("/agents", response_model=dict)
async def create_agent(agent: AgentCreate):
    """Add a new agent by hashing the provided API key."""
    try:
        # Hash the API key using SHA-256
        api_key_hash = hashlib.sha256(agent.api_key.encode()).hexdigest()
        
        # Add agent to database
        agent_id = await add_agent(agent.name, api_key_hash, agent.description)
        
        return {
            "id": agent_id,
            "message": "Agent added successfully",
            "name": agent.name,
            "description": agent.description
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="An agent with this API key already exists")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}", response_model=dict)
async def delete_agent_endpoint(agent_id: int):
    """Delete an agent."""
    try:
        await delete_agent(agent_id)
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 