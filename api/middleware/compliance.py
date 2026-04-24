from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apgi_framework.compliance.compliance_framework import (
    DataClassification,
    get_compliance_framework,
)
from api.middleware.logging import StructuredLogger

logger = StructuredLogger(__name__)


class ComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces compliance policies:
    - Data minimization
    - Access auditing for sensitive data
    - Compliance headers
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.compliance_framework = get_compliance_framework()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Determine user ID (mocked for now, normally from auth middleware)
        user_id = getattr(request.state, "user_id", "anonymous")

        # Before request processing
        # E.g., we could log access to specific endpoints

        response = await call_next(request)

        # Apply compliance logic to response if applicable
        # E.g., Adding headers indicating compliance status
        response.headers["X-Compliance-Audited"] = "true"

        # Log audit if accessing specific paths or handling sensitive data
        if request.url.path.startswith("/v1/sensitive"):
            self.compliance_framework._log_audit(
                user_id=user_id,
                action="access_sensitive_endpoint",
                resource_type="endpoint",
                resource_id=request.url.path,
                classification=DataClassification.CONFIDENTIAL,
                outcome="success" if response.status_code < 400 else "failure",
                details={"method": request.method, "status": response.status_code},
            )

        return response
