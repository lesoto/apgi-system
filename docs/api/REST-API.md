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

### Access Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

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
