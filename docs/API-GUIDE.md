# APGI REST API Setup Guide

This guide walks you through setting up the APGI REST API from scratch.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ (optional, for full functionality)
- Redis 7+ (optional, for caching and task queue)
- Docker and Docker Compose (optional, for containerized deployment)

## Installation Methods

### Method 1: Local Development Setup

#### Step 1: Install Python Dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# At minimum, update:
# - DATABASE_URL (if using PostgreSQL)
# - REDIS_URL (if using Redis)
# - JWT_SECRET_KEY (for production)
```

#### Step 3: Start the API Server

```bash
# Using Python module
python -m api.main

# Or using uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 4: Verify Installation

Open your browser and navigate to:

- API Documentation: <http://localhost:8000/docs>
- Health Check: <http://localhost:8000/health>

### Method 2: Docker Compose (Recommended for Full Stack)

This method sets up the API along with PostgreSQL and Redis.

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at <http://localhost:8000>

### Method 3: Using Setup Scripts

#### On Linux/Mac

```bash
chmod +x api/setup.sh
./api/setup.sh
source venv/bin/activate
python -m api.main
```

#### On Windows (PowerShell)

```powershell
.\api\setup.ps1
.\venv\Scripts\Activate.ps1
python -m api.main
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

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/apgi_api

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET_KEY=your-secret-key-here

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### Configuration File

Settings are managed in `api/config.py` using Pydantic Settings. All settings can be overridden via environment variables.

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=api --cov-report=html

# Run specific test file
pytest tests/test_api_setup.py -v
```

## Development Workflow

### Code Formatting

```bash
# Format code
black api/
isort api/

# Or use make
make format
```

### Linting

```bash
# Run linting
flake8 api/
mypy api/

# Or use make
make lint
```

### Running the Development Server

```bash
# With auto-reload
uvicorn api.main:app --reload

# Or use make
make run
```

## API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: <http://localhost:8000/docs>
  - Interactive API testing interface
  - Try out endpoints directly from the browser

- **ReDoc**: <http://localhost:8000/redoc>
  - Alternative documentation view
  - Better for reading and understanding the API

- **OpenAPI JSON**: <http://localhost:8000/openapi.json>
  - Raw OpenAPI specification
  - Use for code generation or external tools

## Common Issues and Solutions

### Issue: ModuleNotFoundError

**Solution**: Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### Issue: Port 8000 already in use

**Solution**: Use a different port:

```bash
uvicorn api.main:app --port 8001
```

### Issue: Database connection errors

**Solution**:

1. Ensure PostgreSQL is running
2. Verify DATABASE_URL in .env
3. Check database credentials

### Issue: Redis connection errors

**Solution**:

1. Ensure Redis is running: `redis-cli ping`
2. Verify REDIS_URL in .env
3. For development, Redis is optional - the API will work without it

## Next Steps

After successful setup:

1. Review the API documentation at `/docs`
2. Test the health check endpoint: `curl http://localhost:8000/health`
3. Explore the example requests in the documentation
4. Start implementing additional endpoints (see tasks.md)

## Production Deployment

For production deployment:

1. Set strong JWT_SECRET_KEY
2. Configure proper CORS origins
3. Use a production ASGI server (Gunicorn + Uvicorn workers)
4. Set up SSL/TLS certificates
5. Configure proper database connection pooling
6. Enable monitoring and logging
7. Set up rate limiting
8. Use environment-specific configuration

Example production command:

```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Support

For issues or questions:

- Check the API documentation at `/docs`
- Review the design document: `.kiro/specs/api-rest-interface/design.md`
- Check the requirements: `.kiro/specs/api-rest-interface/requirements.md`
