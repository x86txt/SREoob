import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_database
from .monitor import monitor
from .api.endpoints import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global task to hold the monitoring task
monitoring_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    global monitoring_task
    
    # Startup
    logger.info("Starting siteUp application...")
    await init_database()
    logger.info("Database initialized")
    
    # Start monitoring in background
    async with monitor:
        monitoring_task = asyncio.create_task(monitor.start_monitoring(interval=60))
        logger.info("Background monitoring started")
        
        yield
        
        # Shutdown
        logger.info("Shutting down siteUp application...")
        monitor.stop_monitoring()
        if monitoring_task and not monitoring_task.done():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="SiteUp Monitor",
    description="Simple website uptime monitoring service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 