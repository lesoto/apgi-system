"""
Security Headers Middleware

Middleware to add security headers to all HTTP responses.
"""

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Adds OWASP recommended security headers to protect against common web vulnerabilities.
    """

    def __init__(self, app: Any, https_enabled: bool = False) -> None:
        """
        Initialize security headers middleware.

        Args:
            app: FastAPI application
            https_enabled: Whether HTTPS is enabled (affects HSTS header)
        """
        super().__init__(app)
        self.https_enabled = https_enabled

    async def dispatch(self, request: Any, call_next: Any) -> Any:
        """
        Add security headers to the response.

        Args:
            request: HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)

        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        # Add HSTS only if HTTPS is enabled
        if self.https_enabled:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        import secrets

        nonce = secrets.token_urlsafe(16)
        # Store nonce in request state so it can be used by template renderers
        request.state.csp_nonce = nonce

        # Add CSP header (restrictive default)
        security_headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'self'; "
            f"style-src 'self' 'nonce-{nonce}'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Set headers on response
        for header_name, header_value in security_headers.items():
            if header_name not in response.headers:
                response.headers[header_name] = header_value

        return response
