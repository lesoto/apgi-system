"""
API Key Rotation System

Provides secure API key lifecycle management including:
- Automatic key rotation on configurable schedules
- Grace period for dual-key validation during rotation
- Secure key generation with cryptographically secure randomness
- Key versioning and history tracking
- Emergency key revocation
"""

import secrets
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    """Status of an API key."""

    ACTIVE = "active"
    ROTATING = "rotating"  # New key generated, old key still valid
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class APIKey:
    """Represents an API key with metadata."""

    key_id: str
    key_hash: str  # Store hash only, never the plaintext key
    prefix: str  # First 8 chars for identification
    status: KeyStatus
    created_at: datetime
    expires_at: datetime
    rotated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class APIKeyRotationManager:
    """
    Manages API key lifecycle with automatic rotation.

    Features:
    - Configurable rotation intervals (default: 90 days)
    - Grace period for dual-key validation (default: 24 hours)
    - Secure key generation (32-byte random tokens)
    - Key versioning with full history
    - Emergency revocation capability
    """

    DEFAULT_ROTATION_DAYS = 90
    DEFAULT_GRACE_PERIOD_HOURS = 24
    KEY_PREFIX_LENGTH = 8
    KEY_BYTES = 32  # 256 bits of entropy

    def __init__(
        self,
        rotation_days: int = DEFAULT_ROTATION_DAYS,
        grace_period_hours: int = DEFAULT_GRACE_PERIOD_HOURS,
    ):
        """
        Initialize the API key rotation manager.

        Args:
            rotation_days: Days between automatic rotations
            grace_period_hours: Hours old keys remain valid after rotation
        """
        self.rotation_days = rotation_days
        self.grace_period_hours = grace_period_hours
        self._keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self._key_hashes: Dict[str, str] = {}  # key_hash -> key_id
        self._rotation_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    def _generate_key(self) -> Tuple[str, str, str]:
        """
        Generate a new cryptographically secure API key.

        Returns:
            Tuple of (key_id, full_key, key_hash)
        """
        # Generate 32 bytes of randomness (256 bits)
        key_bytes = secrets.token_bytes(self.KEY_BYTES)
        full_key = key_bytes.hex()  # 64 character hex string

        # Create unique key ID
        key_id = hashlib.sha256(f"{full_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()[
            :16
        ]

        # Hash for storage (never store plaintext)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        return key_id, full_key, key_hash

    async def create_key(
        self,
        metadata: Optional[Dict] = None,
        custom_expiry: Optional[datetime] = None,
    ) -> Tuple[str, str]:
        """
        Create a new API key.

        Args:
            metadata: Optional metadata for the key
            custom_expiry: Optional custom expiry date

        Returns:
            Tuple of (key_id, full_key) - full_key is shown ONCE
        """
        async with self._lock:
            key_id, full_key, key_hash = self._generate_key()

            expires_at = custom_expiry or (datetime.utcnow() + timedelta(days=self.rotation_days))

            key = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                prefix=full_key[: self.KEY_PREFIX_LENGTH],
                status=KeyStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                metadata=metadata or {},
            )

            self._keys[key_id] = key
            self._key_hashes[key_hash] = key_id

            logger.info(f"Created new API key: {key_id} (prefix: {key.prefix})")
            return key_id, full_key

    async def validate_key(self, full_key: str) -> Optional[str]:
        """
        Validate an API key and return key_id if valid.

        Args:
            full_key: The API key to validate

        Returns:
            key_id if valid, None otherwise
        """
        if not full_key or len(full_key) < self.KEY_PREFIX_LENGTH:
            return None

        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        async with self._lock:
            key_id = self._key_hashes.get(key_hash)
            if not key_id:
                return None

            key = self._keys.get(key_id)
            if not key:
                return None

            # Check status and expiry
            if key.status == KeyStatus.REVOKED:
                return None

            if key.status == KeyStatus.EXPIRED:
                return None

            if datetime.utcnow() > key.expires_at:
                key.status = KeyStatus.EXPIRED
                return None

            return key_id

    async def rotate_key(self, key_id: str) -> Tuple[str, str]:
        """
        Rotate an existing API key.

        During grace period, both old and new keys are valid.

        Args:
            key_id: The key ID to rotate

        Returns:
            Tuple of (new_key_id, new_full_key)
        """
        async with self._lock:
            old_key = self._keys.get(key_id)
            if not old_key:
                raise ValueError(f"Key not found: {key_id}")

            if old_key.status in [KeyStatus.REVOKED, KeyStatus.EXPIRED]:
                raise ValueError(f"Cannot rotate key with status: {old_key.status}")

            # Mark old key as rotating (grace period)
            old_key.status = KeyStatus.ROTATING
            old_key.rotated_at = datetime.utcnow()
            old_key.expires_at = datetime.utcnow() + timedelta(hours=self.grace_period_hours)

            # Create new key
            new_key_id, new_full_key, new_key_hash = self._generate_key()
            new_expires = datetime.utcnow() + timedelta(days=self.rotation_days)

            new_key = APIKey(
                key_id=new_key_id,
                key_hash=new_key_hash,
                prefix=new_full_key[: self.KEY_PREFIX_LENGTH],
                status=KeyStatus.ACTIVE,
                created_at=datetime.utcnow(),
                expires_at=new_expires,
                metadata={
                    **old_key.metadata,
                    "rotated_from": key_id,
                    "rotation_date": datetime.utcnow().isoformat(),
                },
            )

            self._keys[new_key_id] = new_key
            self._key_hashes[new_key_hash] = new_key_id

            logger.info(
                f"Rotated key {key_id} -> {new_key_id} "
                f"(grace period: {self.grace_period_hours}h)"
            )
            return new_key_id, new_full_key

    async def revoke_key(self, key_id: str, reason: Optional[str] = None) -> bool:
        """
        Revoke an API key immediately.

        Args:
            key_id: The key ID to revoke
            reason: Optional reason for revocation

        Returns:
            True if revoked, False if not found
        """
        async with self._lock:
            key = self._keys.get(key_id)
            if not key:
                return False

            key.status = KeyStatus.REVOKED
            key.revoked_at = datetime.utcnow()
            key.revoke_reason = reason or "Manual revocation"

            # Remove from hash lookup to prevent validation
            self._key_hashes.pop(key.key_hash, None)

            logger.warning(f"Revoked API key {key_id}: {key.revoke_reason}")
            return True

    async def get_key_info(self, key_id: str) -> Optional[Dict]:
        """
        Get non-sensitive information about a key.

        Args:
            key_id: The key ID to query

        Returns:
            Dict with key metadata (no hashes)
        """
        key = self._keys.get(key_id)
        if not key:
            return None

        return {
            "key_id": key.key_id,
            "prefix": key.prefix,
            "status": key.status.value,
            "created_at": key.created_at.isoformat(),
            "expires_at": key.expires_at.isoformat(),
            "rotated_at": key.rotated_at.isoformat() if key.rotated_at else None,
            "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
            "revoke_reason": key.revoke_reason,
            "metadata": key.metadata,
        }

    async def list_keys(self, status: Optional[KeyStatus] = None) -> List[Dict]:
        """
        List all keys with optional status filter.

        Args:
            status: Optional status to filter by

        Returns:
            List of key info dicts
        """
        keys = self._keys.values()
        if status:
            keys = [k for k in keys if k.status == status]

        return [
            {
                "key_id": k.key_id,
                "prefix": k.prefix,
                "status": k.status.value,
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat(),
            }
            for k in keys
        ]

    async def check_expired_keys(self) -> List[str]:
        """
        Check for and mark expired keys.

        Returns:
            List of key IDs that were expired
        """
        expired = []
        now = datetime.utcnow()

        async with self._lock:
            for key in self._keys.values():
                if key.status in [KeyStatus.ACTIVE, KeyStatus.ROTATING]:
                    if now > key.expires_at:
                        key.status = KeyStatus.EXPIRED
                        expired.append(key.key_id)

        if expired:
            logger.info(f"Marked {len(expired)} keys as expired")
        return expired

    async def start_rotation_monitor(self) -> None:
        """Start background task for automatic key rotation."""
        if self._rotation_task and not self._rotation_task.done():
            return

        self._rotation_task = asyncio.create_task(self._rotation_monitor())
        logger.info("Started API key rotation monitor")

    async def stop_rotation_monitor(self) -> None:
        """Stop the background rotation monitor."""
        if self._rotation_task:
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass
            self._rotation_task = None
            logger.info("Stopped API key rotation monitor")

    async def _rotation_monitor(self) -> None:
        """Background task to monitor and rotate keys."""
        while True:
            try:
                # Check for expired keys
                await self.check_expired_keys()

                # Check for keys needing rotation
                now = datetime.utcnow()
                rotation_threshold = now - timedelta(days=self.rotation_days)

                async with self._lock:
                    for key in self._keys.values():
                        if key.status == KeyStatus.ACTIVE:
                            if key.created_at < rotation_threshold:
                                logger.info(f"Key {key.key_id} scheduled for rotation")
                                # In production, notify admin or auto-rotate
                                # For now, just log

                # Sleep for 1 hour
                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Error in rotation monitor: {e}")
                await asyncio.sleep(3600)


# Global instance
_rotation_manager: Optional[APIKeyRotationManager] = None


def get_rotation_manager() -> APIKeyRotationManager:
    """Get or create global rotation manager instance."""
    global _rotation_manager
    if _rotation_manager is None:
        _rotation_manager = APIKeyRotationManager()
    return _rotation_manager
