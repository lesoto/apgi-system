"""
Authentication Middleware

Middleware to extract and verify JWT tokens from Authorization headers.
"""

import hashlib
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api.database.connection import AsyncSessionLocal
from api.exceptions import ExpiredTokenError, InvalidTokenError
from api.services.auth_manager import AuthManager, TokenPayload

logger = logging.getLogger(__name__)

# In-memory token cache with TTL (5 minutes default)
# Structure: {token_hash: (TokenPayload, expiration_timestamp)}
_token_cache: Dict[str, tuple[TokenPayload, float]] = {}
TOKEN_CACHE_TTL_SECONDS = 300  # 5 minutes


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and verify JWT tokens from Authorization headers.

    This middleware:
    1. Extracts JWT token from Authorization header
    2. Verifies the token
    3. Attaches user identity to request state
    4. Handles token expiration and invalid tokens

    Public endpoints (those not requiring authentication) are excluded from token verification.
    """

    # Endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/v1/auth/login",
        "/v1/auth/refresh",
        "/v1/health/live",
        "/v1/health/ready",
    }

    def __init__(self, app: Any) -> None:
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and verify authentication.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler or error response
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Extract token from Authorization header
        token = self._extract_token(request)

        if not token:
            # No token provided - let the endpoint handle it
            # (some endpoints may be optional auth)
            return await call_next(request)

        # Verify token and attach user to request state
        try:
            user_payload = await self._verify_token(token)

            # Attach user information to request state
            request.state.user = user_payload
            request.state.authenticated = True

            # Continue to next handler
            response = await call_next(request)
            return response

        except ExpiredTokenError as e:
            # Token has expired
            return self._create_error_response(
                status_code=401, code="TOKEN_EXPIRED", message=str(e)
            )
        except InvalidTokenError as e:
            # Token is invalid
            return self._create_error_response(
                status_code=401, code="INVALID_TOKEN", message=str(e)
            )
        except Exception as e:
            # Unexpected error (e.g., database failure) - log and return 500
            # instead of masking it as an authentication failure
            logger.error(f"Internal error during token verification: {str(e)}", exc_info=True)
            return self._create_error_response(
                status_code=500,
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
            )

    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is public (doesn't require authentication).

        Args:
            path: Request path

        Returns:
            True if path is public, False otherwise
        """
        # Check exact matches first
        if path in self.PUBLIC_PATHS:
            return True

        # Check for path patterns that should be public (e.g., static files)
        # Only use prefix matching for specific safe patterns
        path_prefixes = [
            "/static/",
            "/docs/",
            "/redoc/",
        ]

        for prefix in path_prefixes:
            if path.startswith(prefix):
                return True

        return False

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Args:
            request: HTTP request

        Returns:
            Token string if present, None otherwise
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        # Expected format: "Bearer <token>"
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    async def _verify_token(self, token: str) -> TokenPayload:
        """
        Verify JWT token and extract payload with caching.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with user information

        Raises:
            InvalidTokenError: If token is invalid
            ExpiredTokenError: If token has expired
        """
        import time

        # Create cache key from token hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Check if token is blacklisted (must be done before cache hit)
        async with AsyncSessionLocal() as db:
            auth_manager = AuthManager(db)  # type: ignore[arg-type]
            if await auth_manager.is_token_blacklisted(token):
                raise InvalidTokenError("Token has been revoked")

        # Check cache after blacklist check
        current_time = time.time()
        if token_hash in _token_cache:
            cached_payload, expiration = _token_cache[token_hash]
            if current_time < expiration:
                logger.debug(f"Token cache hit for user {cached_payload.user_id}")
                return cached_payload
            else:
                del _token_cache[token_hash]
                logger.debug("Token cache entry expired, re-verifying")

        # Cache miss or expired - verify with database
        async with AsyncSessionLocal() as db:
            auth_manager = AuthManager(db)  # type: ignore[arg-type]
            payload = auth_manager.verify_token(token, expected_type="access")

            # Cache the result with TTL (token expiration or cache TTL, whichever is sooner)
            cache_expiration = min(
                current_time + TOKEN_CACHE_TTL_SECONDS,
                payload.exp.timestamp(),
            )
            _token_cache[token_hash] = (payload, cache_expiration)
            logger.debug(f"Token cached for user {payload.user_id}")

            return payload

    def _create_error_response(self, status_code: int, code: str, message: str) -> JSONResponse:
        """
        Create standardized error response.

        Args:
            status_code: HTTP status code
            code: Error code
            message: Error message

        Returns:
            JSONResponse with error details
        """
        from datetime import datetime

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
            },
        )


def get_current_user_from_request(request: Request) -> Optional[TokenPayload]:
    """
    Get current authenticated user from request state.

    This is a helper function to access the user attached by the middleware.

    Args:
        request: HTTP request

    Returns:
        TokenPayload if user is authenticated, None otherwise
    """
    return getattr(request.state, "user", None)


def is_authenticated(request: Request) -> bool:
    """
    Check if request is authenticated.

    Args:
        request: HTTP request

    Returns:
        True if authenticated, False otherwise
    """
    return getattr(request.state, "authenticated", False)
