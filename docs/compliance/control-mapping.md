# Regulatory Control Mapping

This document maps GDPR and HIPAA requirements to specific code implementations in the APGI System. Regulators and auditors can trace compliance requirements to the exact code that implements them.

## Overview

| Regulation | Requirement Category | Implementation Location | Status |
| :--- | :--- | :--- | :--- |
| GDPR Article 5(1)(a) | Lawful processing | `api/compliance/consent_validation.py` | Enforced |
| GDPR Article 5(1)(b) | Purpose limitation | `api/middleware/compliance.py:36-39` | Enforced |
| GDPR Article 5(1)(c) | Data minimization | `api/compliance/data_minimization.py` | Enforced |
| GDPR Article 5(1)(d) | Accuracy | `api/compliance/consent_validation.py:284-331` | Implemented |
| GDPR Article 5(1)(e) | Storage limitation | `api/compliance/data_minimization.py:34-44` | Enforced |
| GDPR Article 6 | Lawful basis | `api/middleware/compliance.py:42-46` | Enforced |
| GDPR Article 7 | Consent conditions | `api/compliance/consent_validation.py` | Enforced |
| GDPR Article 15 | Right of access | `api/routes/compliance_routes.py` | Implemented |
| GDPR Article 17 | Right to erasure | `api/compliance/consent_validation.py:240-282` | Implemented |
| HIPAA 164.312 | Access control | `api/middleware/authentication.py` | Enforced |
| HIPAA 164.308 | Audit controls | `api/audit/logger.py` | Enforced |
| HIPAA 164.310 | Data integrity | `api/middleware/schema_validation.py` | Enforced |

---

## GDPR Compliance Mapping

### Article 5(1)(a) - Lawful, Fair, and Transparent Processing

**Requirement**: Personal data must be processed lawfully, fairly, and in a transparent manner.

**Implementation**:

- **Code**: `api/compliance/consent_validation.py:79-160`
- **Function**: `ConsentValidator.record_consent()`
- **Behavior**: Records consent with verification method and timestamp

```python
# Evidence: Consent is recorded with verification
def record_consent(self, subject_id: str, purposes: List[str], ...):
    consent = ConsentRecord(
        consent_id=consent_id,
        status=ConsentStatus.ACTIVE,
        granted_at=now,
        verification_method=verification_method,
        verified_at=verified_at,
    )
```

**Audit Trail**: `apgi_framework/compliance/compliance_framework.py`

---

### Article 5(1)(b) - Purpose Limitation

**Requirement**: Data collected for specified, explicit, and legitimate purposes.

**Implementation**:

- **Code**: `api/middleware/compliance.py:36-39`
- **List**: `SENSITIVE_ENDPOINT_PATTERNS`
- **Behavior**: Only processes data for defined sensitive endpoints

```python
# Evidence: Explicit endpoint patterns
SENSITIVE_ENDPOINT_PATTERNS = [
    "/v1/sensitive/",
    "/v1/sessions/",
    "/v1/export/",
    "/v1/admin/users/",
]
```

---

### Article 5(1)(c) - Data Minimization

**Requirement**: Data must be adequate, relevant, and limited to what is necessary.

**Implementation**:

- **Code**: `api/compliance/data_minimization.py:57-121`
- **Function**: `DataMinimizationManager.apply_minimization()`
- **Behavior**: Applies masking, suppression, anonymization based on purpose

```python
# Evidence: Minimization levels
class MinimizationLevel(str, Enum):
    NONE = "none"
    MASKING = "masking"
    SUPPRESSION = "suppression"
    ANONYMIZATION = "anonymization"
    PSEUDONYMIZATION = "pseudonymization"
```

---

### Article 5(1)(e) - Storage Limitation

**Requirement**: Kept no longer than necessary for the purposes.

**Implementation**:

- **Code**: `api/middleware/compliance.py:48-68`
- **Class**: `RetentionPolicy`
- **Behavior**: Automatic enforcement with purge candidates

```python
# Evidence: Retention policies
DEFAULT_RETENTION_POLICIES = [
    RetentionPolicy(
        data_type="session_data",
        retention_days=2555,  # 7 years for research
        purpose="consciousness_research",
        legal_basis="consent",
    ),
]
```

**Automated Enforcement**:

- **Code**: `api/compliance/data_minimization.py:310-329`
- **Function**: `get_purge_candidates()`
- **CI Test**: `tests/test_retention_policy.py`

---

### Article 6 - Lawfulness of Processing

**Requirement**: Processing is lawful only if at least one basis applies.

**Implementation**:

- **Code**: `api/middleware/compliance.py:96-141`
- **Function**: `_validate_consent()`
- **Behavior**: Validates consent before processing sensitive data

```python
# Evidence: Consent validation
def _validate_consent(self, request: Request) -> None:
    validation_result = self.consent_validator.validate_consent(
        subject_id=subject_id,
        required_purposes=[p.value for p in SENSITIVE_REQUIRED_PURPOSES],
    )
    if not validation_result.is_valid:
        raise HTTPException(status_code=403, ...)
```

