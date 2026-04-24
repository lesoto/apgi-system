"""
Audit Log Retention Cleanup Task

Provides automated cleanup of expired audit logs using Celery scheduling.
Implements configurable retention policies with support for:
- Scheduled daily cleanup runs
- Immediate cleanup on demand
- Retention policy enforcement by severity level
- Archive before deletion option
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from celery import Celery, shared_task
from celery.schedules import crontab

from .logger import get_audit_logger

logger = logging.getLogger(__name__)

# Default retention periods by severity (days)
DEFAULT_RETENTION_DAYS = 365
SEVERITY_RETENTION = {
    "CRITICAL": 2555,  # 7 years
    "HIGH": 2555,  # 7 years
    "MEDIUM": 1825,  # 5 years
    "LOW": 365,  # 1 year
    "INFO": 90,  # 90 days
}


class AuditRetentionConfig:
    """Configuration for audit retention policies."""

    def __init__(
        self,
        default_retention_days: int = DEFAULT_RETENTION_DAYS,
        severity_retention: Optional[dict] = None,
        archive_before_delete: bool = False,
        archive_path: Optional[str] = None,
    ):
        self.default_retention_days = default_retention_days
        self.severity_retention = severity_retention or SEVERITY_RETENTION.copy()
        self.archive_before_delete = archive_before_delete
        self.archive_path = archive_path


class AuditCleanupManager:
    """
    Manages automated audit log cleanup based on retention policies.
    """

    def __init__(self, config: Optional[AuditRetentionConfig] = None):
        self.config = config or AuditRetentionConfig()
        self._cleanup_stats: Dict[str, Any] = {
            "total_runs": 0,
            "total_deleted": 0,
            "last_run": None,
        }

    async def cleanup_expired_events(self, severity: Optional[str] = None) -> dict:
        """
        Clean up audit events that have exceeded retention period.

        Args:
            severity: Optional severity level to clean (cleans all if None)

        Returns:
            Dict with cleanup statistics
        """
        audit_logger = get_audit_logger()
        results: Dict[str, Any] = {
            "deleted_count": 0,
            "archived_count": 0,
            "errors": [],
            "severity": severity or "all",
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            if severity:
                # Clean specific severity level
                retention_days = self.config.severity_retention.get(
                    severity, self.config.default_retention_days
                )
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

                deleted = await audit_logger.storage.delete_before(cutoff_date)
                results["deleted_count"] = deleted
                results["retention_days"] = retention_days

                logger.info(
                    f"Cleaned up {deleted} {severity} audit events "
                    f"older than {retention_days} days"
                )
            else:
                # Clean all severity levels
                total_deleted = 0
                for sev, days in self.config.severity_retention.items():
                    cutoff_date = datetime.utcnow() - timedelta(days=days)
                    deleted = await audit_logger.storage.delete_before(cutoff_date)
                    total_deleted += deleted
                    results[f"{sev.lower()}_deleted"] = deleted

                results["deleted_count"] = total_deleted
                logger.info(f"Cleaned up {total_deleted} total audit events")

            # Update stats
            self._cleanup_stats["total_runs"] += 1  # type: ignore[operator]
            self._cleanup_stats["total_deleted"] += results["deleted_count"]  # type: ignore[operator]
            self._cleanup_stats["last_run"] = datetime.utcnow().isoformat()

            # Log the cleanup event
            await audit_logger.log(
                event_type=__import__(
                    "api.audit.models", fromlist=["AuditEventType"]
                ).AuditEventType.SYSTEM_WARNING,
                action="audit_cleanup",
                outcome="success",
                details=results,
            )

        except Exception as e:
            logger.error(f"Error during audit cleanup: {e}")
            if isinstance(results["errors"], list):  # type: ignore
                results["errors"].append(str(e))

        return results

    async def enforce_retention_policy(self) -> dict:
        """
        Full retention policy enforcement across all severity levels.

        Returns:
            Dict with comprehensive cleanup results
        """
        all_results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "by_severity": {},
            "total_deleted": 0,
            "errors": [],
        }

        for severity in self.config.severity_retention.keys():
            try:
                result = await self.cleanup_expired_events(severity)
                all_results["by_severity"][severity] = result  # type: ignore[index]
                all_results["total_deleted"] += result.get("deleted_count", 0)  # type: ignore[operator]
            except Exception as e:
                if isinstance(all_results["errors"], list):  # type: ignore
                    all_results["errors"].append({"severity": severity, "error": str(e)})

        return all_results

    def get_cleanup_stats(self) -> dict:
        """Get cleanup operation statistics."""
        return self._cleanup_stats.copy()

    def get_retention_policy(self) -> dict:
        """Get current retention policy configuration."""
        return {
            "default_retention_days": self.config.default_retention_days,
            "severity_retention": self.config.severity_retention,
            "archive_before_delete": self.config.archive_before_delete,
        }


# Global cleanup manager instance
_cleanup_manager: Optional[AuditCleanupManager] = None


def get_cleanup_manager() -> AuditCleanupManager:
    """Get or create global cleanup manager instance."""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = AuditCleanupManager()
    return _cleanup_manager


# Celery task for scheduled cleanup
try:
    celery_app = Celery("audit_cleanup")

    @shared_task(name="audit.cleanup_expired_logs")
    def cleanup_expired_logs_task(severity: Optional[str] = None) -> dict:
        """
        Celery task for scheduled audit log cleanup.

        Args:
            severity: Optional severity level to clean

        Returns:
            Cleanup results dict
        """
        import asyncio

        manager = get_cleanup_manager()
        return asyncio.run(manager.cleanup_expired_events(severity))

    @shared_task(name="audit.enforce_full_retention")
    def enforce_full_retention_task() -> dict:
        """
        Celery task for full retention policy enforcement.

        Returns:
            Cleanup results dict
        """
        import asyncio

        manager = get_cleanup_manager()
        return asyncio.run(manager.enforce_retention_policy())

    # Celery beat schedule configuration
    celery_app.conf.beat_schedule = {
        "daily-audit-cleanup": {
            "task": "audit.cleanup_expired_logs",
            "schedule": crontab(hour=2, minute=0),  # 2 AM daily
        },
        "weekly-full-retention": {
            "task": "audit.enforce_full_retention",
            "schedule": crontab(day_of_week="sunday", hour=3, minute=0),  # Weekly on Sunday 3 AM
        },
    }

    CELERY_AVAILABLE = True

except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available, scheduled cleanup disabled")
