"""
GDPR Right to Rectification (Article 16)

Implements the right for data subjects to have inaccurate personal data corrected.
Provides mechanisms for:
- Data correction requests
- Verification of corrected data
- Audit logging of changes
- Notification to downstream systems
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Callable, Set, Any

logger = logging.getLogger(__name__)


class RectificationStatus(str, Enum):
    """Status of a rectification request."""

    PENDING = "pending"
    VERIFIED = "verified"
    APPLIED = "applied"
    REJECTED = "rejected"
    COMPLETED = "completed"


class RectificationType(str, Enum):
    """Type of rectification being requested."""

    CORRECTION = "correction"  # Fix inaccurate data
    COMPLETION = "completion"  # Add missing data
    UPDATE = "update"  # Refresh outdated data
    DELETION = "deletion"  # Remove incorrect data


@dataclass
class FieldChange:
    """Record of a single field change."""

    field_name: str
    old_value: Any
    new_value: Any
    change_reason: str
    verified: bool = False
    verification_source: Optional[str] = None


@dataclass
class RectificationRequest:
    """A request for data rectification under GDPR Article 16."""

    request_id: str
    data_subject_id: str
    request_type: RectificationType
    requested_at: datetime = field(default_factory=datetime.now)
    status: RectificationStatus = RectificationStatus.PENDING
    field_changes: List[FieldChange] = field(default_factory=list)
    supporting_evidence: Dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    completion_notes: Optional[str] = None
    notified_systems: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "request_id": self.request_id,
            "data_subject_id": self.data_subject_id,
            "request_type": self.request_type.value,
            "requested_at": self.requested_at.isoformat(),
            "status": self.status.value,
            "field_changes": [
                {
                    "field_name": fc.field_name,
                    "old_value": str(fc.old_value) if fc.old_value else None,
                    "new_value": str(fc.new_value) if fc.new_value else None,
                    "change_reason": fc.change_reason,
                    "verified": fc.verified,
                    "verification_source": fc.verification_source,
                }
                for fc in self.field_changes
            ],
            "supporting_evidence": self.supporting_evidence,
            "requested_by": self.requested_by,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "rejection_reason": self.rejection_reason,
            "completion_notes": self.completion_notes,
            "notified_systems": list(self.notified_systems),
        }


class RectificationManager:
    """
    Manager for GDPR Article 16 Right to Rectification.

    Handles:
    - Rectification request submission
    - Verification workflows
    - Data correction application
    - Audit trail maintenance
    - Downstream system notifications
    """

    def __init__(self):
        self._requests: Dict[str, RectificationRequest] = {}
        self._rectification_handlers: Dict[str, Any] = {}
        self._notification_callbacks: List[Callable[[RectificationRequest], None]] = []

    def register_handler(self, data_type: str, handler: Any) -> None:
        """
        Register a handler for applying rectifications to specific data types.

        Args:
            data_type: Type of data this handler manages
            handler: Handler object with apply_rectification method
        """
        self._rectification_handlers[data_type] = handler
        logger.info(f"Registered rectification handler for {data_type}")

    def register_notification_callback(self, callback: Callable[..., Any]) -> None:
        """
        Register a callback for rectification notifications.

        Args:
            callback: Function to call when rectification is applied
        """
        self._notification_callbacks.append(callback)

    def submit_request(
        self,
        data_subject_id: str,
        field_changes: List[FieldChange],
        request_type: RectificationType = RectificationType.CORRECTION,
        supporting_evidence: Optional[Dict[str, Any]] = None,
        requested_by: str = "",
    ) -> RectificationRequest:
        """
        Submit a new rectification request.

        Args:
            data_subject_id: ID of the data subject
            field_changes: List of field changes requested
            request_type: Type of rectification
            supporting_evidence: Evidence supporting the changes
            requested_by: Who submitted the request

        Returns:
            Created RectificationRequest
        """
        request_id = f"RECT-{len(self._requests) + 1:06d}"

        request = RectificationRequest(
            request_id=request_id,
            data_subject_id=data_subject_id,
            request_type=request_type,
            field_changes=field_changes,
            supporting_evidence=supporting_evidence or {},
            requested_by=requested_by,
        )

        self._requests[request_id] = request
        logger.info(f"Rectification request submitted: {request_id}")

        return request

    def verify_request(
        self,
        request_id: str,
        reviewer: str,
        verified_fields: List[str],
        verification_notes: str = "",
    ) -> bool:
        """
        Verify a rectification request.

        Args:
            request_id: Request to verify
            reviewer: Who is verifying
            verified_fields: Which fields have been verified
            verification_notes: Additional notes

        Returns:
            True if verification successful
        """
        request = self._requests.get(request_id)
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False

        if request.status != RectificationStatus.PENDING:
            logger.warning(f"Request {request_id} is not pending (status: {request.status})")
            return False

        # Mark verified fields
        for field_change in request.field_changes:
            if field_change.field_name in verified_fields:
                field_change.verified = True
                field_change.verification_source = reviewer

        request.status = RectificationStatus.VERIFIED
        request.reviewed_by = reviewer
        request.reviewed_at = datetime.now()

        logger.info(f"Request {request_id} verified by {reviewer}")
        return True

    def reject_request(self, request_id: str, reviewer: str, reason: str) -> bool:
        """
        Reject a rectification request.

        Args:
            request_id: Request to reject
            reviewer: Who is rejecting
            reason: Rejection reason

        Returns:
            True if rejection successful
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        request.status = RectificationStatus.REJECTED
        request.reviewed_by = reviewer
        request.reviewed_at = datetime.now()
        request.rejection_reason = reason

        logger.info(f"Request {request_id} rejected by {reviewer}: {reason}")
        return True

    def apply_rectification(
        self,
        request_id: str,
        data_type: str,
        apply_func: Optional[Callable[[Any], None]] = None,
    ) -> bool:
        """
        Apply an approved rectification to data.

        Args:
            request_id: Request to apply
            data_type: Type of data being modified
            apply_func: Optional function to apply changes

        Returns:
            True if application successful
        """
        request = self._requests.get(request_id)
        if not request:
            logger.error(f"Request not found: {request_id}")
            return False

        if request.status != RectificationStatus.VERIFIED:
            logger.error(f"Request {request_id} not verified (status: {request.status})")
            return False

        try:
            # Use registered handler if available
            handler = self._rectification_handlers.get(data_type)
            if handler and hasattr(handler, "apply_rectification"):
                handler.apply_rectification(request)
            elif apply_func:
                apply_func(request)
            else:
                logger.warning(f"No handler for data type {data_type}")

            request.status = RectificationStatus.APPLIED

            # Notify downstream systems
            self._notify_systems(request)

            logger.info(f"Rectification {request_id} applied successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply rectification {request_id}: {e}")
            return False

    def complete_request(self, request_id: str, completion_notes: str = "") -> bool:
        """
        Mark a rectification request as completed.

        Args:
            request_id: Request to complete
            completion_notes: Final notes

        Returns:
            True if completion successful
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.status != RectificationStatus.APPLIED:
            logger.warning(f"Request {request_id} not yet applied")
            return False

        request.status = RectificationStatus.COMPLETED
        request.completion_notes = completion_notes

        logger.info(f"Rectification {request_id} completed")
        return True

    def _notify_systems(self, request: RectificationRequest) -> None:
        """Notify downstream systems of rectification."""
        for callback in self._notification_callbacks:
            try:
                callback(request)
                request.notified_systems.add(callback.__name__)  # type: ignore[attr-defined]
            except Exception as e:
                logger.error(f"Notification failed: {e}")

    def get_request(self, request_id: str) -> Optional[RectificationRequest]:
        """Get a rectification request by ID."""
        return self._requests.get(request_id)

    def get_requests_for_subject(self, data_subject_id: str) -> List[RectificationRequest]:
        """Get all rectification requests for a data subject."""
        return [req for req in self._requests.values() if req.data_subject_id == data_subject_id]

    def get_pending_requests(self) -> List[RectificationRequest]:
        """Get all pending rectification requests."""
        return [req for req in self._requests.values() if req.status == RectificationStatus.PENDING]

    def get_statistics(self) -> Dict[str, int]:
        """Get rectification request statistics."""
        stats = {status.value: 0 for status in RectificationStatus}
        for req in self._requests.values():
            stats[req.status.value] += 1
        return stats


class DataRectificationHandler:
    """
    Base class for data type-specific rectification handlers.

    Implement this class to provide rectification support for specific data types.
    """

    def apply_rectification(self, request: RectificationRequest) -> bool:
        """
        Apply rectification to data.

        Args:
            request: Rectification request to apply

        Returns:
            True if successful
        """
        raise NotImplementedError("Subclasses must implement apply_rectification")

    def validate_change(
        self, field_name: str, old_value: Any, new_value: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a proposed field change.

        Args:
            field_name: Field being changed
            old_value: Current value
            new_value: Proposed new value

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None


# Global rectification manager instance
_rectification_manager: Optional[RectificationManager] = None


def get_rectification_manager() -> RectificationManager:
    """Get or create global rectification manager."""
    global _rectification_manager
    if _rectification_manager is None:
        _rectification_manager = RectificationManager()
    return _rectification_manager
