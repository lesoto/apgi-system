"""
Rate Limiting Middleware

Middleware for enforcing rate limits on API requests.
"""

from datetime import datetime

import redis.asyncio as redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from typing import List, Optional
from api.middleware.logging import StructuredLogger
from api.services.rate_limiter import RateLimiter

logger = StructuredLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on API requests.

    Checks rate limits before processing requests and adds rate limit
    headers to all responses.
    """

    def __init__(
        self,
        app,
        redis_client=None,
        enabled: bool = True,
        trusted_proxies: Optional[List[str]] = None,
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            redis_client: Redis client for rate limiting (optional)
            enabled: Whether rate limiting is enabled
            trusted_proxies: List of trusted proxy IPs that can set X-Forwarded-For
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.enabled = enabled
        self.rate_limiter = RateLimiter(redis_client)
        # Fallback in-memory rate limiter for when Redis is unavailable
        self.fallback_rate_limiter = RateLimiter(redis_client=None)  # In-memory
        self.trusted_proxies = trusted_proxies or []

    def set_redis_client(self, redis_client: redis.Redis):
        """
        Set Redis client and initialize rate limiter.

        Args:
            redis_client: Redis client for rate limiting
        """
        self.redis_client = redis_client
        self.rate_limiter = RateLimiter(redis_client)

    def _get_client_id(self, request: Request) -> str:
        """
        Extract client identifier from request.

        Uses authenticated user ID if available, otherwise falls back to IP address
        from X-Forwarded-For header or client host.

        Args:
            request: HTTP request

        Returns:
            Client identifier string
        """
        # Try to get user ID from request state (set by authentication middleware)
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.user_id}"

        # Fall back to IP address, checking proxy headers first
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """
        Get the real client IP address, checking proxy headers only from trusted proxies.

        Only trusts X-Forwarded-For when the request comes from a trusted proxy IP.

        Args:
            request: HTTP request

        Returns:
            Client IP address string
        """
        # If the client is from a trusted proxy, use X-Forwarded-For
        if request.client and request.client.host in self.trusted_proxies:
            # Check X-Forwarded-For header (most common proxy header)
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                # X-Forwarded-For can contain multiple IPs separated by commas
                # The first IP is the original client IP
                first_ip = x_forwarded_for.split(",")[0].strip()
                if first_ip:
                    return first_ip

        # Check X-Real-IP header (used by some proxies)
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip.strip()

        # Fall back to request.client.host
        client_ip = request.client.host if request.client else "unknown"
        return client_ip

    def _get_endpoint_identifier(self, request: Request) -> str:
        """
        Get endpoint identifier for rate limiting.

        Maps request paths to endpoint identifiers for rate limit configuration.

        Args:
            request: HTTP request

        Returns:
            Endpoint identifier string
        """
        path = request.url.path
        method = request.method

        # Map paths to endpoint identifiers
        if path.startswith("/v1/sessions") and method == "POST":
            if path.endswith("/tasks"):
                return "task:execute"
            return "session:create"
        elif path.startswith("/v1/sessions") and method == "GET":
            return "session:read"
        elif path.startswith("/v1/sessions") and method == "DELETE":
            return "session:delete"
        elif path.startswith("/v1/sessions") and "export" in path:
            return "data:export"
        elif path.startswith("/v1/tasks"):
            return "task:execute"
        elif path == "/v1/auth/login" and method == "POST":
            return "auth:login"
        else:
            return "global"

    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """
        Determine if rate limiting should be skipped for this request.

        Args:
            request: HTTP request

        Returns:
            True if rate limiting should be skipped
        """
        path = request.url.path

        # Skip rate limiting for health checks and metrics
        if path in ["/health", "/v1/health", "/v1/metrics"]:
            return True

        # Skip for docs
        if path in ["/docs", "/redoc", "/openapi.json"]:
            return True

        return False

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with rate limit headers
        """
        # Get client and endpoint identifiers
        client_id = self._get_client_id(request)
        endpoint = self._get_endpoint_identifier(request)

        # Check if rate limiting should be skipped
        skip_rate_limiting = self._should_skip_rate_limiting(request) or not self.enabled

        if skip_rate_limiting:
            # For skipped endpoints, get rate limit info without enforcing limits
            try:
                result = await self.rate_limiter.get_rate_limit_status(
                    client_id=client_id, endpoint=endpoint
                )
                rate_limit_headers = self.rate_limiter.get_rate_limit_headers(result)
            except Exception as e:
                # If rate limit check fails, provide default headers
                logger.warning(f"Failed to get rate limit info for skipped endpoint: {e}")
                rate_limit_headers = {
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "60",
                    "X-RateLimit-Reset": str(int(datetime.utcnow().timestamp()) + 60),
                }

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            for header_name, header_value in rate_limit_headers.items():
                response.headers[header_name] = header_value

            return response

        # Rate limiting is enabled - enforce limits
        try:
            # Check rate limit
            result = await self.rate_limiter.check_rate_limit(
                client_id=client_id, endpoint=endpoint
            )

            # Get rate limit headers
            rate_limit_headers = self.rate_limiter.get_rate_limit_headers(result)

            if not result.allowed:
                # Rate limit exceeded - return 429
                logger.warning(
                    "Rate limit exceeded",
                    client_id=client_id,
                    endpoint=endpoint,
                    limit=result.limit,
                    retry_after=result.retry_after,
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "details": {
                                "limit": result.limit,
                                "retry_after": result.retry_after,
                                "reset_at": result.reset_at.isoformat() + "Z",
                            },
                        }
                    },
                    headers=rate_limit_headers,
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            for header_name, header_value in rate_limit_headers.items():
                response.headers[header_name] = header_value

            return response

        except Exception as e:
            # Log error but try fallback in-memory rate limiting
            logger.error(
                "Rate limiting error", error=str(e), client_id=client_id, endpoint=endpoint
            )

            # Try in-memory fallback rate limiting
            try:
                result = await self.fallback_rate_limiter.check_rate_limit(
                    client_id=client_id, endpoint=endpoint
                )

                # Get rate limit headers
                rate_limit_headers = self.fallback_rate_limiter.get_rate_limit_headers(result)

                if not result.allowed:
                    # Rate limit exceeded even with fallback
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": "Too many requests. Please try again later.",
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "details": {
                                    "limit": result.limit,
                                    "retry_after": result.retry_after,
                                    "reset_at": result.reset_at.isoformat() + "Z",
                                },
                            }
                        },
                        headers=rate_limit_headers,
                    )

                # Process request with fallback rate limiting
                response = await call_next(request)

                # Add rate limit headers to response
                for header_name, header_value in rate_limit_headers.items():
                    response.headers[header_name] = header_value

                return response

            except Exception as fallback_e:
                # If even fallback fails, allow request with restrictive headers
                logger.error(
                    "Fallback rate limiting error",
                    error=str(fallback_e),
                    client_id=client_id,
                    endpoint=endpoint,
                )
                response = await call_next(request)
                # Set very restrictive headers when rate limiting is completely unavailable
                response.headers["X-RateLimit-Limit"] = "1"
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(int(datetime.utcnow().timestamp()) + 60)

                return response
