# Design Document: API Standalone Migration

## Overview

This design document outlines the architecture and implementation approach for migrating the existing APGI API application from its current location in the `api/` directory to a standalone, independently deployable application in a new `apgi-api-standalone/` directory at the workspace root.

The migration will preserve all existing functionality while creating a self-contained application that can be deployed independently on a different domain. The standalone API will include its own dependencies, configuration, database migrations, deployment artifacts, and documentation.

### Goals

1. Create a completely independent API application with no dependencies on the main APGI system codebase
2. Preserve all existing functionality, security features, and integration capabilities
3. Enable independent deployment, scaling, and maintenance of the API layer
4. Maintain backward compatibility with existing API clients
5. Provide comprehensive deployment documentation and scripts

### Non-Goals

1. Modifying or enhancing existing API functionality (this is a migration, not a refactor)
2. Changing the API contract or response formats
3. Migrating the main APGI system code (only the API layer)
4. Creating new features or capabilities

## Architecture

### High-Level Structure

The standalone API will follow a layered architecture pattern:

```
apgi-api-standalone/
├── app/                      # Main application package
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── celery_app.py        # Celery configuration
│   ├── exceptions.py        # Custom exceptions
│   ├── exception_handlers.py # Exception handlers
│   ├── database/            # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py    # SQLAlchemy engine and session
│   │   └── models.py        # Database models
│   ├── models/              # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py       # Request/response schemas
│   ├── routes/              # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── sessions.py
│   │   ├── state.py
│   │   ├── tasks.py
│   │   ├── export.py
│   │   ├── metrics.py
│   │   ├── health.py
│   │   └── version.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── auth_manager.py
│   │   ├── authorization.py
│   │   ├── session_manager.py
│   │   ├── task_executor.py
│   │   ├── user_management.py
│   │   ├── webhook_manager.py
│   │   ├── data_export.py
│   │   ├── health_check.py
│   │   └── rate_limiter.py
│   ├── middleware/          # Middleware components
│   │   ├── __init__.py
│   │   ├── authentication.py
│   │   ├── csrf.py
│   │   ├── rate_limiting.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── alerting.py
│   │   ├── deprecation.py
│   │   ├── request_size_limit.py
│   │   └── schema_validation.py
│   ├── tasks/               # Celery tasks
│   │   ├── __init__.py
│   │   ├── experimental_tasks.py
│   │   └── task_registry.py
│   ├── logging/             # Logging configuration
│   │   ├── __init__.py
│   │   └── filters.py
│   └── utils/               # Utility functions
│       └── __init__.py
├── alembic/                 # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── property/
├── scripts/                 # Deployment and utility scripts
│   ├── init_db.sh
│   ├── run_migrations.sh
│   ├── create_admin_user.py
│   ├── start_services.sh
│   └── health_check.sh
├── docs/                    # Documentation
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── CONFIGURATION.md
│   └── DEVELOPMENT.md
├── .env.example             # Environment variable template
├── .gitignore
├── alembic.ini              # Alembic configuration
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Multi-service orchestration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── pyproject.toml           # Package metadata
├── Makefile                 # Common commands
└── README.md                # Setup and usage guide
```

### Component Layers

#### 1. Presentation Layer (Routes)
- FastAPI route handlers organized by resource type
- Request validation using Pydantic schemas
- Response serialization
- OpenAPI documentation generation

#### 2. Business Logic Layer (Services)
- Domain logic and business rules
- Session management and lifecycle
- Authentication and authorization
- Task execution and scheduling
- Data export and transformation
- Health monitoring

#### 3. Data Access Layer (Database)
- SQLAlchemy ORM models
- Database connection management
- Session lifecycle management
- Migration scripts

#### 4. Cross-Cutting Concerns (Middleware)
- Authentication (JWT token verification)
- Authorization (permission checking)
- CORS configuration
- Rate limiting
- Request logging
- Metrics collection
- CSRF protection
- Schema validation
- Request size limiting

#### 5. Asynchronous Processing (Celery)
- Long-running task execution
- Task queuing and routing
- Result storage and retrieval
- Task monitoring

### Technology Stack

- **Web Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn with Gunicorn for production
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Cache/Broker**: Redis 7+
- **Task Queue**: Celery 5+
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic 2+
- **Testing**: pytest, pytest-asyncio, hypothesis
- **Metrics**: Prometheus client
- **Containerization**: Docker, Docker Compose

## Components and Interfaces

### 1. FastAPI Application (main.py)

**Responsibilities:**
- Application initialization and configuration
- Middleware registration
- Route registration
- Lifespan management (startup/shutdown)
- Exception handler registration

**Key Functions:**
- `create_app(test_mode: bool = False) -> FastAPI`: Factory function to create configured FastAPI instance
- `lifespan(app: FastAPI)`: Async context manager for startup/shutdown events

**Interfaces:**
- Exposes HTTP REST API on configurable host:port
- Provides OpenAPI documentation at `/docs` and `/redoc`
- Health check at `/health`
- Metrics at `/metrics`

### 2. Configuration System (config.py)

