"""
Integration tests for webhook functionality.

Tests webhook registration, validation, delivery, and retry logic.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import httpx

from api.services.webhook_manager import WebhookManager, WebhookStatus
from api.database.models import WebhookDelivery, Task as TaskModel
from api.database.connection import get_db


@pytest.fixture
def webhook_manager():
    """Create webhook manager instance."""
    return WebhookManager()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = Mock()
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


class TestWebhookValidation:
    """Test webhook URL validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_https_url(self, webhook_manager):
        """Test validation of valid HTTPS URL."""
        url = "https://example.com/webhook"
        result = await webhook_manager.validate_webhook_url(url)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_valid_http_url(self, webhook_manager):
        """Test validation of valid HTTP URL."""
        url = "http://example.com/webhook"
        result = await webhook_manager.validate_webhook_url(url)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_empty_url(self, webhook_manager):
        """Test validation rejects empty URL."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await webhook_manager.validate_webhook_url("")

    @pytest.mark.asyncio
    async def test_validate_invalid_protocol(self, webhook_manager):
        """Test validation rejects invalid protocol."""
        with pytest.raises(ValueError, match="must start with http"):
            await webhook_manager.validate_webhook_url("ftp://example.com/webhook")

    @pytest.mark.asyncio
    async def test_validate_url_too_long(self, webhook_manager):
        """Test validation rejects URLs exceeding max length."""
        long_url = "https://example.com/" + "x" * 500
        with pytest.raises(ValueError, match="exceeds maximum length"):
            await webhook_manager.validate_webhook_url(long_url)


class TestWebhookDelivery:
    """Test webhook delivery functionality."""

    @pytest.mark.asyncio
    async def test_successful_delivery(self, webhook_manager, mock_db):
        """Test successful webhook delivery."""
        # Create mock delivery record
        delivery = WebhookDelivery(
            delivery_id="test-delivery-1",
            task_id="test-task-1",
            webhook_url="https://example.com/webhook",
            payload={"test": "data"},
            status=WebhookStatus.PENDING.value,
            attempts=0,
        )

        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = delivery
        mock_db.query.return_value = mock_query

        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        with patch.object(webhook_manager.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await webhook_manager.deliver_webhook(mock_db, "test-delivery-1")

            assert result is True
            assert delivery.status == WebhookStatus.DELIVERED.value
            assert delivery.attempts == 1
            assert delivery.response_status == 200

    @pytest.mark.asyncio
    async def test_failed_delivery_schedules_retry(self, webhook_manager, mock_db):
        """Test failed delivery schedules retry with backoff."""
        # Create mock delivery record
        delivery = WebhookDelivery(
            delivery_id="test-delivery-2",
            task_id="test-task-2",
            webhook_url="https://example.com/webhook",
            payload={"test": "data"},
            status=WebhookStatus.PENDING.value,
            attempts=0,
        )

        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = delivery
        mock_db.query.return_value = mock_query

        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(webhook_manager.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await webhook_manager.deliver_webhook(mock_db, "test-delivery-2")

            assert result is False
            assert delivery.status == WebhookStatus.RETRYING.value
            assert delivery.attempts == 1
            assert delivery.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_max_retries_marks_as_failed(self, webhook_manager, mock_db):
        """Test that max retries marks delivery as permanently failed."""
        # Create mock delivery record at max retries
        delivery = WebhookDelivery(
            delivery_id="test-delivery-3",
            task_id="test-task-3",
            webhook_url="https://example.com/webhook",
            payload={"test": "data"},
            status=WebhookStatus.RETRYING.value,
            attempts=WebhookManager.MAX_RETRIES - 1,
        )

        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = delivery
        mock_db.query.return_value = mock_query

        # Mock timeout error
        with patch.object(webhook_manager.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            result = await webhook_manager.deliver_webhook(mock_db, "test-delivery-3")

            assert result is False
            assert delivery.status == WebhookStatus.FAILED.value
            assert delivery.attempts == WebhookManager.MAX_RETRIES
            assert delivery.next_retry_at is None


class TestExponentialBackoff:
    """Test exponential backoff calculation."""

    @pytest.mark.asyncio
    async def test_backoff_increases_exponentially(self, webhook_manager, mock_db):
        """Test that retry delay increases exponentially."""
        delivery = WebhookDelivery(
            delivery_id="test-delivery-4",
            task_id="test-task-4",
            webhook_url="https://example.com/webhook",
            payload={"test": "data"},
            status=WebhookStatus.PENDING.value,
            attempts=0,
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = delivery
        mock_db.query.return_value = mock_query

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        retry_times = []

        with patch.object(webhook_manager.http_client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            # Simulate multiple failed attempts
            for i in range(3):
                await webhook_manager.deliver_webhook(mock_db, "test-delivery-4")
                if delivery.next_retry_at:
                    retry_times.append(delivery.next_retry_at)

        # Verify retry times increase
        assert len(retry_times) == 3
        # Each retry should be scheduled further in the future
        for i in range(1, len(retry_times)):
            assert retry_times[i] > retry_times[i - 1]


class TestWebhookIntegration:
    """Integration tests for complete webhook flow."""

    @pytest.mark.asyncio
    async def test_create_and_deliver_webhook(self, webhook_manager, mock_db):
        """Test creating and delivering a webhook."""
        task_id = "test-task-5"
        webhook_url = "https://example.com/webhook"
        payload = {"task_id": task_id, "status": "completed"}

        # Mock delivery creation
        mock_delivery = WebhookDelivery(
            delivery_id="test-delivery-5",
            task_id=task_id,
            webhook_url=webhook_url,
            payload=payload,
            status=WebhookStatus.PENDING.value,
            attempts=0,
        )

        with patch.object(mock_db, "add") as mock_add:
            with patch.object(mock_db, "commit"):
                with patch.object(mock_db, "refresh") as mock_refresh:
                    mock_refresh.side_effect = lambda obj: setattr(
                        obj, "delivery_id", "test-delivery-5"
                    )

                    delivery_id = await webhook_manager.create_webhook_delivery(
                        db=mock_db, task_id=task_id, webhook_url=webhook_url, payload=payload
                    )

                    assert delivery_id == "test-delivery-5"
                    mock_add.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
