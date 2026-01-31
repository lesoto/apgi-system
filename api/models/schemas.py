"""
Pydantic Request/Response Models

Data models for API request validation and response serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Enums
# ============================================================================


class SessionStateEnum(str, Enum):
    """Session lifecycle states."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStatusEnum(str, Enum):
    """Task execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Session Models
# ============================================================================


class SessionCreateRequest(BaseModel):
    """Request to create new simulation session."""

    config_path: Optional[str] = Field(None, description="Path to YAML configuration file")
    custom_config: Optional[Dict[str, Any]] = Field(
        None, description="Custom configuration overrides"
    )
    description: Optional[str] = Field(
        None, description="Human-readable description of the session"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "config_path": "config/default.yaml",
                "description": "Baseline simulation experiment",
            }
        }
    )


class SessionCreateResponse(BaseModel):
    """Response with new session details."""

    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Current session status")
    created_at: datetime = Field(..., description="Session creation timestamp")
    config: Dict[str, Any] = Field(..., description="Session configuration")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "created",
                "created_at": "2025-12-03T10:30:00Z",
                "config": {"timestep_ms": 10.0},
            }
        }
    )


class SessionResponse(BaseModel):
    """Detailed session information."""

    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Current session status")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    config: Dict[str, Any] = Field(..., description="Session configuration")
    description: Optional[str] = Field(None, description="Session description")


class SessionActionResponse(BaseModel):
    """Response for session actions (start, pause, stop, reset)."""

    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="New session status")
    timestamp: datetime = Field(..., description="Action timestamp")


# ============================================================================
# System State Models
# ============================================================================


class IgnitionState(BaseModel):
    """Ignition subsystem state."""

    ignition_occurred: bool = Field(..., description="Whether ignition occurred")
    total_signal: float = Field(..., description="Total ignition signal strength")
    threshold: float = Field(..., description="Current ignition threshold")
    duration_ms: Optional[float] = Field(None, description="Duration of ignition event")


class WorkspaceState(BaseModel):
    """Global workspace state."""

    is_broadcasting: bool = Field(..., description="Whether workspace is broadcasting")
    content: Optional[str] = Field(None, description="Type of content being broadcast")
    broadcast_duration_ms: Optional[float] = Field(None, description="Duration of broadcast")


class BodyState(BaseModel):
    """Interoceptive body state."""

    heart_rate: float = Field(..., description="Heart rate (bpm)")
    cortisol: float = Field(..., description="Cortisol level")
    temperature: float = Field(..., description="Body temperature (Celsius)")


class AllostaticState(BaseModel):
    """Allostatic regulation state."""

    allostatic_load: float = Field(..., description="Current allostatic load")


class PrecisionState(BaseModel):
    """Precision weighting state."""

    exteroceptive: float = Field(..., description="Exteroceptive precision weight")
    interoceptive: float = Field(..., description="Interoceptive precision weight")


class MetabolicState(BaseModel):
    """Metabolic reserves state."""

    reserves: float = Field(..., description="Current metabolic reserves")
    reserve_fraction: float = Field(..., description="Fraction of maximum reserves")


class MinimalSelfState(BaseModel):
    """Minimal self-model state."""

    coherence: float = Field(..., description="Self-model coherence")


class NarrativeSelfState(BaseModel):
    """Narrative self-model state."""

    active: bool = Field(..., description="Whether narrative self is active")


class SelfModelState(BaseModel):
    """Self-model state."""

    minimal: MinimalSelfState
    narrative: NarrativeSelfState


class SystemStateResponse(BaseModel):
    """Complete system state."""

    time_ms: float = Field(..., description="Simulation time in milliseconds")
    ignition: IgnitionState
    workspace: WorkspaceState
    body: BodyState
    allostasis: AllostaticState
    precision: PrecisionState
    metabolism: MetabolicState
    self_model: SelfModelState

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time_ms": 5000.0,
                "ignition": {
                    "ignition_occurred": True,
                    "total_signal": 2.5,
                    "threshold": 2.0,
                    "duration_ms": 350.0,
                },
                "workspace": {
                    "is_broadcasting": True,
                    "content": "sensory",
                    "broadcast_duration_ms": 350.0,
                },
                "body": {"heart_rate": 75.0, "cortisol": 0.15, "temperature": 37.0},
                "allostasis": {"allostatic_load": 0.3},
                "precision": {"exteroceptive": 1.2, "interoceptive": 0.8},
                "metabolism": {"reserves": 850.0, "reserve_fraction": 0.85},
                "self_model": {"minimal": {"coherence": 0.75}, "narrative": {"active": True}},
            }
        }
    )


class PredictionErrorsResponse(BaseModel):
    """Prediction errors from hierarchical predictive processing."""

    session_id: str = Field(..., description="Session identifier")
    time_ms: float = Field(..., description="Simulation time in milliseconds")
    prediction_errors: Dict[str, Any] = Field(..., description="Hierarchical prediction errors")
    exteroceptive_stats: Dict[str, Any] = Field(..., description="Exteroceptive statistics")
    interoceptive_stats: Dict[str, Any] = Field(..., description="Interoceptive statistics")


class SomaticMarkersResponse(BaseModel):
    """Somatic markers (context-action-outcome associations)."""

    session_id: str = Field(..., description="Session identifier")
    time_ms: float = Field(..., description="Simulation time in milliseconds")
    num_markers: int = Field(..., description="Number of somatic markers")
    total_retrievals: int = Field(..., description="Total retrieval attempts")
    successful_retrievals: int = Field(..., description="Successful retrievals")
    retrieval_rate: float = Field(..., description="Retrieval success rate")
    markers: List[Dict[str, Any]] = Field(..., description="Somatic marker data")


# ============================================================================
# Task Models
# ============================================================================


class TaskDefinition(BaseModel):
    """Definition of experimental task."""

    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of experimental task")
    session_id: str = Field(..., description="Associated session ID")
    parameters: Dict[str, Any] = Field(..., description="Task parameters")
    created_at: datetime = Field(..., description="Task creation timestamp")


class TaskExecuteRequest(BaseModel):
    """Request to execute experimental task."""

    task_type: str = Field(..., description="Type of task to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task-specific parameters")
    webhook_url: Optional[str] = Field(
        None, description="URL for webhook notification on completion"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"task_type": "iowa_gambling", "parameters": {"num_trials": 100}}
        }
    )


class TaskResult(BaseModel):
    """Results from completed task."""

    task_id: str = Field(..., description="Task identifier")
    status: TaskStatusEnum = Field(..., description="Task execution status")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Task results")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_7f8d9e0a1b2c",
                "status": "completed",
                "progress": 100,
                "started_at": "2025-12-03T10:35:01Z",
                "completed_at": "2025-12-03T10:36:30Z",
                "result_data": {"trials": [], "summary": {"advantageous_deck_preference": 0.65}},
            }
        }
    )


class TaskSubmitRequest(BaseModel):
    """Request to submit a task for execution."""

    task_type: str = Field(..., description="Type of experimental task")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Task-specific parameters"
    )
    webhook_url: Optional[str] = Field(
        None, description="URL for webhook notification on task completion"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_type": "iowa_gambling",
                "parameters": {"num_trials": 100},
                "webhook_url": "https://example.com/webhook",
            }
        }
    )


class TaskSubmitResponse(BaseModel):
    """Response when task is submitted."""

    task_id: str = Field(..., description="Task identifier")
    session_id: str = Field(..., description="Session identifier")
    task_type: str = Field(..., description="Task type")
    status: str = Field(..., description="Initial task status")
    status_url: str = Field(..., description="URL to check task status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_7f8d9e0a1b2c",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_type": "iowa_gambling",
                "status": "pending",
                "status_url": "/v1/tasks/task_7f8d9e0a1b2c",
            }
        }
    )


class TaskStatusResponse(BaseModel):
    """Response with task status and results."""

    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Current task status")
    state: Optional[str] = Field(None, description="Celery task state")
    result: Optional[Dict[str, Any]] = Field(None, description="Task results if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    info: Optional[Dict[str, Any]] = Field(None, description="Progress info if running")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_7f8d9e0a1b2c",
                "status": "completed",
                "state": "SUCCESS",
                "result": {
                    "task_type": "iowa_gambling",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "completed",
                    "results": {"total_trials": 100, "advantageous_ratio": 0.65},
                },
            }
        }
    )


class TaskResultResponse(BaseModel):
    """Detailed task results."""

    task_id: str = Field(..., description="Task identifier")
    task_type: str = Field(..., description="Task type")
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Task status")
    results: Dict[str, Any] = Field(..., description="Task results")


class TaskListResponse(BaseModel):
    """List of available task types."""

    tasks: List[Dict[str, Any]] = Field(..., description="Available task types")


# ============================================================================
# Error Models
# ============================================================================


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: Dict[str, Any] = Field(
        ..., description="Error details including code, message, request_id, timestamp, and details"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": "Session with ID 'abc123' does not exist",
                    "request_id": "req_7f8d9e0a1b2c",
                    "timestamp": "2025-12-03T10:30:00Z",
                    "details": {"session_id": "abc123"},
                }
            }
        }
    )


# ============================================================================
# Data Export Models
# ============================================================================


class PaginationInfo(BaseModel):
    """Pagination information."""

    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_more: bool = Field(..., description="Whether more data is available")


class IgnitionEvent(BaseModel):
    """Single ignition event."""

    time_ms: float = Field(..., description="Event timestamp in milliseconds")
    duration_ms: float = Field(..., description="Event duration")
    trigger_signal: float = Field(..., description="Signal that triggered ignition")
    threshold: float = Field(..., description="Threshold at time of ignition")


class IgnitionHistoryResponse(BaseModel):
    """Ignition event history."""

    events: List[IgnitionEvent] = Field(..., description="List of ignition events")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination info")


class SummaryStatistics(BaseModel):
    """Summary statistics for a session."""

    session_id: str = Field(..., description="Session identifier")
    duration_ms: float = Field(..., description="Total simulation duration")
    num_steps: int = Field(..., description="Number of simulation steps")
    ignition_stats: Dict[str, Any] = Field(..., description="Ignition statistics")
    energy_stats: Dict[str, Any] = Field(..., description="Energy statistics")
    allostasis_stats: Dict[str, Any] = Field(..., description="Allostasis statistics")


# ============================================================================
# Authentication Models
# ============================================================================


class LoginRequest(BaseModel):
    """Login request."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


