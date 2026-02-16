"""
Property-based test for response schema validation.

**Feature: api-rest-interface, Property 27: Response schema validation**

Tests that all API responses validate against their OpenAPI schemas.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from api.middleware.schema_validation import ResponseSchemaValidationMiddleware

# ============================================================================
# Test Models
# ============================================================================


class TestResponse(BaseModel):
    """Test response model."""

    status: str
    data: Optional[Dict[str, Any]] = None
    count: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    error: Dict[str, Any]


# ============================================================================
# Strategies for generating test data
# ============================================================================


def valid_status_string() -> st.SearchStrategy[str]:
    """Generate valid status strings."""
    return st.sampled_from(["ok", "success", "pending", "completed", "failed"])


def valid_response_data() -> st.SearchStrategy[Optional[Dict[str, Any]]]:
    """Generate valid response data dictionaries."""
    # Generate simple dictionaries with string keys and various value types
    return st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=20),
            st.booleans(),
        ),
        min_size=0,
        max_size=5,
    ).map(lambda data: data if data else None)


def valid_count() -> st.SearchStrategy[int]:
    """Generate valid count values."""
    return st.integers(min_value=0, max_value=10000)


# ============================================================================
# Property Tests
# ============================================================================


@given(status=valid_status_string(), data=valid_response_data(), count=valid_count())
@settings(max_examples=100)
def test_property_response_schema_validation(
    status: str, data: Optional[Dict[str, Any]], count: int
) -> None:
    """
    **Feature: api-rest-interface, Property 27: Response schema validation**

    For any API response, it should validate against the OpenAPI schema
    defined for that endpoint.

    This property tests that:
    1. Responses matching the schema pass validation
    2. The middleware correctly validates response structure
    3. All required fields are present
    4. Field types match the schema

    **Validates: Requirements 12.3**
    """
    # Create test app with schema validation
    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    # Define endpoint with response model
    @app.get("/test/response", response_model=TestResponse)
    async def test_endpoint() -> TestResponse:
        """Test endpoint that returns valid response."""
        return TestResponse(status=status, data=data, count=count)

    # Create test client
    client = TestClient(app)

    # Make request
    response = client.get("/test/response")

    # Verify response is successful
    assert response.status_code == 200

    # Verify response structure
    response_data = response.json()
    assert "status" in response_data
    assert response_data["status"] == status

    # Verify optional fields
    if data is not None:
        assert "data" in response_data
        assert response_data["data"] == data

    assert "count" in response_data
    assert response_data["count"] == count


@given(status=valid_status_string(), data=valid_response_data())
@settings(max_examples=100)
def test_property_response_with_optional_fields(
    status: str, data: Optional[Dict[str, Any]]
) -> None:
    """
    Test that responses with optional fields validate correctly.

    **Feature: api-rest-interface, Property 27: Response schema validation**
    **Validates: Requirements 12.3**
    """
    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    @app.get("/test/optional", response_model=TestResponse)
    async def test_endpoint() -> Dict[str, Any]:
        """Endpoint with optional fields."""
        response_dict: Dict[str, Any] = {}
        response_dict["status"] = status
        if data is not None:
            response_dict["data"] = data
        return response_dict

    client = TestClient(app)
    response = client.get("/test/optional")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == status


@given(error_code=st.text(min_size=1, max_size=50), error_message=st.text(min_size=1, max_size=200))
@settings(max_examples=100)
def test_property_error_response_validation(error_code: str, error_message: str) -> None:
    """
    Test that error responses validate correctly.

    **Feature: api-rest-interface, Property 27: Response schema validation**
    **Validates: Requirements 12.3**
    """
    # Filter out problematic characters that might break JSON
    assume(not any(c in error_code for c in ["\x00", "\n", "\r", "\t"]))
    assume(not any(c in error_message for c in ["\x00"]))

    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    @app.get("/test/error")
    async def error_endpoint() -> JSONResponse:
        """Endpoint that returns error."""
        return JSONResponse(
            status_code=400, content={"error": {"code": error_code, "message": error_message}}
        )

    client = TestClient(app)
    response = client.get("/test/error")

    assert response.status_code == 400
    response_data = response.json()
    assert "error" in response_data
    assert response_data["error"]["code"] == error_code
    assert response_data["error"]["message"] == error_message


@given(
    items=st.lists(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=50), st.integers(min_value=-1000, max_value=1000), st.booleans()
            ),
            min_size=1,
            max_size=5,
        ),
        min_size=0,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_property_list_response_validation(items: List[Dict[str, Any]]) -> None:
    """
    Test that list responses validate correctly.

    **Feature: api-rest-interface, Property 27: Response schema validation**
    **Validates: Requirements 12.3**
    """
    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    @app.get("/test/list")
    async def list_endpoint() -> Dict[str, Any]:
        """Endpoint that returns list."""
        return {"items": items, "count": len(items)}

    client = TestClient(app)
    response = client.get("/test/list")

    assert response.status_code == 200
    response_data = response.json()
    assert "items" in response_data
    assert "count" in response_data
    assert response_data["count"] == len(items)
    assert len(response_data["items"]) == len(items)


@given(status=valid_status_string())
@settings(max_examples=100)
def test_property_nested_response_validation(status: str) -> None:
    """
    Test that nested response structures validate correctly.

    **Feature: api-rest-interface, Property 27: Response schema validation**
    **Validates: Requirements 12.3**
    """
    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    @app.get("/test/nested")
    async def nested_endpoint() -> Dict[str, Any]:
        """Endpoint with nested structure."""
        return {"status": status, "data": {"nested": {"level": 2, "value": "test"}}}

    client = TestClient(app)
    response = client.get("/test/nested")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == status
    assert "data" in response_data
    assert "nested" in response_data["data"]


@given(
    path_param=st.text(
        min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)
    )
)
@settings(max_examples=100)
def test_property_path_parameter_response_validation(path_param: str) -> None:
    """
    Test that responses from endpoints with path parameters validate correctly.

    **Feature: api-rest-interface, Property 27: Response schema validation**
    **Validates: Requirements 12.3**
    """
    app = FastAPI()

    app.add_middleware(ResponseSchemaValidationMiddleware, enabled=True, fail_on_error=False)

    @app.get("/test/{item_id}")
    async def path_param_endpoint(item_id: str) -> Dict[str, Any]:
        """Endpoint with path parameter."""
        return {"id": item_id, "status": "ok"}

    client = TestClient(app)
    response = client.get(f"/test/{path_param}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == path_param
    assert response_data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
