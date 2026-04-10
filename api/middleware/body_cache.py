"""
Request Body Caching Middleware

Caches the request body in request.state to prevent double-read issues
in exception handlers and other middlewares.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RequestBodyCachingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that caches the request body for later use.

    This avoids the 'stream consumed' error when multiple parts of the
    application (e.g., logging, validation, exception handlers) need to
    read the request body.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Cache request body and proceed to next handler.
        """
        # Only cache JSON or form-data requests which are common for body reading
        content_type = request.headers.get("content-type", "")
        if (
            "application/json" in content_type
            or "application/x-www-form-urlencoded" in content_type
        ):
            # Read and cache the body
            body = await request.body()
            request.state.cached_body = body

            # Since request.body() caches the body in Starlette/FastAPI,
            # subsequent calls to request.body() from the endpoint will still work.
            # However, storing it in state provides a reliable backup.

        return await call_next(request)
