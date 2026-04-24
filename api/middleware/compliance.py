"""
Compliance Middleware

Enforces compliance controls including:
- Consent validation for sensitive endpoints
- Data minimization policy enforcement
- Access auditing for sensitive data
- Retention policy compliance
"""

from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from apgi_framework.compliance.compliance_framework import (
    DataClassification,
    get_compliance_framework,
)
from api.compliance.consent_validation import (
    ConsentPurpose,
    get_consent_validator,
)
from api.compliance.data_minimization import (
    RetentionPolicy,
    get_minimization_manager,
)
from api.middleware.logging import StructuredLogger

logger = StructuredLogger(__name__)

# Sensitive endpoint patterns requiring consent validation
SENSITIVE_ENDPOINT_PATTERNS = [
    "/v1/sensitive/",
    "/v1/sessions/",  # Session data may contain PHI
    "/v1/export/",  # Data exports
    "/v1/admin/users/",  # User management
]

# Required consent purposes for sensitive endpoints
SENSITIVE_REQUIRED_PURPOSES = [
    ConsentPurpose.DATA_COLLECTION.value,
    ConsentPurpose.PROCESSING.value,
]

# Default retention policies
DEFAULT_RETENTION_POLICIES = [
    RetentionPolicy(
        data_type="session_data",
        retention_days=2555,  # 7 years for research
        purpose="consciousness_research",
        legal_basis="consent",
    ),
    RetentionPolicy(
        data_type="export_logs",
        retention_days=365,  # 1 year for audit
        purpose="audit_trail",
        legal_basis="legal_obligation",
    ),
    RetentionPolicy(
        data_type="user_consent_records",
        retention_days=2555,  # 7 years
        purpose="consent_management",
        legal_basis="legal_obligation",
    ),
]


class ComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces compliance policies:
    - Consent validation for sensitive endpoints
    - Data minimization and retention enforcement
    - Access auditing for sensitive data
    - Compliance headers
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.compliance_framework = get_compliance_framework()
        self.consent_validator = get_consent_validator()
        self.minimization_manager = get_minimization_manager()

        # Register default retention policies
        for policy in DEFAULT_RETENTION_POLICIES:
            self.minimization_manager.register_retention_policy(policy)

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint requires consent validation."""
        return any(path.startswith(pattern) for pattern in SENSITIVE_ENDPOINT_PATTERNS)

    def _validate_consent(self, request: Request) -> None:
        """
        Validate consent for sensitive endpoints.

        Raises:
            HTTPException: If consent validation fails
        """
        # Get subject ID from authenticated user
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required for sensitive endpoints",
            )

        subject_id = user.user_id

        # Validate consent
        validation_result = self.consent_validator.validate_consent(
            subject_id=subject_id,
            required_purposes=SENSITIVE_REQUIRED_PURPOSES,
            data_type="sensitive_data",
        )

        if not validation_result.is_valid:
            logger.warning(
                f"Consent validation failed for {subject_id}",
                endpoint=request.url.path,
                errors=validation_result.errors,
                missing_purposes=validation_result.missing_purposes,
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Consent validation failed",
                    "errors": validation_result.errors,
                    "missing_purposes": validation_result.missing_purposes,
                },
            )

        logger.info(
            f"Consent validated for {subject_id}",
            endpoint=request.url.path,
            granted_purposes=validation_result.granted_purposes,
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Determine user ID from auth middleware
        user = getattr(request.state, "user", None)
        user_id = user.user_id if user else "anonymous"

        # Validate consent for sensitive endpoints (before processing)
        if self._is_sensitive_endpoint(request.url.path):
            self._validate_consent(request)

        response = await call_next(request)

        # Add compliance headers
        response.headers["X-Compliance-Audited"] = "true"

        # Add consent validation header for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["X-Consent-Validated"] = "true"

        # Log audit for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
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
