"""API Key Management for SalesOS.

Provides secure API key generation, hashing, rotation, scope binding,
and per-key rate limiting.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class KeyScope(str, Enum):
    """API key permission scopes."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SEARCH = "search"
    ENRICHMENT = "enrichment"


class ApiKeyRecord(BaseModel):
    """Stored API key metadata (never stores the raw key)."""
    key_id: str
    key_hash: str
    name: str
    scopes: list[KeyScope] = [KeyScope.READ]
    tenant_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    rotated_at: datetime | None = None
    revoked_at: datetime | None = None
    is_active: bool = True
    rate_limit_per_minute: int = 60
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiKeyManager:
    """Manages API key lifecycle: generation, hashing, rotation, and validation.

    Keys are stored as SHA-256 hashes only. The raw key is returned once
    at creation time and never stored.

    Usage:
        manager = ApiKeyManager()
        raw_key, record = manager.create_key(
            name="My Integration",
            scopes=[KeyScope.READ, KeyScope.SEARCH],
        )
        # Store `record` in database. Show `raw_key` to user ONCE.

        # Verify on each request:
        is_valid = manager.verify_key(raw_key, record.key_hash)
    """

    _KEY_PREFIX = "sk_"
    _RAW_KEY_BYTES = 32  # 256 bits
    _HASH_ALGO = "sha256"

    def generate_raw_key(self) -> str:
        """Generate a cryptographically secure 256-bit API key.

        Returns:
            Raw API key string with 'sk_' prefix (e.g., 'sk_abc123...').
        """
        random_bytes = secrets.token_urlsafe(self._RAW_KEY_BYTES)
        return f"{self._KEY_PREFIX}{random_bytes}"

    def hash_key(self, raw_key: str) -> str:
        """Hash an API key using SHA-256 for secure storage.

        Args:
            raw_key: The raw API key string.

        Returns:
            Hex-encoded SHA-256 hash.
        """
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def verify_key(self, raw_key: str, stored_hash: str) -> bool:
        """Verify a raw key against its stored hash using constant-time comparison.

        Args:
            raw_key: The raw API key to verify.
            stored_hash: The stored SHA-256 hash.

        Returns:
            True if the key matches.
        """
        computed_hash = self.hash_key(raw_key)
        return hmac.compare_digest(computed_hash, stored_hash)

    def create_key(
        self,
        name: str,
        scopes: list[KeyScope] | None = None,
        tenant_id: str | None = None,
        expiry_days: int | None = 365,
        rate_limit_per_minute: int = 60,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, ApiKeyRecord]:
        """Generate a new API key and its metadata record.

        Args:
            name: Human-readable name for the key.
            scopes: Permission scopes for this key.
            tenant_id: Optional tenant binding.
            expiry_days: Days until key expires (None = no expiry).
            rate_limit_per_minute: Per-minute rate limit for this key.
            metadata: Optional metadata dict.

        Returns:
            Tuple of (raw_key, ApiKeyRecord). Raw key shown once to user.
        """
        raw_key = self.generate_raw_key()
        key_hash = self.hash_key(raw_key)

        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(days=expiry_days)) if expiry_days else None

        record = ApiKeyRecord(
            key_id=secrets.token_urlsafe(16),
            key_hash=key_hash,
            name=name,
            scopes=scopes or [KeyScope.READ],
            tenant_id=tenant_id,
            created_at=now,
            expires_at=expires_at,
            rate_limit_per_minute=rate_limit_per_minute,
            metadata=metadata or {},
        )

        return raw_key, record

    def rotate_key(
        self,
        old_record: ApiKeyRecord,
        grace_period_hours: int = 24,
    ) -> tuple[str, ApiKeyRecord, ApiKeyRecord]:
        """Rotate an API key with a grace period for the old key.

        Creates a new key and marks the old one for expiry after grace period.
        Both keys remain valid during the grace period.

        Args:
            old_record: The current key record to rotate.
            grace_period_hours: Hours the old key remains valid after rotation.

        Returns:
            Tuple of (new_raw_key, new_record, updated_old_record).
        """
        new_raw_key, new_record = self.create_key(
            name=old_record.name,
            scopes=old_record.scopes,
            tenant_id=old_record.tenant_id,
            expiry_days=365,
            rate_limit_per_minute=old_record.rate_limit_per_minute,
            metadata={**old_record.metadata, "rotated_from": old_record.key_id},
        )

        # Mark old key for expiry after grace period
        now = datetime.now(timezone.utc)
        old_record.rotated_at = now
        old_record.expires_at = now + timedelta(hours=grace_period_hours)
        old_record.metadata["grace_expiry"] = True

        return new_raw_key, new_record, old_record

    def is_key_valid(self, record: ApiKeyRecord) -> bool:
        """Check if a key record is currently valid (active, not expired, not revoked).

        Args:
            record: The API key record to check.

        Returns:
            True if the key is valid for use.
        """
        if not record.is_active:
            return False
        if record.revoked_at is not None:
            return False
        if record.expires_at is not None and record.expires_at < datetime.now(timezone.utc):
            return False
        return True

    def has_scope(self, record: ApiKeyRecord, required_scope: KeyScope) -> bool:
        """Check if a key has a specific permission scope.

        Admin scope grants all permissions.

        Args:
            record: The API key record.
            required_scope: The scope to check for.

        Returns:
            True if the key has the required scope.
        """
        if KeyScope.ADMIN in record.scopes:
            return True
        return required_scope in record.scopes

    def revoke_key(self, record: ApiKeyRecord) -> ApiKeyRecord:
        """Revoke an API key immediately.

        Args:
            record: The API key record to revoke.

        Returns:
            Updated record with revoked status.
        """
        record.is_active = False
        record.revoked_at = datetime.now(timezone.utc)
        return record


# ── Per-Key Rate Limiter ─────────────────────────────────────────────────────

class ApiKeyRateLimiter:
    """In-memory sliding-window rate limiter scoped per API key.

    For production, back with Redis for distributed rate limiting.
    """

    def __init__(self, window_seconds: int = 60):
        self._window = window_seconds
        self._keys: dict[str, list[float]] = {}

    def check_rate_limit(self, key_id: str, max_requests: int) -> tuple[bool, int]:
        """Check if an API key has exceeded its rate limit.

        Args:
            key_id: The API key identifier.
            max_requests: Maximum requests allowed in the window.

        Returns:
            Tuple of (is_allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self._window

        timestamps = self._keys.get(key_id, [])
        # Remove expired timestamps
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= max_requests:
            retry_after = max(1, int(self._window - (now - timestamps[0])))
            return False, retry_after

        timestamps.append(now)
        self._keys[key_id] = timestamps
        return True, 0

    def cleanup(self, max_age_seconds: float = 3600) -> int:
        """Remove stale entries to prevent memory leaks.

        Args:
            max_age_seconds: Remove entries older than this.

        Returns:
            Number of entries cleaned up.
        """
        cutoff = time.time() - max_age_seconds
        stale_keys = [k for k, v in self._keys.items() if not v or v[-1] < cutoff]
        for k in stale_keys:
            del self._keys[k]
        return len(stale_keys)


# ── Singleton ────────────────────────────────────────────────────────────────

_api_key_manager: ApiKeyManager | None = None
_api_key_rate_limiter: ApiKeyRateLimiter | None = None


def get_api_key_manager() -> ApiKeyManager:
    """Get the singleton ApiKeyManager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = ApiKeyManager()
    return _api_key_manager


def get_api_key_rate_limiter() -> ApiKeyRateLimiter:
    """Get the singleton ApiKeyRateLimiter instance."""
    global _api_key_rate_limiter
    if _api_key_rate_limiter is None:
        _api_key_rate_limiter = ApiKeyRateLimiter()
    return _api_key_rate_limiter
