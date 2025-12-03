"""
APGI REST API Main Application

FastAPI application providing RESTful access to the APGI System.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import redis.asyncio as redis

from api.config import settings
from api.routes import sessions, state, tasks, export
from api.database.connection import init_db, close_db
from api.exception_handlers import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global Redis client
redis_client: redis.Redis = None


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="APGI System API",
        version="1.0.0",
        description="REST API for Allostatic Precision-Gated Ignition consciousness modeling",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize resources on startup."""
        global redis_client
        
        # Initialize database
        try:
            init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        
        # Initialize Redis client
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
        
        # Initialize session routes with Redis client
        sessions.init_session_routes(redis_client)
        logger.info("Session routes initialized")
        
        # Initialize task routes
        tasks.init_task_routes()
        logger.info("Task routes initialized")
        
        # Initialize export routes with session manager
        session_mgr = sessions.get_session_manager()
        export.init_export_routes(session_mgr)
        logger.info("Export routes initialized")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        global redis_client
        
        # Close Redis connection
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")
        
        # Close database connections
        close_db()
        logger.info("Database connections closed")
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check endpoint."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0"
            }
        )
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """API root endpoint with basic information."""
        return {
            "name": "APGI System API",
            "version": "1.0.0",
            "description": "REST API for consciousness modeling",
            "docs": "/docs",
            "health": "/health"
        }
    
    # Include routers
    app.include_router(sessions.router)
    app.include_router(state.router)
    app.include_router(tasks.router)
    app.include_router(export.router)
    
    logger.info("APGI API application created successfully")
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
