"""Audit event models and enums."""

from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuditEventType(Enum):
    """Types of auditable events."""

    # Authentication events
    LOGIN = auto()
    LOGOUT = auto()
    LOGIN_FAILED = auto()
    PASSWORD_CHANGE = auto()
    PASSWORD_RESET = auto()
    MFA_ENABLED = auto()
    MFA_DISABLED = auto()

    # Authorization events
    ROLE_ASSIGNMENT = auto()
    ROLE_REMOVAL = auto()
    PERMISSION_GRANTED = auto()
    PERMISSION_REVOKED = auto()
    ACCESS_DENIED = auto()

    # Data access events
    DATA_READ = auto()
    DATA_WRITE = auto()
    DATA_DELETE = auto()
    DATA_EXPORT = auto()
    DATA_IMPORT = auto()
    DATA_QUERY = auto()

    # Configuration events
    CONFIG_CHANGE = auto()
    CONFIG_READ = auto()
    POLICY_CHANGE = auto()
    POLICY_READ = auto()

    # System events
    SYSTEM_START = auto()
    SYSTEM_STOP = auto()
    SYSTEM_ERROR = auto()
    SYSTEM_WARNING = auto()

    # User events
    USER_CREATED = auto()
    USER_UPDATED = auto()
    USER_DELETED = auto()
    USER_ACTIVATED = auto()
    USER_DEACTIVATED = auto()

    # Session events
    SESSION_CREATED = auto()
    SESSION_DESTROYED = auto()
    SESSION_EXPIRED = auto()

    # Security events
    SECURITY_INCIDENT = auto()
    VULNERABILITY_DETECTED = auto()
    THREAT_DETECTED = auto()
    ANOMALY_DETECTED = auto()

    # Compliance events
    GDPR_ACCESS_REQUEST = auto()
    GDPR_ERASURE_REQUEST = auto()
    GDPR_RECTIFICATION_REQUEST = auto()
    HIPAA_DISCLOSURE = auto()
    HIPAA_ACCESS = auto()


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    INFO = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class AuditEvent(BaseModel):
    """Immutable audit event record.

    Attributes:
        event_id: Unique identifier for the event
        event_type: Type of event that occurred
        severity: Severity level of the event
        timestamp: When the event occurred
        user_id: ID of user who performed the action
        session_id: Session identifier
        ip_address: IP address of the requester
        user_agent: User agent string
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        action: Action performed
        outcome: Success or failure
        details: Additional event details
        metadata: System metadata
        correlation_id: Correlation ID for distributed tracing
    """

    event_id: str = Field(..., description="Unique event identifier")
    event_type: AuditEventType = Field(..., description="Type of event")
    severity: AuditSeverity = Field(default=AuditSeverity.INFO, description="Event severity")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User who performed action")
    session_id: Optional[str] = Field(None, description="Session identifier")
    ip_address: Optional[str] = Field(None, description="Request IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    resource_type: Optional[str] = Field(None, description="Resource type affected")
    resource_id: Optional[str] = Field(None, description="Resource ID affected")
    action: str = Field(..., description="Action performed")
    outcome: str = Field(..., description="Success or failure")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="System metadata")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")

    class Config:
        frozen = True  # Immutable after creation
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            AuditEventType: lambda v: v.name,
            AuditSeverity: lambda v: v.name,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage.

        Returns:
            Dictionary representation of event
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.name,
            "severity": self.severity.name,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "details": self.details,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create AuditEvent from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            AuditEvent instance
        """
        if isinstance(data.get("event_type"), str):
            data["event_type"] = AuditEventType[data["event_type"]]
        if isinstance(data.get("severity"), str):
            data["severity"] = AuditSeverity[data["severity"]]
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        return cls(**data)


class AuditQuery(BaseModel):
    """Query parameters for audit log searches."""

    event_type: Optional[AuditEventType] = None
    severity: Optional[AuditSeverity] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    ip_address: Optional[str] = None
    outcome: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    def to_filter_dict(self) -> Dict[str, Any]:
        """Convert to filter dictionary for storage queries.

        Returns:
            Dictionary of filter criteria
        """
        filters = {}
        if self.event_type:
            filters["event_type"] = self.event_type.name
        if self.severity:
            filters["severity"] = self.severity.name
        if self.user_id:
            filters["user_id"] = self.user_id
        if self.resource_type:
            filters["resource_type"] = self.resource_type
        if self.resource_id:
            filters["resource_id"] = self.resource_id
        if self.ip_address:
            filters["ip_address"] = self.ip_address
        if self.outcome:
            filters["outcome"] = self.outcome
        if self.start_time:
            filters["timestamp__gte"] = self.start_time.isoformat()
        if self.end_time:
            filters["timestamp__lte"] = self.end_time.isoformat()

        return filters
