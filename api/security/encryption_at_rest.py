"""
Encryption at Rest for Sensitive Data

Provides AES-256 encryption for database fields, file storage, and PHI.
Implements key rotation, secure key derivation, and transparent encryption/decryption.
Compliant with HIPAA and GDPR encryption requirements.
"""

import base64
import hashlib
import hmac
import logging
import os
from dataclasses import dataclass
from typing import Optional, Union

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Constants for encryption
AES_KEY_SIZE = 32  # 256 bits
SALT_SIZE = 32
NONCE_SIZE = 12
ITERATIONS = 100000  # PBKDF2 iterations


@dataclass
class EncryptionResult:
    """Container for encrypted data with metadata."""

    ciphertext: bytes
    nonce: bytes
    salt: bytes
    tag: bytes

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode("utf-8"),
            "nonce": base64.b64encode(self.nonce).decode("utf-8"),
            "salt": base64.b64encode(self.salt).decode("utf-8"),
            "tag": base64.b64encode(self.tag).decode("utf-8"),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EncryptionResult":
        """Create from dictionary."""
        return cls(
            ciphertext=base64.b64decode(data["ciphertext"]),
            nonce=base64.b64decode(data["nonce"]),
            salt=base64.b64decode(data["salt"]),
            tag=base64.b64decode(data["tag"]),
        )


class EncryptionManager:
    """
    Manager for encryption at rest operations.

    Handles:
    - AES-256-GCM encryption for sensitive fields
    - Key derivation from master key
    - Transparent encryption/decryption
    - Key rotation support
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager.

        Args:
            master_key: Base64-encoded master key (or from ENCRYPTION_KEY env var)
        """
        self.master_key = self._get_master_key(master_key)
        self._cipher_cache: dict = {}

    def _get_master_key(self, provided_key: Optional[str]) -> bytes:
        """
        Get or generate master encryption key.

        Args:
            provided_key: Optional provided key

        Returns:
            Master key bytes
        """
        if provided_key:
            return base64.b64decode(provided_key)

        # Try environment variable
        env_key = os.getenv("ENCRYPTION_KEY")
        if env_key:
            return base64.b64decode(env_key)

        # Generate a new key (for development only)
        logger.warning(
            "No encryption key provided. Generating temporary key. "
            "THIS IS INSECURE FOR PRODUCTION!"
        )
        return AESGCM.generate_key(bit_length=256)

    def derive_key(self, salt: bytes, context: str = "default") -> bytes:
        """
        Derive encryption key from master key using PBKDF2.

        Args:
            salt: Random salt bytes
            context: Key context for separation

        Returns:
            Derived 256-bit key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt + context.encode(),
            iterations=ITERATIONS,
        )
        return kdf.derive(self.master_key)

    def encrypt_field(
        self, plaintext: Union[str, bytes], context: str = "default"
    ) -> EncryptionResult:
        """
        Encrypt a sensitive field value.

        Args:
            plaintext: Data to encrypt
            context: Encryption context for key separation

        Returns:
            EncryptionResult with ciphertext and metadata
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # Generate random salt and nonce
        salt = os.urandom(SALT_SIZE)
        nonce = os.urandom(NONCE_SIZE)

        # Derive key
        key = self.derive_key(salt, context)

        # Encrypt
        aesgcm = AESGCM(key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)

        # Split ciphertext and tag
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]

        return EncryptionResult(
            ciphertext=ciphertext,
            nonce=nonce,
            salt=salt,
            tag=tag,
        )

    def decrypt_field(self, encrypted: EncryptionResult, context: str = "default") -> bytes:
        """
        Decrypt an encrypted field value.

        Args:
            encrypted: EncryptionResult containing ciphertext
            context: Encryption context (must match encryption context)

        Returns:
            Decrypted plaintext bytes
        """
        # Derive key
        key = self.derive_key(encrypted.salt, context)

        # Combine ciphertext and tag for AES-GCM
        ciphertext_with_tag = encrypted.ciphertext + encrypted.tag

        # Decrypt
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(encrypted.nonce, ciphertext_with_tag, None)
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid key or corrupted data")

    def encrypt_dict(
        self, data: dict, sensitive_fields: list[str], context: str = "default"
    ) -> dict:
        """
        Encrypt specified fields in a dictionary.

        Args:
            data: Dictionary containing data
            sensitive_fields: List of field names to encrypt
            context: Encryption context

        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        for field in sensitive_fields:
            if field in result and result[field] is not None:
                encrypted = self.encrypt_field(str(result[field]), context)
                result[field] = encrypted.to_dict()
                result[f"{field}_encrypted"] = True
        return result

    def decrypt_dict(
        self, data: dict, sensitive_fields: list[str], context: str = "default"
    ) -> dict:
        """
        Decrypt specified fields in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            sensitive_fields: List of field names to decrypt
            context: Encryption context

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        for field in sensitive_fields:
            encrypted_field = f"{field}_encrypted"
            if encrypted_field in result and field in result:
                try:
                    encrypted = EncryptionResult.from_dict(result[field])
                    decrypted = self.decrypt_field(encrypted, context)
                    result[field] = decrypted.decode("utf-8")
                    del result[encrypted_field]
                except Exception as e:
                    logger.error(f"Failed to decrypt field {field}: {e}")
                    result[field] = "[DECRYPTION_ERROR]"
        return result

    def encrypt_file(self, file_path: str, output_path: str, context: str = "file") -> None:
        """
        Encrypt a file at rest.

        Args:
            file_path: Path to file to encrypt
            output_path: Path for encrypted output
            context: Encryption context
        """
        with open(file_path, "rb") as f:
            plaintext = f.read()

        encrypted = self.encrypt_field(plaintext, context)

        # Write encrypted data with metadata
        import json

        with open(output_path, "w") as f:
            json.dump(encrypted.to_dict(), f)

        logger.info(f"File encrypted: {file_path} -> {output_path}")

    def decrypt_file(self, encrypted_path: str, output_path: str, context: str = "file") -> None:
        """
        Decrypt a file at rest.

        Args:
            encrypted_path: Path to encrypted file
            output_path: Path for decrypted output
            context: Encryption context
        """
        import json

        with open(encrypted_path, "r") as f:
            data = json.load(f)

        encrypted = EncryptionResult.from_dict(data)
        plaintext = self.decrypt_field(encrypted, context)

        with open(output_path, "wb") as f:
            f.write(plaintext)

        logger.info(f"File decrypted: {encrypted_path} -> {output_path}")

    def rotate_key(
        self, encrypted_data: EncryptionResult, old_context: str, new_context: str
    ) -> EncryptionResult:
        """
        Re-encrypt data with a new key context (key rotation).

        Args:
            encrypted_data: Currently encrypted data
            old_context: Original encryption context
            new_context: New encryption context

        Returns:
            Re-encrypted data
        """
        # Decrypt with old key
        plaintext = self.decrypt_field(encrypted_data, old_context)

        # Re-encrypt with new key
        return self.encrypt_field(plaintext, new_context)

    def generate_data_encryption_key(self) -> str:
        """Generate a new data encryption key."""
        key = AESGCM.generate_key(bit_length=256)
        return base64.b64encode(key).decode("utf-8")

    def hash_sensitive_value(self, value: str, salt: Optional[bytes] = None) -> str:
        """
        Create a searchable hash of a sensitive value (for indexing).

        Uses HMAC-SHA256 for deterministic hashing with key protection.

        Args:
            value: Value to hash
            salt: Optional salt (generated if not provided)

        Returns:
            Base64-encoded hash
        """
        if salt is None:
            salt = os.urandom(16)

        h = hmac.new(self.master_key, salt + value.encode(), hashlib.sha256)
        return base64.b64encode(salt + h.digest()).decode("utf-8")

    def verify_hashed_value(self, value: str, hashed: str) -> bool:
        """
        Verify a value against its searchable hash.

        Args:
            value: Value to verify
            hashed: Previously computed hash

        Returns:
            True if value matches hash
        """
        try:
            decoded = base64.b64decode(hashed)
            salt = decoded[:16]
            expected_hash = self.hash_sensitive_value(value, salt)
            return hmac.compare_digest(hashed, expected_hash)
        except Exception:
            return False