---

### Article 7 - Conditions for Consent

**Requirement**: Consent must be freely given, specific, informed, and unambiguous.

**Implementation**:

- **Code**: `api/compliance/consent_validation.py:161-238`
- **Function**: `validate_consent()`
- **Behavior**: Validates purposes, expiry, verification

```python
# Evidence: Consent validation checks
for consent in active_consents:
    # Check expiry
    if consent.expires_at and consent.expires_at < now:
        consent.status = ConsentStatus.EXPIRED
    
    # Check purposes
    granted_purposes.update(consent.purposes)
    missing_purposes -= consent.purposes
```

---

### Article 17 - Right to Erasure ("Right to be Forgotten")

**Requirement**: Data subject has right to erasure of personal data.

**Implementation**:

- **Code**: `api/compliance/consent_validation.py:240-282`
- **Function**: `revoke_consent()`
- **Behavior**: Revokes consent and marks data for deletion

```python
# Evidence: Revocation
def revoke_consent(self, subject_id: str, revoked_by: str, ...):
    for consent_id in consent_ids:
        consent = self._consent_records.get(consent_id)
        if consent and consent.status == ConsentStatus.ACTIVE:
            consent.status = ConsentStatus.REVOKED
            consent.revoked_at = now
```

---

## HIPAA Compliance Mapping

### 164.312(a)(1) - Access Control

**Requirement**: Implement technical policies to allow access only to authorized persons.

**Implementation**:

- **Code**: `api/middleware/authentication.py`
- **Mechanism**: JWT token validation with RS256
- **Middleware**: `AuthenticationMiddleware`

```python
# Evidence: Token validation
token_payload = verify_token(token.credentials)
request.state.user = token_payload
```

---

### 164.312(a)(2)(i) - Unique User Identification

**Requirement**: Assign unique name/number for identifying user identity.

**Implementation**:

- **Code**: `api/middleware/authentication.py:68-72`
- **Class**: `TokenPayload`
- **Field**: `user_id` (UUID)

```python
@dataclass
class TokenPayload:
    user_id: str  # Unique UUID
    username: str
    roles: List[str]
```

---

### 164.308(a)(1)(ii)(D) - Information Access Management

**Requirement**: Implement policies for authorizing access.

**Implementation**:

- **Code**: `api/services/authorization.py`
- **Function**: `require_role()` decorator
- **Behavior**: Role-based access control

---

### 164.308(a)(5)(ii)(B) - Audit Controls

**Requirement**: Implement hardware, software, and/or procedural mechanisms to record and examine access.

**Implementation**:

- **Code**: `api/audit/logger.py`
- **Function**: `AuditLogger.log_access()`
- **Storage**: Immutable audit trail with tamper detection

```python
# Evidence: Audit logging
self.compliance_framework._log_audit(
    user_id=user_id,
    action="access_sensitive_endpoint",
    resource_id=request.url.path,
    classification=DataClassification.CONFIDENTIAL,
)
```

---

### 164.312(c)(1) - Integrity Controls

**Requirement**: Implement mechanisms to authenticate ePHI.

**Implementation**:

- **Code**: `api/middleware/schema_validation.py`
- **Function**: `ResponseSchemaValidationMiddleware`
- **Behavior**: Validates data integrity before response

---

### 164.312(d) - Person or Entity Authentication

**Requirement**: Implement procedures to verify identity.

**Implementation**:

- **Code**: `api/middleware/authentication.py:137-140`
- **Function**: `verify_token()`
- **Mechanism**: RS256 signature verification

```python
# Evidence: JWT verification
payload = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],
    audience="apgi-api",
)
```

---

## Testing and Verification

### Automated Compliance Tests

| Test File | Coverage | CI Status |
| :--- | :--- | :--- |
| `tests/test_consent_validation.py` | GDPR Art. 7 | Enforced |
| `tests/test_data_minimization.py` | GDPR Art. 5(1)(c) | Enforced |
| `tests/test_retention_policy.py` | GDPR Art. 5(1)(e) | Enforced |
| `tests/test_access_control.py` | HIPAA 164.312 | Enforced |
| `tests/test_audit_logging.py` | HIPAA 164.308 | Enforced |

### Compliance Gates in CI/CD

```yaml
# .github/workflows/ci-cd.yml
- name: Run compliance tests
  run: |
    pytest tests/test_consent_validation.py -v
    pytest tests/test_retention_policy.py -v
    pytest tests/test_access_control.py -v
```

---

## Regulatory Contact

For regulatory inquiries regarding this control mapping:

- **Compliance Officer**: <compliance@apgi-research.org>
- **Data Protection Officer**: <dpo@apgi-research.org>
- **Security Officer**: <security@apgi-research.org>

---

## Document History

| Version | Date | Author | Changes |
| :--- | :--- | :--- | :--- |
| 1.0 | 2026-04-24 | APGI Team | Initial control mapping |
