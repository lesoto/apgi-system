"""
Enhanced Consent Validation System

Provides comprehensive consent validation including:
- Consent record verification
- Expiry checking
- Purpose validation
- Granular consent management
- Consent withdrawal tracking
- Audit trail for consent changes
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class ConsentStatus(Enum):
    """Status of a consent record."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_VERIFICATION = "pending_verification"
    SUPERSEDED = "superseded"


class ConsentPurpose(Enum):
    """Standard consent purposes."""

    DATA_COLLECTION = "data_collection"
    RESEARCH = "research"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"
    PROCESSING = "processing"


@dataclass
class ConsentValidationResult:
    """Result of consent validation."""

    is_valid: bool
    subject_id: str
    status: ConsentStatus
    granted_purposes: List[str]
    missing_purposes: List[str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsentRecord:
    """Enhanced consent record with validation support."""

    consent_id: str
    subject_id: str
    status: ConsentStatus
    granted_at: datetime
    expires_at: Optional[datetime]
    purposes: Set[str]
    data_types: Set[str]
    version: str = "1.0"
    verification_method: Optional[str] = None
    verified_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
    superseded_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConsentValidator:
    """
    Enhanced consent validation with comprehensive checks.
    """

    def __init__(self):
        self._consent_records: Dict[str, ConsentRecord] = {}
        self._subject_consents: Dict[str, Set[str]] = {}  # subject_id -> set of consent_ids

    def _generate_consent_id(self, subject_id: str, timestamp: datetime) -> str:
        """Generate unique consent ID."""
        content = f"{subject_id}_{timestamp.isoformat()}_{__import__('secrets').token_hex(8)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def record_consent(
        self,
        subject_id: str,
        purposes: List[str],
        data_types: List[str],
        expiry_days: Optional[int] = None,
        verification_method: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> ConsentRecord:
        """
        Record new consent with validation.

        Args:
            subject_id: Data subject identifier
            purposes: List of purposes consented to
            data_types: List of data types consented for
            expiry_days: Optional expiry in days from now
            verification_method: How consent was verified (email, signature, etc.)
            metadata: Additional metadata

        Returns:
            Created ConsentRecord
        """
        now = datetime.utcnow()
        consent_id = self._generate_consent_id(subject_id, now)

        expires_at = None
        if expiry_days:
            expires_at = now + __import__("datetime").timedelta(days=expiry_days)

        verified_at = now if verification_method else None

        # Check if subject has existing active consent
        existing_active = self._get_active_consent_for_subject(subject_id)
        if existing_active:
            # Mark existing as superseded
            existing_active.status = ConsentStatus.SUPERSEDED
            existing_active.superseded_by = consent_id
            existing_active.metadata["superseded_at"] = now.isoformat()

        consent = ConsentRecord(
            consent_id=consent_id,
            subject_id=subject_id,
            status=ConsentStatus.ACTIVE,
            granted_at=now,
            expires_at=expires_at,
            purposes=set(purposes),
            data_types=set(data_types),
            version="1.0",
            verification_method=verification_method,
            verified_at=verified_at,
            metadata=metadata or {},
        )

        self._consent_records[consent_id] = consent

        # Track by subject
        if subject_id not in self._subject_consents:
            self._subject_consents[subject_id] = set()
        self._subject_consents[subject_id].add(consent_id)

        logger.info(
            f"Recorded consent {consent_id} for subject {subject_id} "
            f"(purposes: {len(purposes)}, data_types: {len(data_types)})"
        )

        return consent

    def validate_consent(
        self,
        subject_id: str,
        required_purposes: List[str],
        data_type: Optional[str] = None,
    ) -> ConsentValidationResult:
        """
        Validate consent for specific purposes and data type.

        Args:
            subject_id: Data subject to check
            required_purposes: Purposes that must be consented
            data_type: Optional specific data type to check

        Returns:
            ConsentValidationResult with detailed validation info
        """
        errors = []
        warnings = []
        granted_purposes = set()
        missing_purposes = set(required_purposes)

        # Get all active consents for subject
        active_consents = self._get_all_active_consents(subject_id)

        if not active_consents:
            return ConsentValidationResult(
                is_valid=False,
                subject_id=subject_id,
                status=ConsentStatus.REVOKED,  # No consent = revoked
                granted_purposes=[],
                missing_purposes=list(required_purposes),
                errors=["No active consent found for subject"],
                warnings=[],
            )

        # Check each active consent
        now = datetime.utcnow()
        for consent in active_consents:
            # Check expiry
            if consent.expires_at and consent.expires_at < now:
                consent.status = ConsentStatus.EXPIRED
                errors.append(f"Consent {consent.consent_id} has expired")
                continue

            # Check verification
            if consent.verification_method and not consent.verified_at:
                warnings.append(f"Consent {consent.consent_id} pending verification")

            # Check purposes
            granted_purposes.update(consent.purposes)
            missing_purposes -= consent.purposes

            # Check data type if specified
            if data_type and data_type not in consent.data_types:
                warnings.append(
                    f"Data type '{data_type}' not covered by consent {consent.consent_id}"
                )

        # Determine overall validity
        is_valid = len(errors) == 0 and missing_purposes == set() and len(granted_purposes) > 0

        # Determine effective status
        status = ConsentStatus.ACTIVE if is_valid else ConsentStatus.EXPIRED

        return ConsentValidationResult(
            is_valid=is_valid,
            subject_id=subject_id,
            status=status,
            granted_purposes=sorted(list(granted_purposes)),
            missing_purposes=sorted(list(missing_purposes)),
            errors=errors,
            warnings=warnings,
            metadata={
                "active_consent_count": len(active_consents),
                "checked_at": now.isoformat(),
            },
        )

    def revoke_consent(
        self,
        subject_id: str,
        revoked_by: str,
        reason: Optional[str] = None,
        specific_consent_id: Optional[str] = None,
    ) -> List[str]:
        """
        Revoke consent for a subject.

        Args:
            subject_id: Data subject
            revoked_by: Who is performing the revocation
            reason: Optional reason for revocation
            specific_consent_id: Optional specific consent to revoke (revokes all if None)

        Returns:
            List of revoked consent IDs
        """
        revoked = []
        now = datetime.utcnow()

        consent_ids = self._subject_consents.get(subject_id, set())

        for consent_id in consent_ids:
            if specific_consent_id and consent_id != specific_consent_id:
                continue

            consent = self._consent_records.get(consent_id)
            if consent and consent.status == ConsentStatus.ACTIVE:
                consent.status = ConsentStatus.REVOKED
                consent.revoked_at = now
                consent.revoked_by = revoked_by
                consent.revocation_reason = reason or "User requested"
                revoked.append(consent_id)

        if revoked:
            logger.info(
                f"Revoked {len(revoked)} consent(s) for subject {subject_id} "
                f"by {revoked_by}: {reason}"
            )

        return revoked

    def update_consent_purposes(
        self,
        consent_id: str,
        new_purposes: List[str],
        updated_by: str,
    ) -> Optional[ConsentRecord]:
        """
        Update purposes for an existing consent (creates new version).

        Args:
            consent_id: Consent to update
            new_purposes: New list of purposes
            updated_by: Who is making the update

        Returns:
            New ConsentRecord if successful, None if original not found
        """
        original = self._consent_records.get(consent_id)
        if not original:
            return None

        # Create new consent with updated purposes
        new_consent = self.record_consent(
            subject_id=original.subject_id,
            purposes=new_purposes,
            data_types=list(original.data_types),
            expiry_days=(
                None
                if not original.expires_at
                else (original.expires_at - original.granted_at).days
            ),
            verification_method=original.verification_method,
            metadata={
                **original.metadata,
                "previous_consent_id": consent_id,
                "updated_by": updated_by,
                "updated_at": datetime.utcnow().isoformat(),
                "original_purposes": list(original.purposes),
            },
        )

        # Mark original as superseded
        original.status = ConsentStatus.SUPERSEDED
        original.superseded_by = new_consent.consent_id

        logger.info(f"Updated consent {consent_id} -> {new_consent.consent_id} " f"by {updated_by}")

        return new_consent

    def get_consent_history(self, subject_id: str) -> List[Dict]:
        """
        Get full consent history for a subject.

        Args:
            subject_id: Data subject

        Returns:
            List of consent records as dicts
        """
        consent_ids = self._subject_consents.get(subject_id, set())
        history = []

        for consent_id in sorted(consent_ids, key=lambda x: self._consent_records[x].granted_at):
            consent = self._consent_records[consent_id]
            history.append(
                {
                    "consent_id": consent.consent_id,
                    "status": consent.status.value,
                    "granted_at": consent.granted_at.isoformat(),
                    "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                    "purposes": sorted(list(consent.purposes)),
                    "data_types": sorted(list(consent.data_types)),
                    "version": consent.version,
                    "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
                    "revocation_reason": consent.revocation_reason,
                }
            )

        return history

    def _get_active_consent_for_subject(self, subject_id: str) -> Optional[ConsentRecord]:
        """Get the most recent active consent for a subject."""
        consent_ids = self._subject_consents.get(subject_id, set())
        now = datetime.utcnow()

        active = None
        for consent_id in consent_ids:
            consent = self._consent_records.get(consent_id)
            if consent and consent.status == ConsentStatus.ACTIVE:
                if not consent.expires_at or consent.expires_at > now:
                    if not active or consent.granted_at > active.granted_at:
                        active = consent

        return active

    def _get_all_active_consents(self, subject_id: str) -> List[ConsentRecord]:
        """Get all active (non-expired) consents for a subject."""
        consent_ids = self._subject_consents.get(subject_id, set())
        now = datetime.utcnow()

        active = []
        for consent_id in consent_ids:
            consent = self._consent_records.get(consent_id)
            if consent and consent.status == ConsentStatus.ACTIVE:
                if not consent.expires_at or consent.expires_at > now:
                    active.append(consent)

        return sorted(active, key=lambda x: x.granted_at, reverse=True)


# Global validator instance
_validator: Optional[ConsentValidator] = None


def get_consent_validator() -> ConsentValidator:
    """Get or create global consent validator instance."""
    global _validator
    if _validator is None:
        _validator = ConsentValidator()
    return _validator
