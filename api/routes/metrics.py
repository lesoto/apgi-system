"""
Metrics Routes

Endpoints for exposing Prometheus metrics.
"""

from fastapi import APIRouter, Depends, Response

from api.middleware.metrics import get_metrics_response
from api.services.authorization import require_permission, Permission

router = APIRouter(prefix="/v1", tags=["Metrics"])


@router.get("/metrics", dependencies=[Depends(require_permission(Permission.SYSTEM_ADMIN))])
async def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.

    Returns:
        Prometheus metrics
    """
    return get_metrics_response()
