"""
Privacy by Design Assessments

Implementation of privacy impact assessments (PIA) and privacy by design
principles for GDPR compliance and data protection best practices.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class PrivacyRisk(str, Enum):
    """Privacy risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PrivacyPrinciple(str, Enum):
    """Privacy by design principles (GDPR Article 25)."""

    LAWFULNESS = "lawfulness"
    PURPOSE_LIMITATION = "purpose_limitation"
    DATA_MINIMIZATION = "data_minimization"
    ACCURACY = "accuracy"
    STORAGE_LIMITATION = "storage_limitation"
    INTEGRITY_CONFIDENTIALITY = "integrity_confidentiality"
    ACCOUNTABILITY = "accountability"


@dataclass
class PrivacyImpact:
    """Individual privacy impact finding."""

    principle: PrivacyPrinciple
    risk_level: PrivacyRisk
    description: str
    mitigation: Optional[str] = None
    status: str = "open"  # open, mitigated, accepted


@dataclass
class PrivacyAssessment:
    """Privacy Impact Assessment (PIA) for a system or feature."""

    assessment_id: str
    system_name: str
    description: str
    data_types: Set[str] = field(default_factory=set)
    data_subjects: Set[str] = field(default_factory=set)
    purposes: Set[str] = field(default_factory=set)
    impacts: List[PrivacyImpact] = field(default_factory=list)
    assessor: str = ""
    assessment_date: datetime = field(default_factory=datetime.now)
    review_date: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, approved, rejected
    overall_risk: PrivacyRisk = PrivacyRisk.LOW


