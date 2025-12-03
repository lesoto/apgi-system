"""
Webhook Manager Service

Manages webhook registration, validation, delivery with retry logic and exponential backoff.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import httpx
from sqlalchemy.orm import Session as DBSession

from api.database.models import WebhookDelivery, Task
from api.database.connection import get_db


logger = logging.getLogger(__name__)


class WebhookStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookManager:
    """
    Manages webhook registration, validation, and delivery.
    
    Implements retry logic with exponential backoff for failed deliveries.
    """
    
    # Retry configuration
    MAX_RETRIES = 5
    INITIAL_RETRY_DELAY_SECONDS = 60  # 1 minute
    MAX_RETRY_DELAY_SECONDS = 3600  # 1 hour
    BACKOFF_MULTIPLIER = 2
    
    # HTTP timeout configuration
    REQUEST_TIMEOUT_SECONDS = 30
    
    def __init__(self):
        """Initialize webhook manager."""
        self.http_client = httpx.AsyncClient(
            timeout=self.REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True
        )
        logger.info("WebhookManager initialized")
    
    async def validate_webhook_url(self, url: str) -> bool:
        """
        Validate webhook URL format and accessibility.
        
        Args:
            url: Webhook URL to validate
            
        Returns:
            True if URL is valid and accessible
            
        Raises:
            ValueError: If URL is invalid
        """
        # Basic URL validation
        if not url:
            raise ValueError("Webhook URL cannot be empty")
        
        if not url.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        
        # Check URL length
        if len(url) > 500:
            raise ValueError("Webhook URL exceeds maximum length of 500 characters")
        
        # Optionally perform a HEAD request to verify accessibility
        # (commented out to avoid blocking during validation)
        # try:
        #     response = await self.http_client.head(url, timeout=5.0)
        #     return response.status_code < 500
        # except Exception as e:
        #     logger.warning(f"Webhook URL validation failed for {url}: {e}")
        #     return False
        
        return True
    
    async def create_webhook_delivery(
        self,
        db: DBSession,
        task_id: str,
        webhook_url: str,
        payload: Dict[str, Any]
    ) -> str:
        """
        Create a webhook delivery record.
        
        Args:
            db: Database session
            task_id: Associated task ID
            webhook_url: Target webhook URL
            payload: Webhook payload
            
        Returns:
            Delivery ID
        """
        # Validate URL
        await self.validate_webhook_url(webhook_url)
        
        # Create delivery record
        delivery = WebhookDelivery(
            task_id=task_id,
            webhook_url=webhook_url,
            payload=payload,
            status=WebhookStatus.PENDING.value,
            attempts=0
        )
        
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        
        logger.info(f"Created webhook delivery {delivery.delivery_id} for task {task_id}")
        
        return delivery.delivery_id
    
    async def deliver_webhook(
        self,
        db: DBSession,
        delivery_id: str
    ) -> bool:
        """
        Attempt to deliver a webhook.
        
        Args:
            db: Database session
            delivery_id: Webhook delivery ID
            
        Returns:
            True if delivery succeeded, False otherwise
        """
        # Get delivery record
        delivery = db.query(WebhookDelivery).filter(
            WebhookDelivery.delivery_id == delivery_id
        ).first()
        
        if not delivery:
            logger.error(f"Webhook delivery {delivery_id} not found")
            return False
        
        # Update attempt count and timestamp
        delivery.attempts += 1
        delivery.last_attempt_at = datetime.utcnow()
        delivery.status = WebhookStatus.RETRYING.value if delivery.attempts > 1 else WebhookStatus.PENDING.value
        db.commit()
        
        try:
            # Send POST request to webhook URL
            logger.info(
                f"Attempting webhook delivery {delivery_id} "
                f"(attempt {delivery.attempts}/{self.MAX_RETRIES}) to {delivery.webhook_url}"
            )
            
            response = await self.http_client.post(
                delivery.webhook_url,
                json=delivery.payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "APGI-API-Webhook/1.0",
                    "X-Webhook-Delivery-ID": delivery_id,
                    "X-Webhook-Attempt": str(delivery.attempts)
                }
            )
            
            # Store response
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response body size
            
            # Check if delivery was successful (2xx status code)
            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.DELIVERED.value
                delivery.next_retry_at = None
                db.commit()
                
                logger.info(
                    f"Webhook delivery {delivery_id} succeeded "
                    f"(status: {response.status_code})"
                )
                return True
            else:
                # Non-2xx response - schedule retry
                logger.warning(
                    f"Webhook delivery {delivery_id} failed with status {response.status_code}"
                )
                await self._schedule_retry(db, delivery)
                return False
                
        except httpx.TimeoutException as e:
            logger.warning(f"Webhook delivery {delivery_id} timed out: {e}")
            delivery.error_message = f"Request timeout: {str(e)}"
            await self._schedule_retry(db, delivery)
            return False
            
        except httpx.RequestError as e:
            logger.warning(f"Webhook delivery {delivery_id} failed with request error: {e}")
            delivery.error_message = f"Request error: {str(e)}"
            await self._schedule_retry(db, delivery)
            return False
            
        except Exception as e:
            logger.error(f"Webhook delivery {delivery_id} failed with unexpected error: {e}", exc_info=True)
            delivery.error_message = f"Unexpected error: {str(e)}"
            await self._schedule_retry(db, delivery)
            return False
    
    async def _schedule_retry(self, db: DBSession, delivery: WebhookDelivery):
        """
        Schedule retry for failed webhook delivery with exponential backoff.
        
        Args:
            db: Database session
            delivery: Webhook delivery record
        """
        if delivery.attempts >= self.MAX_RETRIES:
            # Max retries reached - mark as failed
            delivery.status = WebhookStatus.FAILED.value
            delivery.next_retry_at = None
            logger.error(
                f"Webhook delivery {delivery.delivery_id} failed permanently "
                f"after {delivery.attempts} attempts"
            )
        else:
            # Calculate next retry time with exponential backoff
            retry_delay = min(
                self.INITIAL_RETRY_DELAY_SECONDS * (self.BACKOFF_MULTIPLIER ** (delivery.attempts - 1)),
                self.MAX_RETRY_DELAY_SECONDS
            )
            
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            delivery.status = WebhookStatus.RETRYING.value
            
            logger.info(
                f"Webhook delivery {delivery.delivery_id} scheduled for retry "
                f"in {retry_delay} seconds (attempt {delivery.attempts + 1}/{self.MAX_RETRIES})"
            )
        
        db.commit()
    
    async def process_pending_webhooks(self, db: DBSession):
        """
        Process all pending webhook deliveries that are ready for retry.
        
        Args:
            db: Database session
        """
        # Query pending/retrying webhooks that are ready for delivery
        now = datetime.utcnow()
        
        pending_deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.status.in_([WebhookStatus.PENDING.value, WebhookStatus.RETRYING.value]),
            (WebhookDelivery.next_retry_at.is_(None)) | (WebhookDelivery.next_retry_at <= now)
        ).all()
        
        logger.info(f"Processing {len(pending_deliveries)} pending webhook deliveries")
        
        # Process each delivery
        for delivery in pending_deliveries:
            try:
                await self.deliver_webhook(db, delivery.delivery_id)
            except Exception as e:
                logger.error(
                    f"Error processing webhook delivery {delivery.delivery_id}: {e}",
                    exc_info=True
                )
    
    async def get_delivery_status(
        self,
        db: DBSession,
        delivery_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get webhook delivery status.
        
        Args:
            db: Database session
            delivery_id: Webhook delivery ID
            
        Returns:
            Dict with delivery status information, or None if not found
        """
        delivery = db.query(WebhookDelivery).filter(
            WebhookDelivery.delivery_id == delivery_id
        ).first()
        
        if not delivery:
            return None
        
        return {
            "delivery_id": delivery.delivery_id,
            "task_id": delivery.task_id,
            "webhook_url": delivery.webhook_url,
            "status": delivery.status,
            "attempts": delivery.attempts,
            "last_attempt_at": delivery.last_attempt_at.isoformat() if delivery.last_attempt_at else None,
            "next_retry_at": delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
            "response_status": delivery.response_status,
            "error_message": delivery.error_message,
            "created_at": delivery.created_at.isoformat()
        }
    
    async def get_task_deliveries(
        self,
        db: DBSession,
        task_id: str
    ) -> list[Dict[str, Any]]:
        """
        Get all webhook deliveries for a task.
        
        Args:
            db: Database session
            task_id: Task ID
            
        Returns:
            List of delivery status dicts
        """
        deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.task_id == task_id
        ).all()
        
        return [
            {
                "delivery_id": d.delivery_id,
                "webhook_url": d.webhook_url,
                "status": d.status,
                "attempts": d.attempts,
                "last_attempt_at": d.last_attempt_at.isoformat() if d.last_attempt_at else None,
                "response_status": d.response_status,
                "error_message": d.error_message
            }
            for d in deliveries
        ]
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
        logger.info("WebhookManager closed")
