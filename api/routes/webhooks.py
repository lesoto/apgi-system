"""
Webhook Management Routes

Endpoints for managing webhook deliveries and retry logic.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.database.models import WebhookDelivery
from api.services.authorization import has_any_role, Role
from api.services.webhook_manager import WebhookManager
from pydantic import BaseModel


router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"])


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery information."""

    delivery_id: str
    task_id: str
    webhook_url: str
    status: str
    attempts: int
    last_attempt_at: Optional[str]
    next_retry_at: Optional[str]
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class WebhookRetryResponse(BaseModel):
    """Response for webhook retry operations."""

    delivery_id: str
    message: str
    status: str


@router.get(
    "",
    response_model=List[WebhookDeliveryResponse],
    summary="List webhook deliveries",
    description="Retrieve list of webhook deliveries with optional filtering",
    dependencies=[Depends(lambda current_user: has_any_role(current_user.roles, [Role.ADMIN]))],
)
async def list_webhook_deliveries(
    status_filter: Optional[str] = Query(None, description="Filter by delivery status"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db),
) -> List[WebhookDeliveryResponse]:
    """
    List webhook deliveries.

    Args:
        status_filter: Optional status filter (pending, success, failed, etc.)
        task_id: Optional task ID filter
        limit: Maximum number of results to return
        db: Database session

    Returns:
        List of webhook delivery information
    """
    query = db.query(WebhookDelivery)

    if status_filter:
        query = query.filter(WebhookDelivery.status == status_filter)

    if task_id:
        query = query.filter(WebhookDelivery.task_id == task_id)

    deliveries = query.order_by(WebhookDelivery.created_at.desc()).limit(limit).all()

    return [
        WebhookDeliveryResponse(
            delivery_id=d.delivery_id,
            task_id=d.task_id,
            webhook_url=d.webhook_url,
            status=d.status,
            attempts=d.attempts,
            last_attempt_at=d.last_attempt_at.isoformat() + "Z" if d.last_attempt_at else None,
            next_retry_at=d.next_retry_at.isoformat() + "Z" if d.next_retry_at else None,
            response_status=d.response_status,
            error_message=d.error_message,
            created_at=d.created_at.isoformat() + "Z",
        )
        for d in deliveries
    ]


@router.get(
    "/{delivery_id}",
    response_model=WebhookDeliveryResponse,
    summary="Get webhook delivery",
    description="Retrieve detailed information about a specific webhook delivery",
    dependencies=[Depends(lambda current_user: has_any_role(current_user.roles, [Role.ADMIN]))],
)
async def get_webhook_delivery(
    delivery_id: str,
    db: Session = Depends(get_db),
) -> WebhookDeliveryResponse:
    """
    Get webhook delivery details.

    Args:
        delivery_id: Webhook delivery identifier
        db: Database session

    Returns:
        Webhook delivery information

    Raises:
        HTTPException: If delivery not found
    """
    delivery = db.query(WebhookDelivery).filter(WebhookDelivery.delivery_id == delivery_id).first()

    if not delivery:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Webhook delivery not found")

    return WebhookDeliveryResponse(
        delivery_id=delivery.delivery_id,
        task_id=delivery.task_id,
        webhook_url=delivery.webhook_url,
        status=delivery.status,
        attempts=delivery.attempts,
        last_attempt_at=delivery.last_attempt_at.isoformat() + "Z"
        if delivery.last_attempt_at
        else None,
        next_retry_at=delivery.next_retry_at.isoformat() + "Z" if delivery.next_retry_at else None,
        response_status=delivery.response_status,
        error_message=delivery.error_message,
        created_at=delivery.created_at.isoformat() + "Z",
    )


@router.post(
    "/{delivery_id}/retry",
    response_model=WebhookRetryResponse,
    summary="Retry webhook delivery",
    description="Manually retry a failed webhook delivery",
    dependencies=[Depends(lambda current_user: has_any_role(current_user.roles, [Role.ADMIN]))],
)
async def retry_webhook_delivery(
    delivery_id: str,
    db: Session = Depends(get_db),
) -> WebhookRetryResponse:
    """
    Manually retry a webhook delivery.

    Args:
        delivery_id: Webhook delivery identifier
        db: Database session

    Returns:
        Retry operation result

    Raises:
        HTTPException: If delivery not found or retry failed
    """
    delivery = db.query(WebhookDelivery).filter(WebhookDelivery.delivery_id == delivery_id).first()

    if not delivery:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Webhook delivery not found")

    try:
        # Create webhook manager and retry
        webhook_manager = WebhookManager()
        success = await webhook_manager.deliver_webhook(db, delivery_id)
        await webhook_manager.close()

        if success:
            return WebhookRetryResponse(
                delivery_id=delivery_id,
                message="Webhook delivery retried successfully",
                status="success",
            )
        else:
            return WebhookRetryResponse(
                delivery_id=delivery_id, message="Webhook delivery retry failed", status="failed"
            )

    except Exception as e:
        return WebhookRetryResponse(
            delivery_id=delivery_id,
            message=f"Webhook delivery retry error: {str(e)}",
            status="error",
        )


@router.delete(
    "/{delivery_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook delivery",
    description="Delete a webhook delivery record",
    dependencies=[Depends(lambda current_user: has_any_role(current_user.roles, [Role.ADMIN]))],
)
async def delete_webhook_delivery(
    delivery_id: str,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a webhook delivery record.

    Args:
        delivery_id: Webhook delivery identifier
        db: Database session

    Raises:
        HTTPException: If delivery not found
    """
    delivery = db.query(WebhookDelivery).filter(WebhookDelivery.delivery_id == delivery_id).first()

    if not delivery:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Webhook delivery not found")

    # Delete the delivery record
    db.delete(delivery)
    db.commit()

    # No response body for 204