**Responsibilities:**
- Load configuration from environment variables
- Validate security-critical settings
- Provide configuration defaults for development
- Enforce production security requirements

**Key Classes:**
- `Settings`: Configuration container with validation

**Configuration Categories:**
- API settings (title, version, description)
- Server settings (host, port, reload)
- Database settings (DATABASE_URL)
- Redis settings (REDIS_URL)
- Celery settings (broker, backend)
- Authentication settings (JWT secret, algorithm, expiration)
- CORS settings (origins, credentials, methods, headers)
- Rate limiting settings (enabled, per-minute limit)
- Logging settings (log level)
- Security settings (CSRF, schema validation, request size limits)
- Alerting settings (webhooks, thresholds, cooldowns)

**Validation Rules:**
- JWT secret must be set in production
- JWT secret must be at least 32 characters
- CORS wildcard with credentials is forbidden
- Known insecure defaults trigger errors in production

### 3. Database Layer

#### Connection Management (database/connection.py)

**Responsibilities:**
- Create and configure SQLAlchemy engine
- Manage database sessions
- Initialize database schema
- Create default users
- Handle connection pooling

**Key Functions:**
- `init_db()`: Create tables and default user
- `get_db() -> Generator[Session, None, None]`: Dependency for route handlers
- `get_db_context() -> Generator[Session, None, None]`: Context manager for services
- `close_db()`: Cleanup connections on shutdown
- `create_default_user()`: Create secure default user for session management

**Configuration:**
- Connection pool size: 10
- Max overflow: 20
- Pre-ping enabled for connection health checks

#### Database Models (database/models.py)

**Responsibilities:**
- Define SQLAlchemy ORM models
- Define table schemas and relationships
- Provide model methods for common operations

**Key Models:**
- `User`: User accounts with authentication
- `Session`: Simulation session metadata
- Additional models as needed for API functionality

### 4. Authentication and Authorization

#### Authentication Manager (services/auth_manager.py)

**Responsibilities:**
- Hash and verify passwords (bcrypt)
- Generate and verify JWT tokens
- Manage token lifecycle (access and refresh tokens)
- Extract user identity from tokens

**Key Methods:**
- `hash_password(password: str) -> str`: Hash password with bcrypt
- `verify_password(password: str, hashed: str) -> bool`: Verify password
- `create_access_token(user_id: str, roles: List[str]) -> str`: Generate access token
- `create_refresh_token(user_id: str) -> str`: Generate refresh token
- `verify_token(token: str, expected_type: str) -> TokenPayload`: Verify and decode token

**Token Structure:**
```python
{
    "sub": "user_id",
    "type": "access" | "refresh",
    "roles": ["user", "admin"],
    "exp": timestamp,
    "iat": timestamp
}
```

#### Authorization Service (services/authorization.py)

**Responsibilities:**
- Define permission model
- Check user permissions
- Provide dependency for protected endpoints

**Key Components:**
- `Permission` enum: Defined permissions (SESSION_CREATE, SESSION_READ, etc.)
- `require_permission(permission: Permission)`: Dependency factory for route protection
- `get_current_user()`: Dependency to extract authenticated user

#### Authentication Middleware (middleware/authentication.py)

**Responsibilities:**
- Extract JWT tokens from Authorization headers
- Verify tokens on each request
- Attach user identity to request state
- Handle token expiration and errors

**Flow:**
1. Check if path is public (skip authentication)
2. Extract token from `Authorization: Bearer <token>` header
3. Verify token signature and expiration
4. Attach `TokenPayload` to `request.state.user`
5. Set `request.state.authenticated = True`
6. Return 401 for invalid/expired tokens

### 5. Session Management

#### Session Manager (services/session_manager.py)

**Responsibilities:**
- Create and manage simulation sessions
- Store session metadata in PostgreSQL
- Store session state in Redis
- Manage session lifecycle (created, running, paused, stopped)
- Clean up session resources

**Key Methods:**
- `create_session(request: SessionCreateRequest) -> str`: Create new session
- `get_session(session_id: str) -> SimulationSession`: Retrieve session
- `update_session_state(session_id: str, state: SessionLifecycleState)`: Update state
- `delete_session(session_id: str)`: Delete session and cleanup

**Session Lifecycle States:**
- `CREATED`: Initial state after creation
- `RUNNING`: Simulation is actively running
- `PAUSED`: Simulation is paused
- `STOPPED`: Simulation is stopped
- `ERROR`: Simulation encountered an error

### 6. Middleware Stack

#### Rate Limiting (middleware/rate_limiting.py)

**Responsibilities:**
- Limit requests per client per time window
- Use Redis for distributed rate limiting
- Return 429 Too Many Requests when limit exceeded

**Configuration:**
- Default: 60 requests per minute per IP
- Configurable via `RATE_LIMIT_PER_MINUTE` environment variable

#### CORS Middleware

**Responsibilities:**
- Handle cross-origin requests
- Validate origin against allowed list
- Set appropriate CORS headers

**Configuration:**
- Allowed origins from `CORS_ORIGINS` environment variable
- Credentials support via `CORS_ALLOW_CREDENTIALS`
- Allowed methods and headers configurable

