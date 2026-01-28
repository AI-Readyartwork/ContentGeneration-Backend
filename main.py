from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from app.config import settings
from app.api import router
from app.services.scheduler_service import (
    start_scheduler, 
    stop_scheduler, 
    get_scheduler_status,
    run_news_update_now
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Starts the scheduler when app starts, stops it when app shuts down.
    """
    # Startup: Start the scheduler
    print("\n[STARTUP] Starting Newsletter AI Backend...")
    start_scheduler()
    
    yield
    
    # Shutdown: Stop the scheduler
    print("\n[SHUTDOWN] Stopping Newsletter AI Backend...")
    stop_scheduler()


app = FastAPI(
    title="Newsletter AI Backend",
    description="FastAPI backend with LangChain for AI-powered newsletter generation",
    version="1.0.0",
    lifespan=lifespan  # Use lifespan for startup/shutdown events
)

# CORS middleware - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Newsletter AI Backend API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    scheduler_status = get_scheduler_status()
    return {
        "status": "healthy",
        "scheduler": scheduler_status
    }


@app.get("/scheduler/status")
async def scheduler_status():
    """Get the current status of the news update scheduler"""
    return get_scheduler_status()


@app.post("/scheduler/trigger")
async def trigger_news_update():
    """Manually trigger news update (for testing or admin use)"""
    await run_news_update_now()
    return {
        "message": "News update triggered",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
