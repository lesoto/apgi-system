"""
Celery tasks for Webhook delivery and Dead Letter Queue management.
"""

import asyncio
import logging

from celery import Task  # type: ignore[import-untyped]
from api.celery_app import celery_app
from api.database.connection import get_db
from typing import Any
from api.services.webhook_manager import WebhookManager
import yaml
from apgi_framework.platform_utils import get_resource_path

logger = logging.getLogger(__name__)


async def process_webhooks_pipeline() -> None:
    db = next(get_db())
    try:
        config_path = get_resource_path("config/default.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        webhook_config = config.get("webhook", {})

        manager = WebhookManager(webhook_config=webhook_config)
        await manager.process_pending_webhooks(db)
        await manager.close()
    finally:
        db.close()


@celery_app.task(name="api.tasks.webhook_tasks.process_webhooks")  # type: ignore[untyped-decorator]
def process_webhooks_task() -> str:
    """Periodic task to process pending webhooks."""
    asyncio.run(process_webhooks_pipeline())
    return "Processed pending webhooks"


@celery_app.task(bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def dlq_failure_handler(self: Task, request: Any, exc: Exception, traceback: Any) -> None:
    """Handle Celery task failures by pushing them to a dead letter queue in Redis."""
    try:
        from api.config import settings
        import redis

        redis_client = redis.Redis.from_url(settings.redis_url)
        dlq_payload = {
            "task_id": request.id,
            "task_args": request.args,
            "task_kwargs": request.kwargs,
            "error": str(exc),
            "traceback": str(traceback),
        }
        import json

        redis_client.lpush("celery_dlq", json.dumps(dlq_payload))
        logger.error(f"Task {request.id} failed. Sent to DLQ.")
    except Exception as e:
        logger.error(f"Failed to push to DLQ: {e}")
