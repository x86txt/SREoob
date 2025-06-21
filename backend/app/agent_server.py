import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api import agent
from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def agent_lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting SiteUp Agent Server on port {settings.AGENT_PORT}")
    yield
    # Shutdown
    logger.info("Agent server shutdown complete")

# Create dedicated agent FastAPI app
agent_app = FastAPI(
    title="SiteUp Agent Server",
    description="Dedicated server for agent communication",
    version="1.0.0",
    lifespan=agent_lifespan
)

# Configure CORS for agent communication
agent_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Agents can connect from anywhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only agent routes
agent_app.include_router(agent.router, prefix="")

@agent_app.get("/")
async def agent_root():
    return {
        "message": "SiteUp Agent Communication Server",
        "version": "1.0.0",
        "port": settings.AGENT_PORT
    }

@agent_app.get("/health")
async def agent_health():
    return {"status": "healthy", "service": "agent-server"}

def run_agent_server():
    """Run the agent server on the configured port."""
    uvicorn.run(
        "backend.app.agent_server:agent_app",
        host="0.0.0.0",
        port=settings.AGENT_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        # Enable HTTP/2 support
        http="h2",
        # SSL configuration for WSS (in production, you'd provide actual certs)
        # ssl_keyfile="path/to/key.pem",
        # ssl_certfile="path/to/cert.pem",
    )

if __name__ == "__main__":
    run_agent_server() 