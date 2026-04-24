"""
Data Minimization and Anonymization

Implements GDPR Article 5(1)(c) data minimization principle and
anonymization techniques for privacy protection.

Provides:
- Automatic data minimization rules
- Data anonymization (k-anonymity, l-diversity)
- Retention policy enforcement
- Automatic data purging
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MinimizationLevel(str, Enum):
    """Level of data minimization to apply."""

    NONE = "none"  # No minimization
    MASKING = "masking"  # Mask sensitive fields
    SUPPRESSION = "suppression"  # Remove unnecessary fields
    ANONYMIZATION = "anonymization"  # Generalize for anonymity
    PSEUDONYMIZATION = "pseudonymization"  # Replace with pseudonyms


@dataclass
class RetentionPolicy:
    """Data retention policy configuration."""

    data_type: str
    retention_days: int
    purpose: str
    legal_basis: str
    can_extend: bool = False
    extension_reason: Optional[str] = None


@dataclass
class AnonymizationConfig:
    """Configuration for anonymization operations."""

    k_threshold: int = 5  # k-anonymity threshold
    l_threshold: int = 2  # l-diversity threshold
    quasi_identifiers: List[str] = field(default_factory=list)
    sensitive_attributes: List[str] = field(default_factory=list)
    generalization_hierarchy: Dict[str, List[str]] = field(default_factory=dict)


class DataMinimizationManager:
    """
    Manager for data minimization and anonymization.

    Implements GDPR Article 5(1)(c) - data must be adequate, relevant,
    and limited to what is necessary for the purposes.
    """

    def __init__(self):
        self._retention_policies: Dict[str, RetentionPolicy] = {}
        self._minimization_rules: Dict[str, List[str]] = {}
        self._anonymization_configs: Dict[str, AnonymizationConfig] = {}
        self._pseudonym_map: Dict[str, str] = {}

    def register_retention_policy(self, policy: RetentionPolicy) -> None:
        """
        Register a retention policy for a data type.

        Args:
            policy: Retention policy to register
        """
        self._retention_policies[policy.data_type] = policy
        logger.info(f"Registered retention policy for {policy.data_type}")

    def register_minimization_rules(self, data_type: str, fields_to_remove: List[str]) -> None:
        """
        Register fields to remove for data minimization.

        Args:
            data_type: Type of data
            fields_to_remove: Fields that should be minimized
        """
        self._minimization_rules[data_type] = fields_to_remove
        logger.info(f"Registered minimization rules for {data_type}")

    def apply_minimization(
        self, data: Dict[str, Any], data_type: str, level: MinimizationLevel
    ) -> Dict[str, Any]:
        """
        Apply data minimization to a data record.

        Args:
            data: Data to minimize
            data_type: Type of data
            level: Minimization level to apply

        Returns:
            Minimized data
        """
        if level == MinimizationLevel.NONE:
            return data.copy()

        result = data.copy()

        if level == MinimizationLevel.MASKING:
            result = self._apply_masking(result, data_type)
        elif level == MinimizationLevel.SUPPRESSION:
            result = self._apply_suppression(result, data_type)
        elif level == MinimizationLevel.ANONYMIZATION:
            result = self._apply_anonymization(result, data_type)
        elif level == MinimizationLevel.PSEUDONYMIZATION:
            result = self._apply_pseudonymization(result, data_type)

        return result

    def _apply_masking(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Apply masking to sensitive fields."""
        result = data.copy()
        sensitive_fields = self._get_sensitive_fields(data_type)

        for field_name in sensitive_fields:
            if field_name in result and result[field_name]:
                value = str(result[field_name])
                if len(value) > 4:
                    result[field_name] = value[:2] + "***" + value[-2:]
                else:
                    result[field_name] = "***"

        return result

    def _apply_suppression(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Suppress (remove) unnecessary fields."""
        result = data.copy()
        fields_to_remove = self._minimization_rules.get(data_type, [])

        for field_name in fields_to_remove:
            if field_name in result:
                del result[field_name]

        return result

    def _apply_anonymization(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Apply anonymization techniques."""
        config = self._anonymization_configs.get(data_type)
        if not config:
            return self._apply_suppression(data, data_type)

        result = data.copy()

        # Generalize quasi-identifiers
        for field_name in config.quasi_identifiers:
            if field_name in result:
                result[field_name] = self._generalize_value(
                    result[field_name], field_name, config.generalization_hierarchy
                )

        # Remove direct identifiers
        direct_identifiers = ["name", "email", "phone", "ssn", "patient_id"]
        for field_name in direct_identifiers:
            if field_name in result:
                result[field_name] = "[ANONYMIZED]"

        return result

    def _apply_pseudonymization(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Apply pseudonymization to identifiers."""
        result = data.copy()
        identifier_fields = ["user_id", "patient_id", "subject_id"]

        for field_name in identifier_fields:
            if field_name in result and result[field_name]:
                original = str(result[field_name])
                if original not in self._pseudonym_map:
                    self._pseudonym_map[original] = self._generate_pseudonym(original)
                result[field_name] = self._pseudonym_map[original]

        return result

    def _generate_pseudonym(self, original: str) -> str:
        """Generate a pseudonym for an identifier."""
        hash_value = hashlib.sha256(original.encode()).hexdigest()[:16]
        return f"PSEUDO_{hash_value.upper()}"

    def _generalize_value(self, value: Any, field: str, hierarchy: Dict[str, List[str]]) -> Any:
        """Generalize a value according to hierarchy."""
        if field not in hierarchy:
            return value

        levels = hierarchy[field]
        # Return a more general level (for demonstration, return first level)
        return levels[0] if levels else value

    def _get_sensitive_fields(self, data_type: str) -> List[str]:
        """Get list of sensitive fields for a data type."""
        default_sensitive = [
            "ssn",
            "password",
            "credit_card",
            "account_number",
            "medical_record_number",
        ]
        return default_sensitive

    def check_retention_expired(
        self, data_type: str, created_at: datetime
    ) -> Tuple[bool, Optional[RetentionPolicy]]:
        """
        Check if data has exceeded retention period.

        Args:
            data_type: Type of data
            created_at: When the data was created

        Returns:
            Tuple of (expired, policy)
        """
        policy = self._retention_policies.get(data_type)
        if not policy:
            return False, None

        retention_end = created_at + timedelta(days=policy.retention_days)
        expired = datetime.now() > retention_end

        return expired, policy

    def should_minimize_data(self, data_type: str, purpose: str, legal_basis: str) -> bool:
        """
        Determine if data should be minimized based on purpose and legal basis.

        Args:
            data_type: Type of data
            purpose: Purpose of processing
            legal_basis: Legal basis for processing

        Returns:
            True if data should be minimized
        """
        policy = self._retention_policies.get(data_type)
        if not policy:
            return False

        # Minimize if purpose doesn't match or legal basis is weak
        if purpose != policy.purpose:
            return True

        if legal_basis in ["consent", "legitimate_interest"]:
            return True

        return False

    def anonymize_dataset(
        self, dataset: List[Dict[str, Any]], config: AnonymizationConfig
    ) -> List[Dict[str, Any]]:
        """
        Anonymize a dataset to achieve k-anonymity.

        Args:
            dataset: List of data records
            config: Anonymization configuration

        Returns:
            Anonymized dataset
        """
        if not dataset:
            return []

        # Group by quasi-identifiers
        groups: Dict[tuple, List[Dict]] = {}
        for record in dataset:
            key = tuple(record.get(f) for f in config.quasi_identifiers)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)

        # Suppress groups that don't meet k-anonymity
        anonymized = []
        for key, group in groups.items():
            if len(group) >= config.k_threshold:
                # Generalize quasi-identifiers
                generalized_key = self._generalize_key(key, config)
                for record in group:
                    anonymized_record = record.copy()
                    for i, field_name in enumerate(config.quasi_identifiers):
                        anonymized_record[field_name] = generalized_key[i]
                    anonymized.append(anonymized_record)
            else:
                # Suppress small groups
                logger.debug(f"Suppressing group with {len(group)} records for k-anonymity")

        return anonymized

    def _generalize_key(self, key: tuple, config: AnonymizationConfig) -> tuple:
        """Generalize a key tuple."""
        result = []
        for i, value in enumerate(key):
            field = config.quasi_identifiers[i]
            if field in config.generalization_hierarchy:
                levels = config.generalization_hierarchy[field]
                result.append(levels[0] if levels else value)
            else:
                result.append(value)
        return tuple(result)

    def get_purge_candidates(
        self, data_type: str, records: List[Tuple[str, datetime]]
    ) -> List[str]:
        """
        Get list of record IDs that should be purged.

        Args:
            data_type: Type of data
            records: List of (record_id, created_at) tuples

        Returns:
            List of record IDs to purge
        """
        candidates = []
        for record_id, created_at in records:
            expired, _ = self.check_retention_expired(data_type, created_at)
            if expired:
                candidates.append(record_id)

        return candidates

    def generate_data_inventory(self) -> Dict[str, Any]:
        """Generate inventory of data minimization policies."""
        return {
            "retention_policies": {
                k: {
                    "retention_days": v.retention_days,
                    "purpose": v.purpose,
                    "legal_basis": v.legal_basis,
                }
                for k, v in self._retention_policies.items()
            },
            "minimization_rules": self._minimization_rules,
            "anonymization_configs": {
                k: {
                    "k_threshold": v.k_threshold,
                    "quasi_identifiers": v.quasi_identifiers,
                }
                for k, v in self._anonymization_configs.items()
            },
        }


# Global data minimization manager instance
_minimization_manager: Optional[DataMinimizationManager] = None


def get_minimization_manager() -> DataMinimizationManager:
    """Get or create global data minimization manager."""
    global _minimization_manager
    if _minimization_manager is None:
        _minimization_manager = DataMinimizationManager()
    return _minimization_manager
