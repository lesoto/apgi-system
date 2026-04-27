"""
Data Residency Controls

Implementation of data residency controls for cross-border data transfer compliance
including GDPR, HIPAA, and regional data protection requirements.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class Region(str, Enum):
    """Supported data residency regions."""

    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_WEST = "eu-west"
    EU_CENTRAL = "eu-central"
    ASIA_PACIFIC = "asia-pacific"
    CANADA = "canada"
    AUSTRALIA = "australia"


class DataClassification(str, Enum):
    """Data classification levels for residency controls."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PHI = "phi"  # Protected Health Information
    PII = "pii"  # Personally Identifiable Information


@dataclass
class ResidencyPolicy:
    """Data residency policy configuration."""

    region: Region
    allowed_regions: Set[Region]
    data_classification: DataClassification
    encryption_required: bool = True
    audit_required: bool = True
    retention_period_days: Optional[int] = None
    cross_border_allowed: bool = False


class DataResidencyManager:
    """
    Manager for data residency controls and cross-border transfer compliance.
    """

    def __init__(self) -> None:
        self.policies: Dict[str, ResidencyPolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default data residency policies by region."""
        # EU: GDPR compliance - strict controls
        self.policies["eu-west"] = ResidencyPolicy(
            region=Region.EU_WEST,
            allowed_regions={Region.EU_WEST, Region.EU_CENTRAL},
            data_classification=DataClassification.CONFIDENTIAL,
            encryption_required=True,
            audit_required=True,
            retention_period_days=365,
            cross_border_allowed=False,
        )

        # US: HIPAA/US privacy laws
        self.policies["us-east"] = ResidencyPolicy(
            region=Region.US_EAST,
            allowed_regions={Region.US_EAST, Region.US_WEST, Region.CANADA},
            data_classification=DataClassification.PHI,
            encryption_required=True,
            audit_required=True,
            retention_period_days=730,
            cross_border_allowed=True,
        )

        # Asia-Pacific: Regional compliance
        self.policies["asia-pacific"] = ResidencyPolicy(
            region=Region.ASIA_PACIFIC,
            allowed_regions={Region.ASIA_PACIFIC, Region.AUSTRALIA},
            data_classification=DataClassification.CONFIDENTIAL,
            encryption_required=True,
            audit_required=True,
            retention_period_days=365,
            cross_border_allowed=False,
        )

    def get_policy(self, region: str) -> Optional[ResidencyPolicy]:
        """
        Get residency policy for a region.

        Args:
            region: Region identifier

        Returns:
            ResidencyPolicy if found, None otherwise
        """
        return self.policies.get(region)

    def check_cross_border_transfer(
        self,
        source_region: str,
        destination_region: str,
        data_classification: DataClassification,
    ) -> tuple[bool, str]:
        """
        Check if cross-border data transfer is allowed.

        Args:
            source_region: Source region identifier
            destination_region: Destination region identifier
            data_classification: Classification of data being transferred

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        source_policy = self.get_policy(source_region)
        dest_policy = self.get_policy(destination_region)

        if not source_policy:
            return False, f"No policy found for source region: {source_region}"

        if not dest_policy:
            return False, f"No policy found for destination region: {destination_region}"

        # Check if destination is in allowed regions
        dest_region_enum = Region(destination_region)
        if dest_region_enum not in source_policy.allowed_regions:
            return (
                False,
                f"Destination region {destination_region} not in allowed regions for {source_region}",
            )

        # Check cross-border policy
        if not source_policy.cross_border_allowed:
            return (
                False,
                f"Cross-border transfer not allowed from {source_region} due to policy",
            )

        # Check data classification compatibility
        if data_classification == DataClassification.PHI:
            if destination_region not in [Region.US_EAST, Region.US_WEST, Region.CANADA]:
                return (
                    False,
                    f"PHI data cannot be transferred to {destination_region} (HIPAA compliance)",
                )

        if data_classification == DataClassification.PII:
            if destination_region not in source_policy.allowed_regions:
                return (
                    False,
                    f"PII data cannot be transferred to {destination_region} (GDPR compliance)",
                )

        return True, "Transfer allowed"

    def log_data_transfer(
        self,
        source_region: str,
        destination_region: str,
        data_classification: DataClassification,
        record_count: int,
        user_id: str,
        allowed: bool,
        reason: str,
    ) -> None:
        """
        Log data transfer for audit trail.

        Args:
            source_region: Source region
            destination_region: Destination region
            data_classification: Data classification
            record_count: Number of records transferred
            user_id: User initiating transfer
            allowed: Whether transfer was allowed
            reason: Reason for decision
        """
        logger.info(
            f"Data Transfer Audit: {source_region} -> {destination_region} | "
            f"Classification: {data_classification} | Records: {record_count} | "
            f"User: {user_id} | Allowed: {allowed} | Reason: {reason}"
        )

    def get_retention_period(self, region: str) -> Optional[int]:
        """
        Get data retention period for a region.

        Args:
            region: Region identifier

        Returns:
            Retention period in days, or None if not specified
        """
        policy = self.get_policy(region)
        return policy.retention_period_days if policy else None

    def is_encryption_required(self, region: str) -> bool:
        """
        Check if encryption is required for data in a region.

        Args:
            region: Region identifier

        Returns:
            True if encryption required, False otherwise
        """
        policy = self.get_policy(region)
        return policy.encryption_required if policy else True

    def is_audit_required(self, region: str) -> bool:
        """
        Check if audit logging is required for data in a region.

        Args:
            region: Region identifier

        Returns:
            True if audit required, False otherwise
        """
        policy = self.get_policy(region)
        return policy.audit_required if policy else True


# Global instance
data_residency_manager = DataResidencyManager()


def check_data_residency_compliance(
    user_region: str,
    data_region: str,
    data_classification: DataClassification,
) -> tuple[bool, str]:
    """
    Check if data storage complies with residency requirements.

    Args:
        user_region: User's home region
        data_region: Region where data is stored
        data_classification: Classification of data

    Returns:
        Tuple of (compliant: bool, reason: str)
    """
    # If data is stored in user's region, it's compliant
    if user_region == data_region:
        return True, "Data stored in user's home region"

    # Check cross-border transfer rules
    return data_residency_manager.check_cross_border_transfer(
        source_region=user_region,
        destination_region=data_region,
        data_classification=data_classification,
    )


def get_allowed_storage_regions(
    user_region: str, data_classification: DataClassification
) -> List[str]:
    """
    Get list of allowed storage regions for a user's data.

    Args:
        user_region: User's home region
        data_classification: Data classification

    Returns:
        List of allowed region identifiers
    """
    policy = data_residency_manager.get_policy(user_region)
    if not policy:
        logger.warning(f"No policy found for region: {user_region}")
        return []

    # Filter regions based on data classification
    allowed = []
    for region in policy.allowed_regions:
        region_str = region.value
        # For PHI, only allow US regions
        if data_classification == DataClassification.PHI:
            if region in [Region.US_EAST, Region.US_WEST, Region.CANADA]:
                allowed.append(region_str)
        else:
            allowed.append(region_str)

    return allowed
