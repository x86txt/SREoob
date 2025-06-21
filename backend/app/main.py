import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_database
from .monitor import monitor_instance as monitor
from .api import endpoints, auth, agent
from .config import settings

# Configure logging with timestamps
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global task to hold the monitoring task
monitoring_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    global monitoring_task
    
    # Startup
    logging.info("Initializing database...")
    await init_database()
    logging.info("Starting site monitoring...")
    await monitor.start()
    logging.info("Application startup complete")
    
    yield
        
    # Shutdown
    logging.info("Shutting down application...")
    await monitor.stop()
    logging.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="SiteUp Monitor",
    description="Simple website uptime monitoring service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(endpoints.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(agent.router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "SiteUp Monitor",
        "version": "1.0.0",
        "description": "Website uptime monitoring service"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    # Initialize the database
    await init_database()
    # Start the background monitoring task
    asyncio.create_task(monitor.start())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 