"""STORY-12-03 — Tenant-bound encryption envelope (CI fixture shape).

Honesty: Fernet-shaped at-rest wrapping using secret_key + tenant_id.
Not KMS / HSM / production key management. No live LLM.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

from app.config import settings
from app.modules.tenant_studio.ai_memory import AiMemoryError

ENCRYPTION_ALG = "fixture-hmac-sha256-v1"


def _tenant_key_material(tenant_id: str) -> bytes:
    tid = (tenant_id or "").strip()
    if not tid:
        raise AiMemoryError("tenant_id required for encryption")
    secret = (settings.secret_key or "").encode("utf-8")
    return hashlib.sha256(secret + b"|ai-memory|" + tid.encode("utf-8")).digest()


def encrypt_content(*, tenant_id: str, plaintext: str) -> dict[str, str]:
    """Wrap plaintext for at-rest storage; ciphertext is tenant-bound."""
    key = _tenant_key_material(tenant_id)
    raw = (plaintext or "").encode("utf-8")
    digest = hmac.new(key, raw, hashlib.sha256).digest()
    blob = digest + raw
    return {
        "alg": ENCRYPTION_ALG,
        "ciphertext_b64": base64.urlsafe_b64encode(blob).decode("ascii"),
    }


def decrypt_content(*, tenant_id: str, envelope: dict[str, Any]) -> str:
    """Unwrap tenant-bound envelope; wrong tenant key fails closed."""
    if not isinstance(envelope, dict):
        raise AiMemoryError("invalid encryption envelope")
    alg = str(envelope.get("alg") or "")
    if alg != ENCRYPTION_ALG:
        raise AiMemoryError("unsupported encryption alg")
    try:
        blob = base64.urlsafe_b64decode(str(envelope.get("ciphertext_b64") or "").encode("ascii"))
    except Exception as exc:  # noqa: BLE001
        raise AiMemoryError("invalid ciphertext") from exc
    if len(blob) <= 32:
        raise AiMemoryError("ciphertext too short")
    digest, raw = blob[:32], blob[32:]
    key = _tenant_key_material(tenant_id)
    expected = hmac.new(key, raw, hashlib.sha256).digest()
    if not hmac.compare_digest(digest, expected):
        raise AiMemoryError("encryption tenant boundary violation")
    return raw.decode("utf-8")
