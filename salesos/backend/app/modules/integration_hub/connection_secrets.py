"""STORY-08-02 — Fernet credential helpers + connection_config hygiene.

Never store raw secrets in connection_config JSONB.
Uses existing app secret material (settings.secret_key) — does not invent keys.
Not Production GO.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sdk.security import decrypt_token, encrypt_token

# Keys forbidden inside connection_config (non-secret JSON only).
_FORBIDDEN_CONFIG_KEYS = frozenset(
    {
        "password",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "client_secret",
        "private_key",
        "credentials",
        "credential",
        "authorization",
    }
)


def assert_safe_connection_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a shallow copy of config or {} after rejecting secret-like keys."""
    if config is None:
        return {}
    if not isinstance(config, Mapping):
        raise ValueError("connection_config must be an object")
    out: dict[str, Any] = {}
    for key, value in config.items():
        k = str(key).strip()
        if k.lower() in _FORBIDDEN_CONFIG_KEYS:
            raise ValueError(
                f"connection_config must not contain secret field {k!r}; "
                "use credential_ref / credentials envelope"
            )
        out[k] = value
    return out


def normalize_credential_ref(credential_ref: str) -> str:
    ref = (credential_ref or "").strip()
    if not ref:
        raise ValueError("credential_ref is required")
    if len(ref) > 512:
        raise ValueError("credential_ref too long")
    # Pointer only — reject embedded secret material.
    lowered = ref.lower()
    if any(x in lowered for x in ("password=", "api_key=", "secret=", "token=")):
        raise ValueError("credential_ref must be a vault pointer, not raw secret material")
    if not (ref.startswith("vault://") or ref.startswith("ref://")):
        raise ValueError("credential_ref must start with vault:// or ref://")
    return ref


def encrypt_credentials_blob(secrets: Mapping[str, Any] | None, *, secret: str) -> str | None:
    """Fernet-encrypt a credentials mapping; None/empty → None stored."""
    if not secrets:
        return None
    if not isinstance(secrets, Mapping):
        raise ValueError("credentials must be an object")
    if not (secret or "").strip():
        raise ValueError("encryption secret is not configured")
    payload = json.dumps(dict(secrets), separators=(",", ":"), sort_keys=True)
    return encrypt_token(payload, secret)


def decrypt_credentials_blob(ciphertext: str | None, *, secret: str) -> dict[str, Any]:
    if not ciphertext:
        return {}
    if not (secret or "").strip():
        raise ValueError("encryption secret is not configured")
    raw = decrypt_token(ciphertext, secret)
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("decrypted credentials must be an object")
    return data
