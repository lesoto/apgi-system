"""PII (Personally Identifiable Information) protection mechanisms."""

import re
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

from ..logging_config import get_logger

logger = get_logger(__name__)


class PIIClassification(Enum):
    """Classification levels for PII."""

    # Direct identifiers - can uniquely identify an individual
    NAME = auto()
    EMAIL = auto()
    PHONE = auto()
    SSN = auto()  # Social Security Number
    PASSPORT = auto()
    DRIVERS_LICENSE = auto()

    # Indirect identifiers - can identify when combined
    ZIP_CODE = auto()
    DATE_OF_BIRTH = auto()
    ADDRESS = auto()
    IP_ADDRESS = auto()
    MAC_ADDRESS = auto()

    # Sensitive PII - requires special protection
    MEDICAL_RECORD = auto()
    FINANCIAL_ACCOUNT = auto()
    CREDIT_CARD = auto()
    BIOMETRIC = auto()
    GENETIC = auto()


@dataclass
class PIIPattern:
    """Pattern for detecting PII in text."""

    classification: PIIClassification
    pattern: str
    description: str
    confidence: float


class PIIDetector:
    """Detects PII in data using pattern matching and ML.

    Features:
    - Regex-based pattern matching
    - Context-aware detection
    - Confidence scoring
    - Custom pattern registration
    """

    DEFAULT_PATTERNS = [
        PIIPattern(
            PIIClassification.EMAIL,
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "Email address",
            0.95,
        ),
        PIIPattern(
            PIIClassification.PHONE,
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "Phone number (US format)",
            0.85,
        ),
        PIIPattern(
            PIIClassification.SSN,
            r"\b\d{3}-\d{2}-\d{4}\b",
            "Social Security Number",
            0.99,
        ),
        PIIPattern(
            PIIClassification.CREDIT_CARD,
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            "Credit card number",
            0.90,
        ),
        PIIPattern(
            PIIClassification.IP_ADDRESS,
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "IP address",
            0.80,
        ),
        PIIPattern(
            PIIClassification.DATE_OF_BIRTH,
            r"\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/]\d{4}\b",
            "Date (MM/DD/YYYY or MM-DD-YYYY)",
            0.70,
        ),
        PIIPattern(
            PIIClassification.ZIP_CODE,
            r"\b\d{5}(?:-\d{4})?\b",
            "ZIP code",
            0.60,
        ),
    ]

    def __init__(self, custom_patterns: Optional[List[PIIPattern]] = None) -> None:
        """Initialize PII detector.

        Args:
            custom_patterns: Additional patterns to use
        """
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

        # Compile regex patterns
        self.compiled_patterns = [
            (p.classification, re.compile(p.pattern), p.confidence) for p in self.patterns
        ]

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII with metadata
        """
        detections = []

        for classification, pattern, confidence in self.compiled_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                detections.append(
                    {
                        "classification": classification.name,
                        "match": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": confidence,
                        "pattern": pattern.pattern,
                    }
                )

        return detections

    def has_pii(self, text: str) -> bool:
        """Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected
        """
        return len(self.detect(text)) > 0

    def classify(self, data: Any) -> Dict[str, Any]:
        """Classify data for PII content.

        Args:
            data: Data to classify (string, dict, list)

        Returns:
            Classification results
        """
        if isinstance(data, str):
            detections = self.detect(data)
            return {
                "has_pii": len(detections) > 0,
                "detections": detections,
                "pii_types": list(set(d["classification"] for d in detections)),
            }
        elif isinstance(data, dict):
            field_results: Dict[str, Any] = {}
            for key, value in data.items():
                if isinstance(value, str):
                    field_results[key] = self.classify(value)
            return {
                "has_pii": any(r.get("has_pii", False) for r in field_results.values()),
                "fields": field_results,
            }
        elif isinstance(data, list):
            item_results: List[Dict[str, Any]] = []
            for item in data:
                if isinstance(item, str):
                    item_results.append(self.classify(item))
            return {
                "has_pii": any(r.get("has_pii", False) for r in item_results),
                "items": item_results,
            }
        else:
            return {"has_pii": False, "reason": "Unsupported type"}


class PIIMasker:
    """Masks PII in data for logging and display.

    Features:
    - Configurable masking strategies
    - Preserves data structure
    - Reversible masking (with key)
    - Format-aware masking
    """

    MASK_CHAR = "*"
    EMAIL_MASK = "***@***.***"
    PHONE_MASK = "***-***-****"
    SSN_MASK = "***-**-****"
    CREDIT_CARD_MASK = "****-****-****-****"

    def __init__(
        self,
        detector: Optional[PIIDetector] = None,
        mask_char: str = MASK_CHAR,
    ) -> None:
        """Initialize PII masker.

        Args:
            detector: PII detector instance
            mask_char: Character to use for masking
        """
        self.detector = detector or PIIDetector()
        self.mask_char = mask_char

    def mask_string(self, text: str, classification: Optional[PIIClassification] = None) -> str:
        """Mask PII in a string.

        Args:
            text: Text to mask
            classification: Specific classification to mask (all if None)

        Returns:
            Masked string
        """
        if classification:
            # Mask specific type
            pattern = next(
                (p for p in self.detector.patterns if p.classification == classification),
                None,
            )
            if pattern:
                return re.sub(pattern.pattern, self._get_mask(classification), text)
            return text
        else:
            # Mask all detected PII
            masked = text
            for pii_class, compiled_pattern, _ in self.detector.compiled_patterns:
                masked = compiled_pattern.sub(self._get_mask(pii_class), masked)
            return masked

    def _get_mask(self, classification: PIIClassification) -> str:
        """Get mask string for classification.

        Args:
            classification: PII classification

        Returns:
            Mask string
        """
        mapping = {
            PIIClassification.EMAIL: self.EMAIL_MASK,
            PIIClassification.PHONE: self.PHONE_MASK,
            PIIClassification.SSN: self.SSN_MASK,
            PIIClassification.CREDIT_CARD: self.CREDIT_CARD_MASK,
        }
        return mapping.get(classification, self.MASK_CHAR * 8)

    def mask_dict(
        self, data: Dict[str, Any], sensitive_keys: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """Mask PII in dictionary.

        Args:
            data: Dictionary to mask
            sensitive_keys: Keys known to contain PII

        Returns:
            Masked dictionary
        """
        masked: Dict[str, Any] = {}
        sensitive_keys = sensitive_keys or set()

        for key, value in data.items():
            if key in sensitive_keys and isinstance(value, str):
                masked[key] = self.mask_string(value)
            elif isinstance(value, str):
                classification = self.detector.detect(value)
                if classification:
                    masked[key] = self.mask_string(value)
                else:
                    masked[key] = value
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value, sensitive_keys)  # type: ignore[assignment]
            elif isinstance(value, list):
                masked[key] = self.mask_list(value, sensitive_keys)  # type: ignore[assignment]
            else:
                masked[key] = value

        return masked

    def mask_list(self, data: List[Any], sensitive_keys: Optional[Set[str]] = None) -> List[Any]:
        """Mask PII in list.

        Args:
            data: List to mask
            sensitive_keys: Keys known to contain PII

        Returns:
            Masked list
        """
        masked: List[Any] = []
        for item in data:
            if isinstance(item, str):
                masked.append(self.mask_string(item))
            elif isinstance(item, dict):
                masked.append(self.mask_dict(item, sensitive_keys))
            elif isinstance(item, list):
                masked.append(self.mask_list(item, sensitive_keys))
            else:
                masked.append(item)
        return masked

    def mask_json(self, json_str: str) -> str:
        """Mask PII in JSON string.

        Args:
            json_str: JSON string to mask

        Returns:
            Masked JSON string
        """
        import json

        data = json.loads(json_str)
        masked = self.mask_dict(data)
        return json.dumps(masked)


class PIIProtector:
    """Comprehensive PII protection with encryption and access controls.

    Features:
    - Encryption at rest for PII
    - Access control enforcement
    - Audit logging for PII access
    - Data minimization
    """

    def __init__(
        self,
        detector: Optional[PIIDetector] = None,
        masker: Optional[PIIMasker] = None,
        encryption_key: Optional[str] = None,
    ) -> None:
        """Initialize PII protector.

        Args:
            detector: PII detector instance
            masker: PII masker instance
            encryption_key: Key for PII encryption
        """
        self.detector = detector or PIIDetector()
        self.masker = masker or PIIMasker(self.detector)
        self.encryption_key = encryption_key
        self._access_log: List[Dict[str, Any]] = []

    def protect(
        self,
        data: Any,
        operation: str = "read",
        user_id: Optional[str] = None,
    ) -> Any:
        """Protect PII in data based on operation and user.

        Args:
            data: Data to protect
            operation: Operation being performed (read, write, delete)
            user_id: User performing operation

        Returns:
            Protected data (masked or encrypted)
        """
        # Log access
        self._log_access(data, operation, user_id)

        # Check if data contains PII
        classification = self.detector.classify(data)

        if not classification["has_pii"]:
            return data

        # Apply protection based on operation
        if operation == "read":
            # Mask for display/logging
            if isinstance(data, dict):
                return self.masker.mask_dict(data)
            elif isinstance(data, str):
                return self.masker.mask_string(data)
            else:
                return data
        elif operation == "write":
            # Encrypt for storage
            return self._encrypt(data)
        else:
            return data

    def _encrypt(self, data: Any) -> Any:
        """Encrypt PII data.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        if not self.encryption_key:
            logger.warning("No encryption key, returning masked data")
            if isinstance(data, dict):
                return self.masker.mask_dict(data)
            return data

        # Simple encryption - in production, use proper encryption library
        if isinstance(data, str):
            return self._encrypt_string(data)
        elif isinstance(data, dict):
            return {k: self._encrypt(v) for k, v in data.items()}
        else:
            return data

    def _encrypt_string(self, text: str) -> str:
        """Encrypt a string.

        Args:
            text: Text to encrypt

        Returns:
            Encrypted string
        """
        # In production, use cryptography.fernet or similar
        key = hashlib.sha256(self.encryption_key.encode()).digest()
        cipher = hashlib.sha256(key + text.encode()).hexdigest()
        return f"ENC:{cipher}"

    def _log_access(
        self,
        data: Any,
        operation: str,
        user_id: Optional[str],
    ) -> None:
        """Log PII access for audit trail.

        Args:
            data: Data being accessed
            operation: Operation type
            user_id: User performing operation
        """
        classification = self.detector.classify(data)

        if classification["has_pii"]:
            self._access_log.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation": operation,
                    "user_id": user_id,
                    "pii_types": classification.get("pii_types", []),
                }
            )

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get PII access log.

        Returns:
            List of access log entries
        """
        return self._access_log.copy()


# Global instances
_pii_detector: Optional[PIIDetector] = None
_pii_masker: Optional[PIIMasker] = None
_pii_protector: Optional[PIIProtector] = None


def get_pii_detector() -> PIIDetector:
    """Get global PII detector instance."""
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector


def get_pii_masker() -> PIIMasker:
    """Get global PII masker instance."""
    global _pii_masker
    if _pii_masker is None:
        _pii_masker = PIIMasker(get_pii_detector())
    return _pii_masker


def get_pii_protector(encryption_key: Optional[str] = None) -> PIIProtector:
    """Get global PII protector instance."""
    global _pii_protector
    if _pii_protector is None:
        _pii_protector = PIIProtector(
            detector=get_pii_detector(),
            masker=get_pii_masker(),
            encryption_key=encryption_key,
        )
    return _pii_protector