# ============================================================================
# Health and Version Models
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Check timestamp")
    checks: Optional[Dict[str, str]] = Field(None, description="Individual component checks")


class VersionResponse(BaseModel):
    """API version information."""

    current_version: str = Field(..., description="Current API version")
    supported_versions: List[str] = Field(..., description="List of supported versions")
    deprecated_versions: List[str] = Field(..., description="List of deprecated versions")
    api_spec_url: str = Field(..., description="URL to OpenAPI specification")


# ============================================================================
# User Management Models
# ============================================================================


class UserCreateRequest(BaseModel):
    """Request to create a new user."""

    username: Optional[str] = Field(None, description="Username (auto-generated if not provided)")
    email: Optional[str] = Field(None, description="Email address")
    password: Optional[str] = Field(None, description="Password (auto-generated if not provided)")
    roles: Optional[List[str]] = Field(None, description="List of user roles")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secure_password123",
                "roles": ["user"],
            }
        }
    )


class UserCreateResponse(BaseModel):
    """Response after user creation."""

    user_id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    roles: List[str] = Field(..., description="User roles")
    password: str = Field(..., description="Plain text password (only returned once)")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Status message")


class UserResponse(BaseModel):
    """User information response."""

    user_id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    roles: List[str] = Field(..., description="User roles")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "john_doe",
                "email": "john@example.com",
                "roles": ["user"],
                "is_active": True,
                "created_at": "2025-12-03T10:30:00Z",
                "updated_at": "2025-12-03T10:30:00Z",
                "last_login": "2025-12-03T11:00:00Z",
            }
        }
    )


class UserUpdateRequest(BaseModel):
    """Request to update user information."""

    email: Optional[str] = Field(None, description="New email address")
    roles: Optional[List[str]] = Field(None, description="New roles list (admin only)")
    is_active: Optional[bool] = Field(None, description="Active status (admin only)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newemail@example.com",
                "roles": ["user", "researcher"],
                "is_active": True,
            }
        }
    )


class PasswordResetRequest(BaseModel):
    """Request to reset user password."""

    new_password: Optional[str] = Field(
        None, description="New password (auto-generated if not provided)"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"new_password": "new_secure_password456"}}
    )


class PasswordResetResponse(BaseModel):
    """Response after password reset."""

    user_id: str = Field(..., description="User identifier")
    new_password: str = Field(..., description="New plain text password")
    message: str = Field(..., description="Status message")


class UserStatsResponse(BaseModel):
    """User statistics response."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    role_counts: Dict[str, int] = Field(..., description="Count of users by role")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_users": 10,
                "active_users": 8,
                "inactive_users": 2,
                "role_counts": {"admin": 2, "user": 6, "researcher": 2},
            }
        }
    )
