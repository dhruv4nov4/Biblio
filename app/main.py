"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
from app.utils.logger import get_logger
import uvicorn

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Builder Platform",
    description="Generate complete web projects from natural language",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["builder"])


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("=" * 60)
    logger.info("AI Builder Platform Starting")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.LOG_LEVEL}")
    logger.info(f"Output Directory: {settings.OUTPUT_DIR}")
    logger.info(f"Max Retries: {settings.MAX_RETRY_COUNT}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("AI Builder Platform Shutting Down")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )