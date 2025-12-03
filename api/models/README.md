# API Data Models

This directory contains Pydantic models for request/response validation and serialization.

## Overview

The models are organized into several categories:

### Session Models
- `SessionCreateRequest`: Request to create a new simulation session
- `SessionCreateResponse`: Response with new session details
- `SessionResponse`: Detailed session information
- `SessionActionResponse`: Response for session actions (start, pause, stop, reset)

### System State Models
Complete system state representation with nested models:
- `SystemStateResponse`: Top-level state container
- `IgnitionState`: Ignition subsystem state
- `WorkspaceState`: Global workspace state
- `BodyState`: Interoceptive body state
- `AllostaticState`: Allostatic regulation state
- `PrecisionState`: Precision weighting state
- `MetabolicState`: Metabolic reserves state
- `SelfModelState`: Self-model state (minimal and narrative)

### Task Models
- `TaskDefinition`: Definition of experimental task
- `TaskExecuteRequest`: Request to execute a task
- `TaskResult`: Results from completed task
- `TaskSubmitResponse`: Response when task is submitted
- `TaskListResponse`: List of available task types

### Error Models
- `ErrorResponse`: Standard error response format
- `ErrorDetail`: Detailed error information

### Data Export Models
- `IgnitionEvent`: Single ignition event
- `IgnitionHistoryResponse`: Ignition event history with pagination
- `SummaryStatistics`: Summary statistics for a session
- `PaginationInfo`: Pagination information

### Authentication Models
- `LoginRequest`: Login credentials
- `TokenResponse`: JWT token response
- `TokenRefreshRequest`: Token refresh request

### Health and Version Models
- `HealthCheckResponse`: Health check response
- `VersionResponse`: API version information

## Usage

```python
from api.models import SessionCreateRequest, SystemStateResponse

# Create a request
request = SessionCreateRequest(
    config_path="config/default.yaml",
    description="My experiment"
)

# Validate and serialize
json_data = request.model_dump_json()

# Parse response
state = SystemStateResponse.model_validate_json(response_json)
```

## Validation

All models use Pydantic v2 for automatic validation:
- Type checking
- Required field validation
- Custom validators
- JSON schema generation

## OpenAPI Integration

Models automatically generate OpenAPI schemas for FastAPI documentation:
- Request/response examples
- Field descriptions
- Validation constraints
- Nested object schemas

## Testing

See `tests/test_api_models.py` for comprehensive model tests.
