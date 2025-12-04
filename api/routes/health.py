"""
Health Check Routes

Endpoints for API health monitoring.
"""

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from api.services.health_check import HealthCheckService


router = APIRouter(prefix="/v1", tags=["Health"])

# Global health check service instance
health_service: HealthCheckService = None


def init_health_routes(redis_client):
    """
    Initialize health routes with Redis client.
    
    Args:
        redis_client: Redis client instance
    """
    global health_service
    health_service = HealthCheckService(redis_client=redis_client)


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Checks the health of all API dependencies:
    - Database connectivity
    - Redis connectivity
    - Celery worker status
    
    Returns:
        JSON response with overall status and individual component checks
        
    Response Codes:
        200: All components healthy
        503: One or more components unhealthy
    """
    if not health_service:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Health service not initialized"
            }
        )
    
    # Perform health check
    health_status = await health_service.perform_health_check()
    
    # Return 503 if any component is unhealthy
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )
