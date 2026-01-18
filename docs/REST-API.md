# APGI REST API

RESTful API interface for the Allostatic Precision-Gated Ignition (APGI) System.

## Overview

This API provides programmatic access to the APGI consciousness modeling system, enabling researchers and developers to:

- Create and manage simulation sessions
- Control simulation execution (start, pause, stop, reset)
- Access real-time system state and metrics
- Execute experimental tasks (Iowa Gambling, Masking Paradigm, etc.)
- Export and analyze simulation data

## Quick Start

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Configure environment:

```bash
cp .env.example .env
# Edit .env with your settings
```

1. Start the API server:

```bash
python -m api.main
```

Or using uvicorn directly:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Get Default User Credentials

Before using the API, you need to know the default user credentials:

```bash
python scripts/show_default_user.py
```

This will display the default username. The password is logged to the server logs during startup.

### Access Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

## API Examples

### Authentication

First, authenticate to get an access token:

```bash
curl -X POST "http://localhost:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "default_abc123",
    "password": "your_password_here"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Use the `access_token` in subsequent requests:

```bash
export TOKEN="your_access_token_here"

# Include token in Authorization header
curl -X GET "http://localhost:8000/v1/sessions" \
  -H "Authorization: Bearer $TOKEN"
```

### Create a Session

```bash
curl -X POST "http://localhost:8000/v1/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "description": "Test simulation"
    }
  }'
```

### Get Session Status

```bash
curl -X GET "http://localhost:8000/v1/sessions/{session_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Start Simulation

```bash
curl -X POST "http://localhost:8000/v1/sessions/{session_id}/start" \
  -H "Authorization: Bearer $TOKEN"
```

### Stop Simulation

```bash
curl -X POST "http://localhost:8000/v1/sessions/{session_id}/stop" \
  -H "Authorization: Bearer $TOKEN"
```

### Delete Session

```bash
curl -X DELETE "http://localhost:8000/v1/sessions/{session_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token

When your access token expires, use the refresh token to get a new one:

```bash
curl -X POST "http://localhost:8000/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token_here"
  }'
```

### Using Python

```python
import requests

# Authenticate
response = requests.post(
    "http://localhost:8000/v1/auth/login",
    json={"username": "default_abc123", "password": "your_password"}
)
tokens = response.json()
access_token = tokens["access_token"]

headers = {"Authorization": f"Bearer {access_token}"}

# Create session
session = requests.post(
    "http://localhost:8000/v1/sessions",
    headers=headers,
    json={"config": {"description": "Test"}}
)
session_data = session.json()

# Start simulation
requests.post(
    f"http://localhost:8000/v1/sessions/{session_data['session_id']}/start",
    headers=headers
)
```

## Project Structure

```text
api/
├── __init__.py           # Package initialization
├── main.py               # FastAPI application entry point
├── config.py             # Configuration settings
├── models/               # Pydantic request/response models
├── routes/               # API endpoint handlers
├── services/             # Business logic layer
├── middleware/           # Custom middleware
├── database/             # Database configuration
└── utils/                # Helper utilities
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black api/
isort api/
```

### Type Checking

```bash
mypy api/
```

## API Versioning

All endpoints are versioned with a `/v1/` prefix:

- `/v1/sessions` - Session management
- `/v1/tasks` - Experimental tasks
- `/v1/auth` - Authentication
- etc.

## Requirements

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- See requirements.txt for full dependency list

## License

MIT