#### CSRF Protection (middleware/csrf.py)

**Responsibilities:**
- Generate CSRF tokens
- Validate CSRF tokens on state-changing requests
- Set CSRF token cookie

**Flow:**
1. Generate token on first request
2. Set token in cookie
3. Require token in `X-CSRF-Token` header for POST/PUT/DELETE
4. Validate token matches cookie

#### Request Logging (middleware/logging.py)

**Responsibilities:**
- Log all incoming requests
- Log request method, path, status, duration
- Use structured logging (JSON format)
- Filter sensitive data from logs

**Log Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "component": "api",
  "method": "GET",
  "path": "/v1/sessions/abc123",
  "status_code": 200,
  "duration_ms": 45.2,
  "user_id": "user_123"
}
```

#### Metrics Collection (middleware/metrics.py)

**Responsibilities:**
- Collect Prometheus metrics
- Track request counts, durations, error rates
- Expose metrics at `/metrics` endpoint

**Metrics:**
- `http_requests_total`: Counter of total requests by method, path, status
- `http_request_duration_seconds`: Histogram of request durations
- `http_requests_in_progress`: Gauge of concurrent requests

### 7. Celery Task Processing

#### Celery Application (celery_app.py)

**Responsibilities:**
- Configure Celery with Redis broker
- Define task routing
- Set task time limits and worker configuration

**Configuration:**
- Broker: Redis (separate database from cache)
- Result backend: Redis
- Task serialization: JSON
- Task time limit: 1 hour hard, 55 minutes soft
- Result expiration: 24 hours

#### Task Executor (services/task_executor.py)

**Responsibilities:**
- Submit tasks to Celery
- Monitor task status
- Retrieve task results
- Handle task errors

**Key Methods:**
- `submit_task(task_name: str, **kwargs) -> str`: Submit task and return task ID
- `get_task_status(task_id: str) -> TaskStatus`: Get task status
- `get_task_result(task_id: str) -> Any`: Get task result
- `cancel_task(task_id: str)`: Cancel running task

### 8. Health Monitoring

#### Health Check Service (services/health_check.py)

**Responsibilities:**
- Check database connectivity
- Check Redis connectivity
- Check Celery worker availability
- Aggregate health status

**Health Check Response:**
```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 5.2},
    "redis": {"status": "healthy", "latency_ms": 1.8},
    "celery": {"status": "healthy", "workers": 2}
  }
}
```

### 9. Data Export Service

#### Export Service (services/data_export.py)

**Responsibilities:**
- Export session data in various formats (JSON, CSV)
- Stream large exports
- Apply data transformations
- Handle export errors

**Key Methods:**
- `export_session_data(session_id: str, format: str) -> bytes`: Export session data
- `export_metrics(session_id: str, format: str) -> bytes`: Export metrics
- `stream_export(session_id: str, format: str) -> AsyncIterator[bytes]`: Stream large exports

## Data Models

### Database Models (SQLAlchemy)

#### User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    roles = Column(ARRAY(String), default=["user"])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

#### Session Model

```python
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    state = Column(String, nullable=False)  # created, running, paused, stopped, error
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="sessions")
```

### API Schemas (Pydantic)

#### Authentication Schemas

```python
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseModel):
    sub: str  # user_id
    type: str  # access or refresh
    roles: List[str]
    exp: int
    iat: int
```

#### Session Schemas

```python
class SessionCreateRequest(BaseModel):
    config: Dict[str, Any]
    description: Optional[str] = None

class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    created_at: datetime
    config: Dict[str, Any]

class SessionResponse(BaseModel):
    session_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    config: Dict[str, Any]
    description: Optional[str] = None

class SessionActionResponse(BaseModel):
    session_id: str
    status: str
    timestamp: datetime
```

#### Error Schemas

```python
class ErrorDetail(BaseModel):
    code: str
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

### Redis Data Structures

#### Session State Cache

```
Key: session:{session_id}:state
Type: Hash
Fields:
  - state: "running" | "paused" | "stopped"
  - updated_at: ISO timestamp
  - metrics: JSON string
TTL: 24 hours
```

#### Rate Limiting

```
Key: ratelimit:{ip_address}:{minute}
Type: String (counter)
Value: Request count
TTL: 60 seconds
```

#### Session Lock

```
Key: lock:session:{session_id}
Type: String
Value: Lock owner ID
TTL: 30 seconds
```

### Configuration Data

#### Environment Variables

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/apgi_api

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Authentication
JWT_SECRET_KEY=<secure-random-key-min-32-chars>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Security
CSRF_PROTECTION_ENABLED=true
SCHEMA_VALIDATION_ENABLED=true
REQUEST_SIZE_LIMIT_MB=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO

# Alerting
ALERT_WEBHOOK_URLS=https://hooks.slack.com/services/xxx
ALERT_ERROR_RATE_THRESHOLD=10
ALERT_ERROR_RATE_WINDOW_MINUTES=1
ALERT_COOLDOWN_MINUTES=5

# Environment
ENVIRONMENT=production
```

