"""
Health Check Routes

Endpoints for API health monitoring.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Any, Optional

from api.services.authorization import (
    get_current_user,
    TokenPayload,
    has_any_role,
    Role,
)
from api.services.health_check import HealthCheckService

router = APIRouter(prefix="/v1", tags=["Health"])

# Global health check service instance
health_service: Optional[HealthCheckService] = None


def init_health_routes(redis_client: Any) -> None:
    """
    Initialize health routes with Redis client.

    Args:
        redis_client: Redis client instance
    """
    global health_service
    health_service = HealthCheckService(redis_client=redis_client)


@router.get("/health")
async def health_check(
    current_user: Optional[TokenPayload] = Depends(get_current_user),
) -> JSONResponse:
    """
    Health check endpoint with varying detail levels.

    Returns minimal status for unauthenticated requests.
    Returns detailed component checks for authenticated admin users.

    Returns:
        JSON response with health status

    Response Codes:
        200: API is healthy
        503: API or components are unhealthy
    """
    if not health_service:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Health service not initialized"},
        )

    # Check if user is authenticated and is admin
    is_admin = current_user and has_any_role(current_user.roles, [Role.ADMIN])

    if is_admin:
        # Admin user - return detailed health check
        health_status = await health_service.perform_health_check()
    else:
        # Unauthenticated or non-admin - return minimal status
        try:
            detailed_status = await health_service.perform_health_check()
            health_status = {"status": detailed_status["status"]}
        except Exception:
            health_status = {"status": "unhealthy"}

    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(status_code=status_code, content=health_status)


@router.get("/health/live")
async def liveness_probe() -> JSONResponse:
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the process is alive and the event loop is responsive.
    This intentionally does NOT check external dependencies — if a dependency
    is down the pod should stay alive (so traffic can drain) rather than be
    killed and restarted repeatedly.

    Returns:
        200: Process is alive
    """
    return JSONResponse(status_code=200, content={"status": "alive"})


@router.get("/health/ready")
async def readiness_probe() -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.

    Returns 200 only when all dependencies (database, Redis) are reachable
    and the service is ready to accept traffic.  Returns 503 otherwise so
    the pod is removed from the load balancer until dependencies recover.

    Returns:
        200: Service is ready to accept traffic
        503: Service is not yet ready
    """
    if not health_service:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "Health service not initialized"},
        )

    try:
        health_status = await health_service.perform_health_check()
        if health_status.get("status") == "healthy":
            return JSONResponse(status_code=200, content={"status": "ready"})
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "details": health_status},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": str(exc)},
        )