class PrivacyByDesignManager:
    """
    Manager for privacy by design assessments and compliance.
    """

    def __init__(self):
        self.assessments: Dict[str, PrivacyAssessment] = {}
        self._initialize_framework_assessments()

    def _initialize_framework_assessments(self) -> None:
        """Initialize privacy assessments for core framework components."""
        # Assessment for Session Management
        session_pia = PrivacyAssessment(
            assessment_id="PIA-001",
            system_name="Session Management System",
            description="User session creation, storage, and management",
            data_types={"user_id", "session_config", "timestamp", "ip_address"},
            data_subjects={"researchers", "clinicians"},
            purposes={"simulation_management", "user_authentication"},
        )
        session_pia.impacts = [
            PrivacyImpact(
                principle=PrivacyPrinciple.DATA_MINIMIZATION,
                risk_level=PrivacyRisk.LOW,
                description="Session data includes only necessary configuration",
                mitigation="Session data purged after retention period",
                status="mitigated",
            ),
            PrivacyImpact(
                principle=PrivacyPrinciple.STORAGE_LIMITATION,
                risk_level=PrivacyRisk.MEDIUM,
                description="Session data retention needs clear policy",
                mitigation="Implement automated session cleanup after 90 days",
                status="open",
            ),
        ]
        session_pia.overall_risk = PrivacyRisk.MEDIUM
        self.assessments["PIA-001"] = session_pia

        # Assessment for Clinical Data Storage
        clinical_pia = PrivacyAssessment(
            assessment_id="PIA-002",
            system_name="Clinical Data Storage",
            description="Storage and processing of clinical/health data",
            data_types={"patient_id", "health_metrics", "diagnosis", "treatment_data"},
            data_subjects={"patients", "healthcare_providers"},
            purposes={"research", "clinical_analysis", "treatment"},
        )
        clinical_pia.impacts = [
            PrivacyImpact(
                principle=PrivacyPrinciple.LAWFULNESS,
                risk_level=PrivacyRisk.HIGH,
                description="Requires explicit consent for health data processing",
                mitigation="Implement consent management system",
                status="open",
            ),
            PrivacyImpact(
                principle=PrivacyPrinciple.INTEGRITY_CONFIDENTIALITY,
                risk_level=PrivacyRisk.CRITICAL,
                description="Health data requires highest protection",
                mitigation="AES-256 encryption at rest and in transit, access controls",
                status="mitigated",
            ),
            PrivacyImpact(
                principle=PrivacyPrinciple.ACCOUNTABILITY,
                risk_level=PrivacyRisk.HIGH,
                description="Full audit trail required for health data access",
                mitigation="Comprehensive audit logging implemented",
                status="mitigated",
            ),
        ]
        clinical_pia.overall_risk = PrivacyRisk.HIGH
        self.assessments["PIA-002"] = clinical_pia

    def create_assessment(
        self,
        system_name: str,
        description: str,
        data_types: Set[str],
        data_subjects: Set[str],
        purposes: Set[str],
        assessor: str,
    ) -> PrivacyAssessment:
        """
        Create a new privacy impact assessment.

        Args:
            system_name: Name of system/feature being assessed
            description: Description of the system
            data_types: Types of data processed
            data_subjects: Categories of data subjects
            purposes: Purposes for data processing
            assessor: Person conducting assessment

        Returns:
            Created PrivacyAssessment
        """
        assessment_id = f"PIA-{len(self.assessments) + 1:03d}"
        assessment = PrivacyAssessment(
            assessment_id=assessment_id,
            system_name=system_name,
            description=description,
            data_types=data_types,
            data_subjects=data_subjects,
            purposes=purposes,
            assessor=assessor,
        )

        # Auto-assess privacy principles
        self._auto_assess_principles(assessment)

        self.assessments[assessment_id] = assessment
        logger.info(f"Created privacy assessment: {assessment_id} for {system_name}")
        return assessment

    def _auto_assess_principles(self, assessment: PrivacyAssessment) -> None:
        """
        Automatically assess privacy principles based on data types and purposes.

        Args:
            assessment: Assessment to populate with auto-assessed impacts
        """
        # Data Minimization Assessment
        if len(assessment.data_types) > 10:
            assessment.impacts.append(
                PrivacyImpact(
                    principle=PrivacyPrinciple.DATA_MINIMIZATION,
                    risk_level=PrivacyRisk.MEDIUM,
                    description="Large number of data types may indicate unnecessary collection",
                    mitigation="Review data types and remove non-essential ones",
                )
            )
        else:
            assessment.impacts.append(
                PrivacyImpact(
                    principle=PrivacyPrinciple.DATA_MINIMIZATION,
                    risk_level=PrivacyRisk.LOW,
                    description="Data types appear minimal and necessary",
                    status="accepted",
                )
            )

        # Purpose Limitation Assessment
        if len(assessment.purposes) > 5:
            assessment.impacts.append(
                PrivacyImpact(
                    principle=PrivacyPrinciple.PURPOSE_LIMITATION,
                    risk_level=PrivacyRisk.MEDIUM,
                    description="Multiple purposes may indicate function creep",
                    mitigation="Ensure each purpose is necessary and documented",
                )
            )
        else:
            assessment.impacts.append(
                PrivacyImpact(
                    principle=PrivacyPrinciple.PURPOSE_LIMITATION,
                    risk_level=PrivacyRisk.LOW,
                    description="Purposes are limited and well-defined",
                    status="accepted",
                )
            )

        # Integrity and Confidentiality Assessment
        if (
            "health" in " ".join(assessment.data_types).lower()
            or "patient" in " ".join(assessment.data_types).lower()
        ):
            assessment.impacts.append(
                PrivacyImpact(
                    principle=PrivacyPrinciple.INTEGRITY_CONFIDENTIALITY,
                    risk_level=PrivacyRisk.HIGH,
                    description="Health/patient data requires enhanced protection",
                    mitigation="Implement encryption, access controls, audit logging",
                )
            )

        # Calculate overall risk
        if assessment.impacts:
            max_risk = max(imp.risk_level for imp in assessment.impacts)
            assessment.overall_risk = max_risk

    def get_assessment(self, assessment_id: str) -> Optional[PrivacyAssessment]:
        """
        Get a privacy assessment by ID.

        Args:
            assessment_id: Assessment identifier

        Returns:
            PrivacyAssessment if found, None otherwise
        """
        return self.assessments.get(assessment_id)

    def approve_assessment(self, assessment_id: str, reviewer: str) -> bool:
        """
        Approve a privacy assessment.

        Args:
            assessment_id: Assessment identifier
            reviewer: Person approving the assessment

        Returns:
            True if approved, False otherwise
        """
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"Assessment not found: {assessment_id}")
            return False

        # Check if all high/critical risks are mitigated
        unmitigated_high_risks = [
            imp
            for imp in assessment.impacts
            if imp.risk_level in [PrivacyRisk.HIGH, PrivacyRisk.CRITICAL]
            and imp.status != "mitigated"
        ]

        if unmitigated_high_risks:
            logger.warning(
                f"Cannot approve assessment {assessment_id}: "
                f"{len(unmitigated_high_risks)} unmitigated high/critical risks"
            )
            return False

        assessment.status = "approved"
        assessment.review_date = datetime.now()
        logger.info(f"Privacy assessment {assessment_id} approved by {reviewer}")
        return True

    def add_mitigation(
        self, assessment_id: str, principle: PrivacyPrinciple, mitigation: str
    ) -> bool:
        """
        Add mitigation for a privacy impact.

        Args:
            assessment_id: Assessment identifier
            principle: Privacy principle being mitigated
            mitigation: Mitigation description

        Returns:
            True if added, False otherwise
        """
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            return False

        for impact in assessment.impacts:
            if impact.principle == principle:
                impact.mitigation = mitigation
                impact.status = "mitigated"
                logger.info(f"Added mitigation for {principle} in {assessment_id}")
                return True

        return False

    def get_pending_mitigations(self, assessment_id: str) -> List[PrivacyImpact]:
        """
        Get pending mitigations for an assessment.

        Args:
            assessment_id: Assessment identifier

        Returns:
            List of impacts requiring mitigation
        """
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            return []

        return [
            imp
            for imp in assessment.impacts
            if imp.status == "open" and imp.risk_level in [PrivacyRisk.HIGH, PrivacyRisk.CRITICAL]
        ]


# Global instance
privacy_manager = PrivacyByDesignManager()


def check_privacy_compliance(
    system_name: str, data_types: Set[str], purposes: Set[str]
) -> tuple[bool, List[str]]:
    """
    Quick privacy compliance check for a system.

    Args:
        system_name: Name of system
        data_types: Types of data processed
        purposes: Purposes for processing

    Returns:
        Tuple of (compliant: bool, issues: List[str])
    """
    issues = []

    # Check for health/patient data without proper purposes
    has_health_data = any("health" in dt.lower() or "patient" in dt.lower() for dt in data_types)
    if has_health_data and "research" not in purposes and "clinical" not in purposes:
        issues.append("Health/patient data detected but no clinical/research purpose specified")

    # Check for PII without consent purpose
    has_pii = any(
        "name" in dt.lower() or "email" in dt.lower() or "address" in dt.lower()
        for dt in data_types
    )
    if has_pii and "consent" not in purposes:
        issues.append("PII data detected but no consent management purpose specified")

    # Check data minimization
    if len(data_types) > 15:
        issues.append("Large number of data types may violate data minimization principle")

    return len(issues) == 0, issues
