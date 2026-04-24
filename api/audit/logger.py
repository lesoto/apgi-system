"""Audit logger for comprehensive event logging."""

import uuid
from datetime import datetime, timedelta
import asyncio
from functools import wraps
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager

from .models import AuditEvent, AuditEventType, AuditSeverity, AuditQuery
from .storage import AuditStorage, get_audit_storage
from ..logging_config import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """Comprehensive audit logger for sensitive operations.

    Features:
    - Immutable audit events with tamper-evident storage
    - Structured event types for GDPR, HIPAA, SOC 2 compliance
    - Query capabilities for audit investigations
    - Retention policy enforcement
    - Alerting for critical events
    - Distributed tracing support

    Attributes:
        storage: Audit storage backend
        enabled: Whether audit logging is active
        retention_days: Days to retain audit logs
    """

    DEFAULT_RETENTION_DAYS = 365  # 1 year retention

    def __init__(
        self,
        storage: Optional[AuditStorage] = None,
        enabled: bool = True,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> None:
        """Initialize audit logger.

        Args:
            storage: Audit storage backend
            enabled: Whether audit logging is active
            retention_days: Days to retain audit logs
        """
        self.storage = storage or get_audit_storage()
        self.enabled = enabled
        self.retention_days = retention_days
        self._alert_handlers: List = []

    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        outcome: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of event
            action: Action performed
            outcome: Success or failure
            severity: Event severity
            user_id: User who performed action
            session_id: Session identifier
            ip_address: Request IP address
            user_agent: User agent string
            resource_type: Resource type affected
            resource_id: Resource ID affected
            details: Additional event details
            metadata: System metadata
            correlation_id: Correlation ID for tracing

        Returns:
            Created AuditEvent
        """
        if not self.enabled:
            return None

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=details or {},
            metadata=metadata or {},
            correlation_id=correlation_id,
        )

        try:
            await self.storage.store(event)
            logger.info(f"Audit event logged: {event.event_type.name} - {event.action}")

            # Trigger alerts for critical events
            if severity in (AuditSeverity.HIGH, AuditSeverity.CRITICAL):
                await self._trigger_alerts(event)

            return event
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Re-raise to ensure caller knows logging failed
            raise

    async def query(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit logs.

        Args:
            query: Query parameters

        Returns:
            List of matching audit events
        """
        if not self.enabled:
            return []

        try:
            return await self.storage.query(query)
        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")
            return []

    async def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """Get specific audit event by ID.

        Args:
            event_id: Event identifier

        Returns:
            AuditEvent or None if not found
        """
        if not self.enabled:
            return None

        try:
            return await self.storage.retrieve(event_id)
        except Exception as e:
            logger.error(f"Failed to retrieve audit event {event_id}: {e}")
            return None

    async def get_user_history(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get audit history for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of events

        Returns:
            List of user's audit events
        """
        query = AuditQuery(user_id=user_id, limit=limit)
        return await self.query(query)

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get audit history for a specific resource.

        Args:
            resource_type: Resource type
            resource_id: Resource identifier
            limit: Maximum number of events

        Returns:
            List of resource's audit events
        """
        query = AuditQuery(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )
        return await self.query(query)

    async def enforce_retention(self) -> int:
        """Enforce retention policy by deleting old logs.

        Returns:
            Number of events deleted
        """
        if not self.enabled:
            return 0

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            deleted = await self.storage.delete_before(cutoff_date)
            logger.info(f"Deleted {deleted} audit events older than {self.retention_days} days")
            return deleted
        except Exception as e:
            logger.error(f"Failed to enforce retention policy: {e}")
            return 0

    def add_alert_handler(self, handler: Callable[[AuditEvent], None]) -> None:
        """Add alert handler for critical events.

        Args:
            handler: Callable that takes AuditEvent
        """
        self._alert_handlers.append(handler)

    async def _trigger_alerts(self, event: AuditEvent) -> None:
        """Trigger alert handlers for critical events.

        Args:
            event: Audit event to alert on
        """
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    @contextmanager
    def audit_context(
        self,
        event_type: AuditEventType,
        action: str,
        **kwargs,
    ):
        """Context manager for automatic audit logging.

        Automatically logs success/failure of wrapped operations.

        Args:
            event_type: Type of event
            action: Action being performed
            **kwargs: Additional audit event parameters

        Yields:
            None

        Example:
            with audit_logger.audit_context(
                AuditEventType.DATA_WRITE,
                "update_user_profile",
                user_id="123",
                resource_type="user",
                resource_id="123",
            ):
                # Perform operation
                update_profile(data)
        """
        try:
            yield
            outcome = "success"
        except Exception as e:
            outcome = f"failure: {str(e)}"
            raise
        finally:
            asyncio.create_task(
                self.log(
                    event_type=event_type,
                    action=action,
                    outcome=outcome,
                    **kwargs,
                )
            )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance.

    Returns:
        AuditLogger singleton instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def configure_audit_logger(
    storage: Optional[AuditStorage] = None,
    enabled: bool = True,
    retention_days: int = 365,
) -> AuditLogger:
    """Configure global audit logger with custom settings.

    Args:
        storage: Audit storage backend
        enabled: Whether audit logging is enabled
        retention_days: Days to retain audit logs

    Returns:
        Configured AuditLogger instance
    """
    global _audit_logger
    _audit_logger = AuditLogger(
        storage=storage,
        enabled=enabled,
        retention_days=retention_days,
    )
    return _audit_logger


# Convenience decorators
def audit_event(
    event_type: AuditEventType,
    action: str,
    **audit_kwargs,
):
    """Decorator to automatically audit function calls.

    Args:
        event_type: Type of event
        action: Action description
        **audit_kwargs: Additional audit parameters

    Returns:
        Decorated function with automatic audit logging
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            try:
                result = await func(*args, **kwargs)
                await audit_logger.log(
                    event_type=event_type,
                    action=action,
                    outcome="success",
                    **audit_kwargs,
                )
                return result
            except Exception as e:
                await audit_logger.log(
                    event_type=event_type,
                    action=action,
                    outcome=f"failure: {str(e)}",
                    severity=AuditSeverity.HIGH,
                    **audit_kwargs,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            try:
                result = func(*args, **kwargs)
                asyncio.create_task(
                    audit_logger.log(
                        event_type=event_type,
                        action=action,
                        outcome="success",
                        **audit_kwargs,
                    )
                )
                return result
            except Exception as e:
                asyncio.create_task(
                    audit_logger.log(
                        event_type=event_type,
                        action=action,
                        outcome=f"failure: {str(e)}",
                        severity=AuditSeverity.HIGH,
                        **audit_kwargs,
                    )
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
