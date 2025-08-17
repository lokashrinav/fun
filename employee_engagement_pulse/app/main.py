"""
FastAPI main application entry point
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.slack_events import slack_router
from app.models import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app import api

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting Employee Engagement Pulse API")
    
    # Initialize database
    init_db()
    
    # Start scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Employee Engagement Pulse API")
    stop_scheduler()


app = FastAPI(
    title="Employee Engagement Pulse API",
    description="Transform Slack workspace chatter into actionable engagement insights",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(slack_router, prefix="/slack", tags=["slack"])
app.include_router(api.router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Employee Engagement Pulse API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Could add database connectivity check here
        return {
            "status": "healthy",
            "database": "connected",
            "scheduler": "running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard HTML file"""
    # dashboard.html is in the project root directory
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard.html")
    return FileResponse(dashboard_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
