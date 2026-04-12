"""
Unit Tests for Response Schema Validation Middleware

Tests the schema validation middleware functionality.
"""

from typing import Any

import pytest
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from api.middleware.schema_validation import ResponseSchemaValidationMiddleware


@pytest.fixture
def app_with_validation() -> FastAPI:
    """Create a test FastAPI app with schema validation middleware."""
    app = FastAPI()

    # Add schema validation middleware
    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    # Define test endpoints
    @app.get("/test/valid", response_model=dict)
    async def valid_endpoint() -> dict[str, Any]:
        """Endpoint that returns valid response."""
        return {"status": "ok", "data": {"value": 123}}

    @app.get("/test/invalid-type")
    async def invalid_type_endpoint() -> JSONResponse:
        """Endpoint that returns wrong type."""
        return JSONResponse(status_code=200, content={"status": 123})  # Should be string

    @app.get("/test/missing-field")
    async def missing_field_endpoint() -> JSONResponse:
        """Endpoint that returns response with missing required field."""
        return JSONResponse(status_code=200, content={"data": "test"})  # Missing 'status' field

    @app.get("/test/empty")
    async def empty_endpoint() -> Response:
        """Endpoint that returns empty response."""
        return Response(status_code=204)

    @app.get("/test/error")
    async def error_endpoint() -> JSONResponse:
        """Endpoint that returns error."""
        return JSONResponse(status_code=500, content={"error": "Internal error"})

    return app


@pytest.fixture
def client(app_with_validation: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app_with_validation)


def test_middleware_initialization() -> None:
    """Test that middleware can be initialized."""
    app = FastAPI()

    middleware = ResponseSchemaValidationMiddleware(app=app, enabled=True, fail_on_error=False)

    assert middleware.enabled is True
    assert middleware.fail_on_error is False
    assert middleware.openapi_schema is None


def test_middleware_disabled() -> None:
    """Test that middleware can be disabled."""
    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=False)

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200


def test_valid_response(client: TestClient) -> None:
    """Test that valid responses pass validation."""
    response = client.get("/test/valid")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "data" in data


def test_empty_response(client: TestClient) -> None:
    """Test that empty responses are handled correctly."""
    response = client.get("/test/empty")

    # Should not fail even with empty response
    assert response.status_code == 204


def test_error_response_not_validated(client: TestClient) -> None:
    """Test that 5xx error responses are not validated."""
    response = client.get("/test/error")

    # Should not fail validation for 5xx errors
    assert response.status_code == 500


def test_get_response_schema() -> None:
    """Test schema extraction from OpenAPI spec."""
    app = FastAPI()

    @app.get("/test/{item_id}")
    async def test_endpoint(item_id: str) -> dict[str, str]:
        return {"id": item_id}

    middleware = ResponseSchemaValidationMiddleware(app=app, enabled=True)

    # Get OpenAPI schema
    openapi_schema = app.openapi()
    middleware.openapi_schema = openapi_schema

    # Test exact path match
    schema = middleware._get_response_schema("/test/123", "get", 200)
    assert schema is not None


def test_find_matching_path() -> None:
    """Test path matching with parameters."""
    app = FastAPI()

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str) -> dict[str, str]:
        return {"session_id": session_id}

    middleware = ResponseSchemaValidationMiddleware(app=app, enabled=True)

    # Get OpenAPI schema
    openapi_schema = app.openapi()
    middleware.openapi_schema = openapi_schema

    # Test path parameter matching
    path_item = middleware._find_matching_path("/sessions/abc123")
    assert path_item is not None


def test_validate_schema_basic() -> None:
    """Test basic schema validation."""
    middleware = ResponseSchemaValidationMiddleware(app=FastAPI(), enabled=True)

    # Test valid object
    schema = {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["status"],
                    "properties": {"status": {"type": "string"}, "data": {"type": "object"}},
                }
            }
        }
    }

    data = {"status": "ok", "data": {}}
    errors = middleware._validate_schema(data, schema)
    assert len(errors) == 0


def test_validate_schema_missing_required() -> None:
    """Test validation with missing required field."""
    middleware = ResponseSchemaValidationMiddleware(app=FastAPI(), enabled=True)

    schema = {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["status", "data"],
                    "properties": {"status": {"type": "string"}, "data": {"type": "object"}},
                }
            }
        }
    }

    data = {"status": "ok"}  # Missing 'data'
    errors = middleware._validate_schema(data, schema)
    assert len(errors) > 0
    assert any("data" in str(error) for error in errors)


def test_validate_schema_wrong_type() -> None:
    """Test validation with wrong field type."""
    middleware = ResponseSchemaValidationMiddleware(app=FastAPI(), enabled=True)

    schema = {
        "content": {
            "application/json": {
                "schema": {"type": "object", "properties": {"count": {"type": "integer"}}}
            }
        }
    }

    data = {"count": "not a number"}
    errors = middleware._validate_schema(data, schema)
    assert len(errors) > 0


def test_validate_field_types() -> None:
    """Test field type validation."""
    middleware = ResponseSchemaValidationMiddleware(app=FastAPI(), enabled=True)

    # Test string
    errors = middleware._validate_field("test", {"type": "string"}, "field")
    assert len(errors) == 0

    # Test integer
    errors = middleware._validate_field(123, {"type": "integer"}, "field")
    assert len(errors) == 0

    # Test boolean
    errors = middleware._validate_field(True, {"type": "boolean"}, "field")
    assert len(errors) == 0

    # Test array
    errors = middleware._validate_field([1, 2, 3], {"type": "array"}, "field")
    assert len(errors) == 0

    # Test object
    errors = middleware._validate_field({}, {"type": "object"}, "field")
    assert len(errors) == 0

    # Test wrong type
    errors = middleware._validate_field("test", {"type": "integer"}, "field")
    assert len(errors) > 0


def test_schema_cache() -> None:
    """Test that schemas are cached."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    middleware = ResponseSchemaValidationMiddleware(app=app, enabled=True)

    openapi_schema = app.openapi()
    middleware.openapi_schema = openapi_schema

    # First call - should cache
    schema1 = middleware._get_response_schema("/test", "get", 200)

    # Second call - should use cache
    schema2 = middleware._get_response_schema("/test", "get", 200)

    # Should be the same object (from cache)
    assert schema1 is schema2

    # Check cache was populated
    cache_key = "get:/test:200"
    assert cache_key in middleware._schema_cache


@pytest.mark.asyncio
async def test_get_response_body() -> None:
    """Test response body extraction."""
    middleware = ResponseSchemaValidationMiddleware(app=FastAPI(), enabled=True)

    # Test with bytes body
    response = Response(content=b'{"test": "data"}')
    body = await middleware._get_response_body(response)
    assert body == '{"test": "data"}'

    # Test with empty body
    response = Response(content=b"")
    body = await middleware._get_response_body(response)
    assert body is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
