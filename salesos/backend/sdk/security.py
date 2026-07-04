"""Security utilities: hashing, encryption, token management."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def create_jwt(
    payload: dict,
    secret: str,
    algorithm: str = "HS256",
    expires_minutes: int = 30,
) -> str:
    """Create a signed JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    token_payload = {**payload, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(token_payload, secret, algorithm=algorithm)


def decode_jwt(token: str, secret: str, algorithms: list[str] | None = None) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, secret, algorithms=algorithms or ["HS256"])
    except JWTError:
        raise ValueError("Invalid or expired token")


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key pair: (raw_key, key_hash)."""
    raw_key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    computed_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return hmac.compare_digest(computed_hash, key_hash)


def generate_entity_code(module: str, entity_type: str, entity_id: str) -> str:
    """Generate a universal entity identifier: MOD_ENTYPE_SHORTID."""
    short_id = entity_id.replace("-", "")[:8]
    return f"{module[:3].upper()}_{entity_type[:3].upper()}_{short_id}"


def mask_pii(value: str, visible_chars: int = 3) -> str:
    """Mask personally identifiable information."""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return value[:visible_chars] + "*" * (len(value) - visible_chars)


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)
