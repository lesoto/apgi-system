"""
HTTPS Redirect Middleware

Middleware to redirect HTTP requests to HTTPS when HTTPS is enabled.
"""

from typing import Any, Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS.

    Redirects all HTTP requests to HTTPS when HTTPS is enabled in the configuration.
    This ensures secure communication and prevents mixed content issues.
    """

    def __init__(self, app: Any, https_enabled: bool) -> None:
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
            https_enabled: Whether HTTPS is enabled
        """
        super().__init__(app)
        self.https_enabled = https_enabled

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and redirect to HTTPS if necessary.

        Args:
            request: The incoming request
            call_next: The next middleware in the chain

        Returns:
            Response: Either a redirect response or the original response
        """
        if self.https_enabled and request.url.scheme == "http":
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(https_url, status_code=301)

        # Continue with the request
        return await call_next(request)
