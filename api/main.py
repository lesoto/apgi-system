"""
APGI REST API Main Application

FastAPI application providing RESTful access to the APGI System.
"""

import sys
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Check dependencies before starting
try:
    from utils.dependency_checker import check_dependencies_on_startup

    if not check_dependencies_on_startup():
        print("Dependency check failed. Exiting...")
        sys.exit(1)
except ImportError:
    print("Warning: Dependency checker not available. Continuing anyway...")
except Exception as e:
    print(f"Warning: Error during dependency check: {e}. Continuing anyway...")

from api.config import settings
from api.database.connection import close_db, init_db
from api.exception_handlers import register_exception_handlers
from api.middleware.alerting import configure_alerting
from api.middleware.authentication import AuthenticationMiddleware
from api.middleware.csrf import CSRFMiddleware
from api.middleware.deprecation import DeprecationMiddleware
from api.middleware.request_size_limit import RequestSizeLimitMiddleware
from api.middleware.logging import (
    RequestLoggingMiddleware,
    StructuredLogger,
    configure_structured_logging,
)
from api.middleware.metrics import PrometheusMetricsMiddleware
from api.middleware.rate_limiting import RateLimitingMiddleware
from api.middleware.schema_validation import ResponseSchemaValidationMiddleware
from api.routes import auth, export, health, metrics, sessions, state, tasks, version

# Configure structured logging
configure_structured_logging(settings.log_level)
logger = StructuredLogger(__name__)


# Global Redis client
redis_client: Optional[redis.Redis] = None

# Global rate limiting middleware reference
rate_limiting_middleware: Optional[RateLimitingMiddleware] = None


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
        openapi_url="/openapi.json",
    )

    # Add request size limiting middleware (first, to catch large requests early)
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size_mb=getattr(settings, "max_request_size_mb", 10),
        enabled=getattr(settings, "request_size_limit_enabled", True),
    )

    # Add metrics middleware (first, to track all requests)
    app.add_middleware(PrometheusMetricsMiddleware)

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Add authentication middleware (extracts and verifies JWT tokens)
    app.add_middleware(AuthenticationMiddleware)

    # Add response schema validation middleware
    app.add_middleware(
        ResponseSchemaValidationMiddleware,
        enabled=settings.schema_validation_enabled,
        fail_on_error=settings.schema_validation_fail_on_error,
    )

    # Add CSRF protection middleware
    app.add_middleware(
        CSRFMiddleware,
        enabled=(
            settings.csrf_protection_enabled
            if hasattr(settings, "csrf_protection_enabled")
            else True
        ),
        cookie_name="csrf_token",
        header_name="X-CSRF-Token",
        token_expiry_minutes=60,
    )

    # Add deprecation middleware
    app.add_middleware(DeprecationMiddleware, deprecated_endpoints={})

    # Add rate limiting middleware (will be enabled if Redis is available)
    global rate_limiting_middleware
    rate_limiting_middleware = RateLimitingMiddleware(
        app,
        redis_client=None,  # Will be set in startup
        enabled=settings.rate_limit_enabled,
    )
    app.add_middleware(
        rate_limiting_middleware.__class__, redis_client=None, enabled=settings.rate_limit_enabled
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
        global redis_client  # type: ignore # noqa: F824

        # Configure alerting system
        configure_alerting(
            webhook_urls=settings.alert_webhook_urls,
            enable_log_channel=settings.alert_enable_log_channel,
            error_rate_threshold=settings.alert_error_rate_threshold,
            error_rate_window_minutes=settings.alert_error_rate_window_minutes,
            alert_cooldown_minutes=settings.alert_cooldown_minutes,
        )
        logger.info("Alerting system configured", component="alerting")

        # Initialize database
        try:
            init_db()
            logger.info("Database initialized", component="database")
        except Exception as e:
            logger.error("Failed to initialize database", component="database", error=str(e))
            raise

        # Initialize Redis client
        try:
            redis_client = redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            await redis_client.ping()
            logger.info("Redis client initialized", component="redis", url=settings.redis_url)

            # Update rate limiting middleware with Redis client
            if rate_limiting_middleware:
                rate_limiting_middleware.set_redis_client(redis_client)
                logger.info(
                    "Rate limiting middleware updated with Redis client", component="middleware"
                )

        except Exception as e:
            logger.error("Failed to initialize Redis", component="redis", error=str(e))
            raise

        # Initialize session routes with Redis client
        sessions.init_session_routes(redis_client)
        logger.info("Session routes initialized", component="routes")

        # Initialize task routes
        tasks.init_task_routes()
        logger.info("Task routes initialized", component="routes")

        # Initialize export routes with session manager
        session_mgr = sessions.get_session_manager()
        export.init_export_routes(session_mgr)
        logger.info("Export routes initialized", component="routes")

        # Initialize health routes with Redis client
        health.init_health_routes(redis_client)
        logger.info("Health routes initialized", component="routes")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        global redis_client  # type: ignore # noqa: F824

        # Close Redis connection
        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed", component="redis")

        # Close database connections
        close_db()
        logger.info("Database connections closed", component="database")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check endpoint."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0",
            },
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
            "health": "/health",
        }

    # Include routers
    app.include_router(auth.router)
    app.include_router(sessions.router)
    app.include_router(state.router)
    app.include_router(tasks.router)
    app.include_router(export.router)
    app.include_router(metrics.router)
    app.include_router(health.router)
    app.include_router(version.router)

    logger.info("APGI API application created successfully", version="1.0.0")
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
