# Database Migrations

This Alembic database migrations for the APGI REST API.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure database URL in `.env` file or environment variable:

```bash
DATABASE_URL=postgresql://user:password@localhost/apgi_api
```

## Running Migrations

### Apply all pending migrations

```bash
alembic upgrade head
```

### Revert last migration

```bash
alembic downgrade -1
```

### Revert all migrations

```bash
alembic downgrade base
```

### View migration history

```bash
alembic history
```

### View current revision

```bash
alembic current
```

## Creating New Migrations

### Auto-generate migration from model changes

```bash
alembic revision --autogenerate -m "description of changes"
```

### Create empty migration

```bash
alembic revision -m "description of changes"
```

## Migration Files

Migrations are stored in `api/alembic/versions/` directory.

### Initial Schema (001)

- Creates all base tables: users, sessions, tasks, session_data, refresh_tokens, webhook_deliveries
- Sets up indexes for performance
- Configures foreign key relationships with cascade deletes

## Database Schema

### Tables

- **users**: User accounts with authentication and RBAC
- **sessions**: Simulation sessions with configuration and state
- **tasks**: Experimental tasks with async execution tracking
- **session_data**: Time series data for simulation sessions
- **refresh_tokens**: JWT refresh token storage
- **webhook_deliveries**: Webhook delivery tracking with retry logic

### Indexes

Performance indexes are created for:

- User lookups (username, email)
- Session queries (user_id + created_at, state)
- Task queries (session_id + created_at, status, type)
- Time series queries (session_id + time_ms)
- Token lookups (token_hash, expires_at)
- Webhook retries (next_retry_at)

## Notes

- All timestamps use timezone-aware DateTime (UTC)
- JSONB is used for flexible configuration and data storage
- Foreign keys use CASCADE delete for automatic cleanup
- UUIDs (as strings) are used for primary keys
