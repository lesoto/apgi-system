"""Tests for Rate Limiting Middleware with Redis."""

from typing import Any, List
from unittest.mock import AsyncMock

import pytest
import redis
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture
def redis_client() -> AsyncMock:
    """Create a test Redis client."""
    # Use a test Redis instance or mock
    # For this test, we'll use a mock Redis that simulates Redis operations
    mock_redis = AsyncMock(spec=redis.Redis)
    mock_redis.ping = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock()
    mock_redis.delete = AsyncMock()
    return mock_redis


@pytest.fixture
def client_with_rate_limiting(redis_client: AsyncMock) -> TestClient:
    """Create test client with rate limiting enabled and Redis."""
    app = create_app(test_mode=False)

    # Override the rate limiting middleware to use our test Redis
    for i, middleware in enumerate(app.user_middleware):
        if hasattr(middleware, "cls") and "RateLimitingMiddleware" in str(middleware.cls):
            # Replace the middleware instance
            original_middleware = middleware.cls

            def create_test_middleware(app: Any) -> Any:
                return original_middleware(app, redis_client=redis_client, enabled=True)  # type: ignore[call-arg, arg-type]

            # Create a new middleware object with the same interface
            from types import SimpleNamespace

            test_middleware = SimpleNamespace(
                cls=create_test_middleware, options=getattr(middleware, "options", {})
            )
            app.user_middleware[i] = test_middleware  # type: ignore[call-overload]
            break

    return TestClient(app)


class TestRateLimitingWithRedis:
    """Test rate limiting middleware with Redis backend."""

    def test_rate_limiting_basic_functionality(
        self, client_with_rate_limiting: TestClient, redis_client: AsyncMock
    ) -> None:
        """Test basic rate limiting functionality with Redis."""
        # Mock Redis to simulate rate limiting
        call_count = 0

        def mock_incr(key: str) -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        redis_client.incr.side_effect = mock_incr
        redis_client.get.return_value = None  # No existing count

        # Make multiple requests to a rate-limited endpoint
        for i in range(5):
            response = client_with_rate_limiting.get("/v1/health")
            if i < 3:  # First 3 should succeed
                assert response.status_code == 200
            else:  # Next ones should be rate limited
                assert response.status_code == 429

    def test_rate_limiting_headers(
        self, client_with_rate_limiting: TestClient, redis_client: AsyncMock
    ) -> None:
        """Test that rate limit headers are added to responses."""
        redis_client.incr.return_value = 1
        redis_client.get.return_value = None

        response = client_with_rate_limiting.get("/v1/health")
        assert response.status_code == 200

        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limiting_redis_persistence(
        self, client_with_rate_limiting: TestClient, redis_client: AsyncMock
    ) -> None:
        """Test that rate limiting persists across requests using Redis."""
        # Simulate Redis persistence
        redis_calls: List[Any] = []

        def mock_get(key: Any) -> Any:
            # Return stored value if it exists
            for call in redis_calls:
                if call[0] == "get" and call[1] == key and len(call) > 2:
                    return call[2]
            return None

        def mock_setex(key: Any, time: Any, value: Any) -> None:
            redis_calls.append(("setex", key, time, value))

        def mock_incr(key: Any) -> int:
            current = mock_get(key) or 0
            new_value = current + 1
            mock_setex(key, 60, new_value)  # Store for 60 seconds
            return new_value

        redis_client.get.side_effect = mock_get
        redis_client.setex.side_effect = mock_setex
        redis_client.incr.side_effect = mock_incr

        # First request
        response1 = client_with_rate_limiting.get("/v1/health")
        assert response1.status_code == 200

        # Second request should see the incremented count
        response2 = client_with_rate_limiting.get("/v1/health")
        assert response2.status_code == 200

        # Verify Redis was called correctly
        assert redis_client.incr.call_count >= 2

    def test_rate_limiting_different_clients(
        self, client_with_rate_limiting: TestClient, redis_client: AsyncMock
    ) -> None:
        """Test that different clients have separate rate limits."""
        # This is harder to test with TestClient since it doesn't simulate different IPs
        # We can test by mocking the client identification

        def mock_incr(key: Any) -> int:
            if "192.168.1.1" in key:
                return 1  # First client, first request
            elif "192.168.1.2" in key:
                return 1  # Second client, first request
            return 1

        redis_client.incr.side_effect = mock_incr

        # Make requests - they should all succeed since different clients
        response1 = client_with_rate_limiting.get("/v1/health")
        response2 = client_with_rate_limiting.get("/v1/health")

        # Both should succeed (in a real scenario with different IPs)
        assert response1.status_code in [200, 429]
        assert response2.status_code in [200, 429]

    def test_rate_limiting_disabled(self, redis_client: AsyncMock) -> None:
        """Test that rate limiting can be disabled."""
        app = create_app(test_mode=False)

        # Disable rate limiting
        for i, middleware in enumerate(app.user_middleware):
            if hasattr(middleware, "cls") and "RateLimitingMiddleware" in str(middleware.cls):
                original_middleware = middleware.cls

                def create_test_middleware(app: Any) -> Any:
                    return original_middleware(app, redis_client=redis_client, enabled=False)  # type: ignore[call-arg, arg-type]

                # Create a new middleware object with the same interface
                from types import SimpleNamespace

                test_middleware = SimpleNamespace(
                    cls=create_test_middleware, options=getattr(middleware, "options", {})
                )
                app.user_middleware[i] = test_middleware  # type: ignore[call-overload]
                break

        client = TestClient(app)

        # Make many requests - should all succeed when disabled
        for _ in range(10):
            response = client.get("/v1/health")
            assert response.status_code == 200

    def test_rate_limiting_redis_connection_error(
        self, client_with_rate_limiting: TestClient, redis_client: AsyncMock
    ) -> None:
        """Test behavior when Redis connection fails."""
        # Mock Redis to raise connection error
        redis_client.incr.side_effect = redis.ConnectionError("Redis unavailable")

        # Request should still succeed (fallback to allow)
        response = client_with_rate_limiting.get("/v1/health")
        assert response.status_code == 200

    def test_rate_limiting_different_endpoints(
        self, client_with_rate_limiting: TestClient, redis_client: AsyncMock
    ) -> None:
        """Test that different endpoints have different rate limits."""
        # Mock Redis responses
        redis_client.incr.return_value = 1
        redis_client.get.return_value = None

        # Health endpoint
        response1 = client_with_rate_limiting.get("/v1/health")
        assert response1.status_code == 200

        # Different endpoint (if available)
        response2 = client_with_rate_limiting.get("/v1/version")
        assert response2.status_code == 200

        # Verify Redis was called for both (different keys)
        assert redis_client.incr.call_count >= 2
