"""
System Administration Routes

Admin-only endpoints for system monitoring and maintenance.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.services.authorization import Role, require_role

router = APIRouter(prefix="/v1/admin", tags=["Administration"])


class CeleryWorkerResponse(BaseModel):
    """Celery worker status information."""

    hostname: str
    status: str
    active: int
    processed: int
    failed: int


class RedisStatsResponse(BaseModel):
    """Redis cache statistics."""

    connected_clients: int
    total_keys: int
    memory_used: str
    memory_peak: str
    uptime_days: float
    hit_rate: Optional[float]


class CircuitBreakerState(BaseModel):
    """Circuit breaker state information."""

    service: str
    state: str
    failure_count: int
    last_failure_time: Optional[str]
    next_retry_time: Optional[str]


class DatabaseMaintenanceResponse(BaseModel):
    """Database maintenance operation result."""

    operation: str
    status: str
    message: str
    execution_time_ms: float


class RateLimitStats(BaseModel):
    """Rate limiting statistics for a user."""

    identifier: str
    requests_this_minute: int
    requests_this_hour: int
    blocked_until: Optional[str]


@router.get(
    "/celery/workers",
    response_model=List[CeleryWorkerResponse],
    summary="List Celery workers",
    description="Retrieve status of active Celery workers",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def list_celery_workers() -> List[CeleryWorkerResponse]:
    """
    List active Celery workers.

    Returns information about Celery worker processes and their current status.

    Returns:
        List of Celery worker status information
    """
    try:
        from celery.app.control import Control

        # Create Celery app instance
        from api.celery_app import celery_app

        control = Control(celery_app)

        # Get active workers
        active_workers = control.inspect().active()
        stats = control.inspect().stats()

        workers = []
        if active_workers:
            for hostname, tasks in active_workers.items():
                worker_stats = stats.get(hostname, {}) if stats else {}
                workers.append(
                    CeleryWorkerResponse(
                        hostname=hostname,
                        status="active",
                        active=len(tasks),
                        processed=worker_stats.get("total", {})
                        .get("tasks", {})
                        .get("succeeded", 0),
                        failed=worker_stats.get("total", {}).get("tasks", {}).get("failed", 0),
                    )
                )

        return workers

    except Exception:
        # Return empty list if Celery is not available
        return []


@router.get(
    "/redis/stats",
    response_model=RedisStatsResponse,
    summary="Get Redis statistics",
    description="Retrieve Redis cache statistics and memory usage",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def get_redis_stats() -> RedisStatsResponse:
    """
    Get Redis cache statistics.

    Returns information about Redis memory usage, connections, and performance.

    Returns:
        Redis statistics information

    Raises:
        HTTPException: If Redis is not available
    """
    try:
        import redis.asyncio as redis

        from api.config import settings

        redis_client = redis.Redis.from_url(settings.redis_url)
        info = await redis_client.info()

        # Calculate hit rate if available
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        hit_rate = (hits / (hits + misses)) * 100 if (hits + misses) > 0 else None

        return RedisStatsResponse(
            connected_clients=info.get("connected_clients", 0),
            total_keys=sum(
                db_info.get("keys", 0)
                for db_info in info.values()
                if isinstance(db_info, dict) and "keys" in db_info
            ),
            memory_used=f"{info.get('used_memory_human', '0B')}",
            memory_peak=f"{info.get('used_memory_peak_human', '0B')}",
            uptime_days=info.get("uptime_in_days", 0),
            hit_rate=hit_rate,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis service unavailable"
        )


@router.delete(
    "/redis/cache",
    status_code=status.HTTP_200_OK,
    summary="Clear Redis cache",
    description="Clear all cached data in Redis (use with caution)",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def clear_redis_cache() -> Dict[str, str]:
    """
    Clear Redis cache.

    Removes all cached data from Redis. This operation cannot be undone.

    Returns:
        Confirmation message

    Raises:
        HTTPException: If Redis is not available
    """
    try:
        import redis.asyncio as redis

        from api.config import settings

        redis_client = redis.Redis.from_url(settings.redis_url)
        await redis_client.flushall()

        return {"message": "Redis cache cleared successfully"}

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis service unavailable"
        )


@router.get(
    "/circuit-breakers",
    response_model=List[CircuitBreakerState],
    summary="Get circuit breaker states",
    description="Retrieve current state of circuit breakers for external services",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def get_circuit_breaker_states() -> List[CircuitBreakerState]:
    """
    Get circuit breaker states.

    Returns current state information for circuit breakers protecting external service calls.

    Returns:
        List of circuit breaker state information
    """
    # Retrieve metrics from the global circuit breaker registry
    from datetime import datetime

    from utils.circuit_breaker_utils import circuit_breaker_registry

    metrics = circuit_breaker_registry.get_metrics()

    return [
        CircuitBreakerState(
            service=name,
            state=m["state"],
            failure_count=m["failed_requests"],
            last_failure_time=(
                datetime.fromtimestamp(m["last_failure_time"]).isoformat()
                if m["last_failure_time"]
                else None
            ),
            next_retry_time=(
                datetime.fromtimestamp(m["last_failure_time"] + m["recovery_timeout"]).isoformat()
                if m["state"] == "open" and m["last_failure_time"]
                else None
            ),
        )
        for name, m in metrics.items()
    ]


@router.post(
    "/database/maintenance",
    response_model=DatabaseMaintenanceResponse,
    summary="Run database maintenance",
    description="Execute database maintenance operations like vacuum and analyze",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def run_database_maintenance(
    operation: str = "vacuum_analyze",
    db: Session = Depends(get_db),
) -> DatabaseMaintenanceResponse:
    """
    Run database maintenance operations.

    Args:
        operation: Maintenance operation to perform (vacuum_analyze, etc.)
        db: Database session

    Returns:
        Maintenance operation result

    Raises:
        HTTPException: If operation fails
    """
    import time

    start_time = time.time()

    try:
        if operation == "vacuum_analyze":
            # Run VACUUM ANALYZE on all tables
            from sqlalchemy import text

            db.execute(text("VACUUM ANALYZE"))
            db.commit()

            execution_time = (time.time() - start_time) * 1000

            return DatabaseMaintenanceResponse(
                operation="vacuum_analyze",
                status="completed",
                message="VACUUM ANALYZE completed successfully",
                execution_time_ms=round(execution_time, 2),
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported maintenance operation: {operation}",
            )

    except Exception:
        execution_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database maintenance failed",
        )


@router.get(
    "/rate-limits",
    response_model=List[RateLimitStats],
    summary="Get rate limiting statistics",
    description="Retrieve current rate limiting statistics for users and IPs",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def get_rate_limit_stats(
    limit: int = 50,
) -> List[RateLimitStats]:
    """
    Get rate limiting statistics.

    Returns current rate limit counters for users and IP addresses.

    Args:
        limit: Maximum number of results to return

    Returns:
        List of rate limiting statistics
    """
    import redis.asyncio as redis

    from api.config import settings

    redis_client = redis.Redis.from_url(settings.redis_url)
    keys = await redis_client.keys("rate_limit:*")

    stats = []
    for key in keys[:limit]:
        key_str = key if isinstance(key, str) else key.decode("utf-8")
        parts = key_str.split(":")
        if len(parts) >= 3:
            identifier = f"{parts[1]} ({parts[2]})"

            # Get current count from Redis sorted set
            count = await redis_client.zcard(key)

            # Get TTL to estimate blocked_until
            ttl = await redis_client.ttl(key)
            blocked_until = None
            if ttl > 0:
                blocked_until = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat() + "Z"

            stats.append(
                RateLimitStats(
                    identifier=identifier,
                    requests_this_minute=count,
                    requests_this_hour=count if "hour" in parts[2] or "3600" in parts[2] else 0,
                    blocked_until=blocked_until,
                )
            )

    return stats
