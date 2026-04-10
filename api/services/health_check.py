"""
Health Check Service

Service for checking the health of API dependencies.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as redis
from celery import Celery  # type: ignore
from sqlalchemy import text

from api.celery_app import celery_app as default_celery_app
from api.database.connection import get_db_context

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Service for performing health checks on API dependencies.
    """

    def __init__(
        self, redis_client: Optional[redis.Redis] = None, celery_app: Optional[Celery] = None
    ):
        """
        Initialize health check service.

        Args:
            redis_client: Redis client instance
            celery_app: Celery application instance
        """
        self.redis_client = redis_client
        self.celery_app = celery_app or default_celery_app

    def check_database(self) -> Tuple[str, str]:
        """
        Check database connectivity.

        Returns:
            Tuple of (status, message) where status is "healthy" or "unhealthy"
        """
        try:
            with get_db_context() as db:
                # Execute simple query to verify connection with 5s timeout
                db.execute(text("SET statement_timeout = 5000"))
                result = db.execute(text("SELECT 1"))
                result.fetchone()
            return "healthy", "Database connection successful"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return "unhealthy", f"Database connection failed: {str(e)}"

    async def check_redis(self) -> Tuple[str, str]:
        """
        Check Redis connectivity.

        Returns:
            Tuple of (status, message) where status is "healthy" or "unhealthy"
        """
        if not self.redis_client:
            return "unhealthy", "Redis client not initialized"

        try:
            # Ping Redis to verify connection with 5s timeout
            import asyncio

            await asyncio.wait_for(self.redis_client.ping(), timeout=5.0)  # type: ignore[misc]
            return "healthy", "Redis connection successful"
        except asyncio.TimeoutError:
            logger.error("Redis health check timed out")
            return "unhealthy", "Redis connection timed out"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return "unhealthy", f"Redis connection failed: {str(e)}"

    def check_celery(self) -> Tuple[str, str]:
        """
        Check Celery worker status.

        Returns:
            Tuple of (status, message) where status is "healthy" or "unhealthy"
        """
        try:
            # Check if Celery app is properly configured
            if not self.celery_app:
                return "unhealthy", "Celery application not configured"

            # Check if broker URL is configured
            broker_url = getattr(self.celery_app, "conf", {}).get("broker_url") or getattr(
                self.celery_app, "broker_url", None
            )
            if not broker_url:
                return "unhealthy", "Celery broker URL not configured"

            # Try to ping workers first (more reliable than active())
            inspect = self.celery_app.control.inspect()

            # Use ping instead of active for better error handling
            ping_result = inspect.ping(timeout=5.0)

            if ping_result is None:
                return (
                    "unhealthy",
                    "Celery broker unreachable - check broker connection and configuration",
                )

            # Check if any workers responded to ping
            if not ping_result:
                return "unhealthy", "No Celery workers available - ensure workers are running"

            worker_count = len(ping_result)
            return "healthy", f"{worker_count} Celery worker(s) responding to ping"

        except Exception as e:
            error_msg = str(e).lower()
            if "connection refused" in error_msg or "connection error" in error_msg:
                return (
                    "unhealthy",
                    f"Celery broker connection failed - check broker URL and network: {str(e)}",
                )
            elif "timeout" in error_msg:
                return (
                    "unhealthy",
                    f"Celery broker timeout - broker may be overloaded or unreachable: {str(e)}",
                )
            elif "no workers" in error_msg or "no active workers" in error_msg:
                return "unhealthy", f"No Celery workers running - start worker processes: {str(e)}"
            else:
                return (
                    "unhealthy",
                    f"Celery health check failed - configuration or broker issue: {str(e)}",
                )

    async def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on all dependencies.

        Returns:
            Dict containing overall status and individual component checks
        """
        # Check database
        db_status, db_message = self.check_database()

        # Check Redis
        redis_status, redis_message = await self.check_redis()

        # Check Celery
        celery_status, celery_message = self.check_celery()

        # Determine overall status
        all_healthy = all(
            [db_status == "healthy", redis_status == "healthy", celery_status == "healthy"]
        )

        overall_status = "healthy" if all_healthy else "unhealthy"

        return {
            "status": overall_status,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {
                "database": {"status": db_status, "message": db_message},
                "redis": {"status": redis_status, "message": redis_message},
                "celery": {"status": celery_status, "message": celery_message},
            },
        }
