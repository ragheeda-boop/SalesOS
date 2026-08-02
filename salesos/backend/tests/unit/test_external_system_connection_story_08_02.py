"""STORY-08-02 — ExternalSystemConnection Fernet + cross-tenant isolation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.modules.integration_hub.connection_secrets import (
    assert_safe_connection_config,
    decrypt_credentials_blob,
    encrypt_credentials_blob,
    normalize_credential_ref,
)
from tests.support.tenant_isolation import (
    CrossTenantIsolationViolation,
    assert_cross_tenant_read_blocked,
)

_TEST_SECRET = "unit-test-fernet-material-not-for-production"


def test_connection_config_rejects_secret_keys() -> None:
    assert assert_safe_connection_config({"base_url": "https://example.test"}) == {
        "base_url": "https://example.test"
    }
    with pytest.raises(ValueError, match="secret field"):
        assert_safe_connection_config({"api_key": "nope"})


def test_credential_ref_pointer_rules() -> None:
    assert normalize_credential_ref("vault://t/conn/1").startswith("vault://")
    with pytest.raises(ValueError, match="vault://"):
        normalize_credential_ref("plain-string")
    with pytest.raises(ValueError, match="raw secret"):
        normalize_credential_ref("vault://x?password=hunter2")


def test_fernet_credentials_roundtrip() -> None:
    blob = encrypt_credentials_blob({"token": "abc"}, secret=_TEST_SECRET)
    assert blob and "abc" not in blob
    assert decrypt_credentials_blob(blob, secret=_TEST_SECRET) == {"token": "abc"}


@dataclass
class _MemConn:
    id: uuid.UUID
    tenant_id: uuid.UUID
    connector_key: str
    name: str
    credential_ref: str
    credentials_encrypted: str | None = None
    connection_config: dict[str, Any] = field(default_factory=dict)


class _MemConnectionStore:
    """App-layer stand-in for tenant-scoped get (STORY-01-04 template)."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, _MemConn] = {}

    async def create(self, tenant_id: str) -> uuid.UUID:
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id)
        cid = uuid.uuid4()
        enc = encrypt_credentials_blob({"x": "1"}, secret=_TEST_SECRET)
        self.rows[cid] = _MemConn(
            id=cid,
            tenant_id=tid,
            connector_key="fake",
            name="mem",
            credential_ref=f"vault://{tenant_id}/c/{cid}",
            credentials_encrypted=enc,
            connection_config={"env": "test"},
        )
        return cid

    async def get(self, key: uuid.UUID, tenant_id: str) -> _MemConn | None:
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id)
        row = self.rows.get(key)
        if row is None or row.tenant_id != tid:
            return None
        return row


@pytest.mark.asyncio
async def test_cross_tenant_connection_read_blocked() -> None:
    store = _MemConnectionStore()
    await assert_cross_tenant_read_blocked(
        create_as=store.create,
        read_as=store.get,
        tenant_a="tenant-a",
        tenant_b="tenant-b",
    )


@pytest.mark.asyncio
async def test_cross_tenant_leak_raises_security_error() -> None:
    store = _MemConnectionStore()

    async def leaky_get(key: uuid.UUID, tenant_id: str) -> _MemConn | None:
        return store.rows.get(key)

    with pytest.raises(CrossTenantIsolationViolation):
        await assert_cross_tenant_read_blocked(
            create_as=store.create,
            read_as=leaky_get,
            tenant_a="tenant-a",
            tenant_b="tenant-b",
        )
