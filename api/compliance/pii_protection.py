"""
PII Protection Mechanisms

Implementation of Personally Identifiable Information (PII) protection
including identification, classification, masking, and access controls.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PIICategory(str, Enum):
    """Categories of PII data."""

    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    MEDICAL_RECORD = "medical_record"
    BIOMETRIC = "biometric"


class PIISensitivity(str, Enum):
    """Sensitivity levels for PII."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PIIField:
    """PII field definition."""

    field_name: str
    category: PIICategory
    sensitivity: PIISensitivity
    pattern: str
    description: str


class PIIIdentifier:
    """
    Identify and classify PII in data.
    """

    # Common PII patterns
    PATTERNS = {
        PIICategory.EMAIL: {
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "sensitivity": PIISensitivity.MEDIUM,
        },
        PIICategory.PHONE: {
            "pattern": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "sensitivity": PIISensitivity.MEDIUM,
        },
        PIICategory.SSN: {
            "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
            "sensitivity": PIISensitivity.CRITICAL,
        },
        PIICategory.CREDIT_CARD: {
            "pattern": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "sensitivity": PIISensitivity.CRITICAL,
        },
        PIICategory.IP_ADDRESS: {
            "pattern": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "sensitivity": PIISensitivity.LOW,
        },
        PIICategory.DATE_OF_BIRTH: {
            "pattern": r"\b\d{4}[-/]\d{2}[-/]\d{2}\b",
            "sensitivity": PIISensitivity.HIGH,
        },
    }

    def __init__(self):
        self.compiled_patterns = {
            category: re.compile(pattern_data["pattern"])
            for category, pattern_data in self.PATTERNS.items()
        }

    def identify_pii(self, text: str) -> List[PIIField]:
        """
        Identify PII in text.

        Args:
            text: Text to analyze

        Returns:
            List of identified PII fields
        """
        pii_fields = []

        for category, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                pii_fields.append(
                    PIIField(
                        field_name=f"detected_{category.value}",
                        category=category,
                        sensitivity=PIISensitivity(self.PATTERNS[category]["sensitivity"]),
                        pattern=match.group(),
                        description=f"Detected {category.value}",
                    )
                )

        return pii_fields

    def classify_data(self, data: Dict[str, str]) -> Dict[str, PIICategory]:
        """
        Classify data fields as PII categories.

        Args:
            data: Dictionary of field names and values

        Returns:
            Dictionary mapping field names to PII categories
        """
        classification = {}

        for field_name, value in data.items():
            field_lower = field_name.lower()
            value_str = str(value)

            # Check field name for PII indicators
            if "email" in field_lower or "mail" in field_lower:
                classification[field_name] = PIICategory.EMAIL
            elif "phone" in field_lower or "mobile" in field_lower or "tel" in field_lower:
                classification[field_name] = PIICategory.PHONE
            elif "ssn" in field_lower or "social" in field_lower:
                classification[field_name] = PIICategory.SSN
            elif "credit" in field_lower or "card" in field_lower or "cc" in field_lower:
                classification[field_name] = PIICategory.CREDIT_CARD
            elif "address" in field_lower or "street" in field_lower or "city" in field_lower:
                classification[field_name] = PIICategory.ADDRESS
            elif "name" in field_lower or "first" in field_lower or "last" in field_lower:
                classification[field_name] = PIICategory.NAME
            elif "dob" in field_lower or "birth" in field_lower or "birthday" in field_lower:
                classification[field_name] = PIICategory.DATE_OF_BIRTH
            elif "ip" in field_lower:
                classification[field_name] = PIICategory.IP_ADDRESS
            else:
                # Check value for PII patterns
                pii_fields = self.identify_pii(value_str)
                if pii_fields:
                    classification[field_name] = pii_fields[0].category

        return classification


