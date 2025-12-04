"""
Health Check Service

Service for checking the health of API dependencies.
"""

from typing import Dict, Tuple
from datetime import datetime
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis.asyncio as redis
from celery import Celery

from api.database.connection import get_db_context
from api.celery_app import celery_app


logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Service for performing health checks on API dependencies.
    """
    
    def __init__(self, redis_client: redis.Redis = None, celery_app: Celery = None):
        """
        Initialize health check service.
        
        Args:
            redis_client: Redis client instance
            celery_app: Celery application instance
        """
        self.redis_client = redis_client
        self.celery_app = celery_app or globals()['celery_app']
    
    def check_database(self) -> Tuple[str, str]:
        """
        Check database connectivity.
        
        Returns:
            Tuple of (status, message) where status is "healthy" or "unhealthy"
        """
        try:
            with get_db_context() as db:
                # Execute simple query to verify connection
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
            # Ping Redis to verify connection
            await self.redis_client.ping()
            return "healthy", "Redis connection successful"
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
            # Inspect active workers
            inspect = self.celery_app.control.inspect()
            
            # Get active workers with timeout
            active_workers = inspect.active()
            
            if active_workers is None:
                return "unhealthy", "No Celery workers available"
            
            worker_count = len(active_workers)
            if worker_count == 0:
                return "unhealthy", "No active Celery workers"
            
            return "healthy", f"{worker_count} Celery worker(s) active"
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return "unhealthy", f"Celery check failed: {str(e)}"
    
    async def perform_health_check(self) -> Dict:
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
        all_healthy = all([
            db_status == "healthy",
            redis_status == "healthy",
            celery_status == "healthy"
        ])
        
        overall_status = "healthy" if all_healthy else "unhealthy"
        
        return {
            "status": overall_status,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {
                "database": {
                    "status": db_status,
                    "message": db_message
                },
                "redis": {
                    "status": redis_status,
                    "message": redis_message
                },
                "celery": {
                    "status": celery_status,
                    "message": celery_message
                }
            }
        }
