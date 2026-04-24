"""
Unit tests for compliance enforcement middleware.

Tests PII detection, masking, and residency validation.
"""

from apgi_framework.compliance.enforcement_middleware import (
    ComplianceEnforcer,
    DataResidencyValidator,
    PIIDetector,
)


class TestPIIDetector:
    """Tests for PII detection."""

    def test_detect_email(self):
        """Test email detection."""
        detector = PIIDetector()
        data = "Contact user@example.com for support"
        detections = detector.detect_pii(data)

        assert len(detections) > 0
        assert any(d["type"] == "email" for d in detections)

    def test_detect_phone(self):
        """Test phone number detection."""
        detector = PIIDetector()
        data = "Call 555-123-4567 for assistance"
        detections = detector.detect_pii(data)

        assert len(detections) > 0
        assert any(d["type"] == "phone" for d in detections)

    def test_detect_ssn(self):
        """Test SSN detection."""
        detector = PIIDetector()
        data = "SSN: 123-45-6789"
        detections = detector.detect_pii(data)

        assert len(detections) > 0
        assert any(d["type"] == "ssn" for d in detections)

    def test_detect_credit_card(self):
        """Test credit card detection."""
        detector = PIIDetector()
        data = "Card: 4532-1234-5678-9010"
        detections = detector.detect_pii(data)

        assert len(detections) > 0
        assert any(d["type"] == "credit_card" for d in detections)

    def test_mask_pii_string(self):
        """Test PII masking in string."""
        detector = PIIDetector()
        data = "Email: user@example.com"
        masked = detector.mask_pii(data)

        assert "user@example.com" not in masked
        assert "*" in masked

    def test_mask_pii_dict(self):
        """Test PII masking in dictionary."""
        detector = PIIDetector()
        data = {"email": "user@example.com", "name": "John Doe"}
        masked = detector.mask_pii(data)

        assert "user@example.com" not in str(masked)
        assert "*" in str(masked)

    def test_mask_pii_list(self):
        """Test PII masking in list."""
        detector = PIIDetector()
        data = ["user@example.com", "555-123-4567"]
        masked = detector.mask_pii(data)

        assert "user@example.com" not in str(masked)
        assert "555-123-4567" not in str(masked)

    def test_no_pii_detected(self):
        """Test when no PII is present."""
        detector = PIIDetector()
        data = "This is a normal message with no sensitive data"
        detections = detector.detect_pii(data)

        assert len(detections) == 0


class TestDataResidencyValidator:
    """Tests for data residency validation."""

    def test_validate_allowed_region(self):
        """Test validation of allowed region."""
        validator = DataResidencyValidator(allowed_regions={"US", "EU"})
        assert validator.validate_residency("US") is True
        assert validator.validate_residency("EU") is True

    def test_validate_disallowed_region(self):
        """Test validation of disallowed region."""
        validator = DataResidencyValidator(allowed_regions={"US", "EU"})
        assert validator.validate_residency("APAC") is False
        assert validator.validate_residency("CN") is False

    def test_case_insensitive_validation(self):
        """Test case-insensitive region validation."""
        validator = DataResidencyValidator(allowed_regions={"US", "EU"})
        assert validator.validate_residency("us") is True
        assert validator.validate_residency("Eu") is True

    def test_extract_residency_from_headers(self):
        """Test extracting residency from request headers."""
        validator = DataResidencyValidator()
        headers = {"X-Data-Residency": "US"}
        region = validator.get_residency_from_request(headers)

        assert region == "US"

    def test_extract_residency_fallback_header(self):
        """Test fallback header for residency."""
        validator = DataResidencyValidator()
        headers = {"X-Data-Region": "EU"}
        region = validator.get_residency_from_request(headers)

        assert region == "EU"

    def test_no_residency_header(self):
        """Test when no residency header present."""
        validator = DataResidencyValidator()
        headers = {}
        region = validator.get_residency_from_request(headers)

        assert region is None


class TestComplianceEnforcer:
    """Tests for compliance enforcement."""

    def test_check_request_with_pii(self):
        """Test compliance check detects PII in request."""
        enforcer = ComplianceEnforcer()
        request_body = {"email": "user@example.com", "data": "test"}
        headers = {}

        compliant, violations = enforcer.check_request_compliance(
            request_body, headers, "req-123", user_id="user1"
        )

        assert not compliant
        assert len(violations) > 0
        assert any(v.violation_type == "PII_DETECTED" for v in violations)

    def test_check_request_residency_violation(self):
        """Test compliance check detects residency violation."""
        enforcer = ComplianceEnforcer(
            residency_validator=DataResidencyValidator(allowed_regions={"US"})
        )
        request_body = {"data": "test"}
        headers = {"X-Data-Residency": "CN"}

        compliant, violations = enforcer.check_request_compliance(
            request_body, headers, "req-123", user_id="user1"
        )

        assert not compliant
        assert any(v.violation_type == "RESIDENCY_VIOLATION" for v in violations)

    def test_check_request_compliant(self):
        """Test compliant request passes check."""
        enforcer = ComplianceEnforcer()
        request_body = {"data": "test", "value": 123}
        headers = {}

        compliant, violations = enforcer.check_request_compliance(
            request_body, headers, "req-123", user_id="user1"
        )

        assert compliant
        assert len(violations) == 0

    def test_mask_response_pii(self):
        """Test PII masking in response."""
        enforcer = ComplianceEnforcer()
        response_body = {"email": "user@example.com", "name": "John"}
        masked = enforcer.mask_response_pii(response_body)

        assert "user@example.com" not in str(masked)
        assert "*" in str(masked)

    def test_audit_log_generation(self):
        """Test audit log generation."""
        enforcer = ComplianceEnforcer()
        request_body = {"email": "user@example.com"}
        headers = {}

        enforcer.check_request_compliance(request_body, headers, "req-123", user_id="user1")
        audit_log = enforcer.get_audit_log()

        assert len(audit_log) > 0
        assert audit_log[0]["request_id"] == "req-123"
        assert audit_log[0]["user_id"] == "user1"

    def test_clear_violations(self):
        """Test clearing violation history."""
        enforcer = ComplianceEnforcer()
        request_body = {"email": "user@example.com"}
        headers = {}

        enforcer.check_request_compliance(request_body, headers, "req-123")
        assert len(enforcer.get_audit_log()) > 0

        enforcer.clear_violations()
        assert len(enforcer.get_audit_log()) == 0


class TestComplianceMiddleware:
    """Tests for compliance middleware integration."""

    def test_middleware_deny_behavior(self):
        """Test middleware denies non-compliant requests."""
        from apgi_framework.compliance.enforcement_middleware import compliance_middleware

        request_body = {"email": "user@example.com"}
        headers = {}

        compliant, violations = compliance_middleware(request_body, headers, "req-123")

        assert not compliant
        assert len(violations) > 0

    def test_middleware_allow_behavior(self):
        """Test middleware allows compliant requests."""
        from apgi_framework.compliance.enforcement_middleware import compliance_middleware

        request_body = {"data": "test"}
        headers = {}

        compliant, violations = compliance_middleware(request_body, headers, "req-123")

        assert compliant
        assert len(violations) == 0