class PIIMasker:
    """
    Mask PII data for logging and display purposes.
    """

    MASKING_STRATEGIES = {
        PIISensitivity.LOW: lambda x: x[:2] + "*" * (len(x) - 4) + x[-2:],
        PIISensitivity.MEDIUM: lambda x: x[:1] + "*" * (len(x) - 2) + x[-1:],
        PIISensitivity.HIGH: lambda x: "*" * len(x),
        PIISensitivity.CRITICAL: lambda x: "[REDACTED]",
    }

    def mask_value(self, value: str, sensitivity: PIISensitivity) -> str:
        """
        Mask a value based on its sensitivity level.

        Args:
            value: Value to mask
            sensitivity: Sensitivity level

        Returns:
            Masked value
        """
        mask_func = self.MASKING_STRATEGIES.get(sensitivity, lambda x: "*" * len(x))
        return mask_func(value)

    def mask_dict(
        self, data: Dict[str, str], classification: Dict[str, PIICategory]
    ) -> Dict[str, str]:
        """
        Mask PII fields in a dictionary.

        Args:
            data: Original data dictionary
            classification: PII classification for fields

        Returns:
            Dictionary with PII fields masked
        """
        masked_data = data.copy()

        for field_name, category in classification.items():
            if field_name in masked_data:
                sensitivity = PIISensitivity(PIIIdentifier.PATTERNS[category]["sensitivity"])
                masked_data[field_name] = self.mask_value(masked_data[field_name], sensitivity)

        return masked_data

    def mask_log_message(self, message: str) -> str:
        """
        Mask PII in log messages.

        Args:
            message: Original log message

        Returns:
            Message with PII masked
        """
        identifier = PIIIdentifier()
        pii_fields = identifier.identify_pii(message)

        masked_message = message
        for pii in pii_fields:
            if pii.pattern in masked_message:
                masked = self.mask_value(pii.pattern, pii.sensitivity)
                masked_message = masked_message.replace(pii.pattern, masked)

        return masked_message


class PIIAccessControl:
    """
    Access control for PII data.
    """

    def __init__(self) -> None:
        self.access_log: List[Dict] = []

    def check_access(
        self,
        user_id: str,
        pii_category: PIICategory,
        purpose: str,
        required_role: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Check if user has access to PII category.

        Args:
            user_id: User requesting access
            pii_category: PII category being accessed
            purpose: Purpose of access
            required_role: Required role for access (optional)

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Log access attempt
        self.access_log.append(
            {
                "user_id": user_id,
                "pii_category": pii_category.value,
                "purpose": purpose,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Check sensitivity-based access rules
        if pii_category in [PIICategory.SSN, PIICategory.CREDIT_CARD]:
            if required_role != "admin":
                return False, "Admin role required for critical PII access"

        if pii_category == PIICategory.MEDICAL_RECORD:
            if purpose not in ["treatment", "research", "clinical"]:
                return False, f"Invalid purpose for medical record access: {purpose}"

        return True, "Access granted"

    def log_access(
        self,
        user_id: str,
        pii_category: PIICategory,
        action: str,
        record_id: str,
        allowed: bool,
    ) -> None:
        """
        Log PII access for audit trail.

        Args:
            user_id: User accessing PII
            pii_category: PII category accessed
            action: Action performed (read, write, delete)
            record_id: Record identifier
            allowed: Whether access was allowed
        """
        self.access_log.append(
            {
                "user_id": user_id,
                "pii_category": pii_category.value,
                "action": action,
                "record_id": record_id,
                "allowed": allowed,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(
            f"PII Access Log: User={user_id}, Category={pii_category.value}, "
            f"Action={action}, Record={record_id}, Allowed={allowed}"
        )


# Global instances
pii_identifier = PIIIdentifier()
pii_masker = PIIMasker()
pii_access_control = PIIAccessControl()


def protect_pii_in_logs(log_message: str) -> str:
    """
    Protect PII in log messages by masking.

    Args:
        log_message: Original log message

    Returns:
        Log message with PII masked
    """
    return pii_masker.mask_log_message(log_message)


def classify_and_mask_data(data: Dict[str, str]) -> Dict[str, str]:
    """
    Classify and mask PII in data dictionary.

    Args:
        data: Original data dictionary

    Returns:
        Data dictionary with PII classified and masked
    """
    classification = pii_identifier.classify_data(data)
    masked_data = pii_masker.mask_dict(data, classification)
    return masked_data