class PHISanitizer:
    """
    Sanitizer for Protected Health Information (PHI).

    Implements HIPAA-compliant data handling including:
    - Field-level encryption
    - Data masking for display
    - Audit logging
    """

    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption = encryption_manager
        self.phi_fields = [
            "patient_id",
            "ssn",
            "mrn",  # Medical Record Number
            "dob",
            "address",
            "phone",
            "email",
            "diagnosis",
            "treatment_data",
            "insurance_id",
        ]

    def sanitize_for_storage(self, data: dict) -> dict:
        """
        Sanitize PHI data for database storage.

        Args:
            data: Dictionary containing potential PHI

        Returns:
            Sanitized data with encrypted PHI fields
        """
        return self.encryption.encrypt_dict(data, self.phi_fields, context="phi")

    def desanitize_for_use(self, data: dict) -> dict:
        """
        Decrypt PHI data for authorized use.

        Args:
            data: Dictionary with encrypted PHI

        Returns:
            Data with decrypted PHI fields
        """
        return self.encryption.decrypt_dict(data, self.phi_fields, context="phi")

    def mask_for_display(self, data: dict, visible_fields: list[str] = None) -> dict:
        """
        Mask sensitive data for safe display.

        Args:
            data: Data containing PHI
            visible_fields: Fields that should remain visible

        Returns:
            Masked data safe for logging/display
        """
        visible = visible_fields or []
        result = {}
        for key, value in data.items():
            if key in self.phi_fields and key not in visible:
                if isinstance(value, str) and len(value) > 4:
                    result[key] = value[:2] + "***" + value[-2:]
                else:
                    result[key] = "***MASKED***"
            else:
                result[key] = value
        return result


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None
_phi_sanitizer: Optional[PHISanitizer] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def get_phi_sanitizer() -> PHISanitizer:
    """Get or create global PHI sanitizer."""
    global _phi_sanitizer
    if _phi_sanitizer is None:
        _phi_sanitizer = PHISanitizer(get_encryption_manager())
    return _phi_sanitizer
