from __future__ import annotations

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from app.config import settings
from app.modules.tenant_studio.ai_memory import AiMemoryError
from app.modules.tenant_studio.postgres_ai_memory_store import PostgresAiMemoryStore


def test_persisted_memory_encryption_hides_text_and_is_tenant_bound(monkeypatch) -> None:
    monkeypatch.setattr(
        settings, "ai_memory_encryption_key", Fernet.generate_key().decode("ascii")
    )
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    plaintext = "sensitive conversation value"

    envelope = PostgresAiMemoryStore._encrypt(tenant_a, plaintext)

    assert envelope["alg"] == "fernet-tenant-v1"
    assert plaintext not in envelope["ciphertext"]
    assert PostgresAiMemoryStore._decrypt(tenant_a, envelope) == plaintext
    with pytest.raises(AiMemoryError, match="decryption failed"):
        PostgresAiMemoryStore._decrypt(tenant_b, envelope)


def test_memory_persistence_fails_closed_without_dedicated_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_memory_encryption_key", "")

    with pytest.raises(AiMemoryError, match="encryption key is not configured"):
        PostgresAiMemoryStore._tenant_key(str(uuid4()))
