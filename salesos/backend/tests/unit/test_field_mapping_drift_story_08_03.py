"""STORY-08-03 — FieldMappingConfig drift detection (rename alerts loudly)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.modules.integration_hub.drift_job import run_field_drift_job
from app.modules.integration_hub.field_mapping import (
    detect_field_drift,
    parse_field_mappings,
)
from tests.support.tenant_isolation import assert_cross_tenant_read_blocked


def test_parse_and_missing_mapped_field() -> None:
    maps = parse_field_mappings(
        [{"internal": "name", "external": "display_name", "direction": "pull"}]
    )
    # Empty remote → pure missing (not rename heuristic: missing+one-new).
    alerts = detect_field_drift(
        mappings=maps,
        remote_schema={},
        baseline_fields={"display_name"},
    )
    assert any(a.kind == "missing_mapped_field" and a.severity == "critical" for a in alerts)
    assert any("DRIFT ALERT" in a.message for a in alerts)


def test_simulated_field_rename_alerts_loudly() -> None:
    """Acceptance: drift job alerts loudly on a simulated field rename."""
    mappings = [
        {"internal": "name", "external": "display_name", "direction": "pull"},
        {"internal": "email", "external": "email_from", "direction": "pull"},
    ]
    # Remote renamed display_name → name_full; email_from intact.
    remote = {
        "name_full": {"type": "char"},
        "email_from": {"type": "char"},
    }
    result = run_field_drift_job(
        model="ext.partner",
        mappings=mappings,
        remote_schema=remote,
        baseline_fields={"display_name", "email_from"},
        connection_id="conn-demo",
    )
    assert result.status == "alert"
    assert result.critical_count >= 1
    rename = [a for a in result.alerts if a.kind == "possible_rename"]
    assert rename, result.to_dict()
    assert rename[0].severity == "critical"
    assert "DRIFT ALERT" in rename[0].message
    assert "RENAME" in rename[0].message
    assert rename[0].candidate_external == "name_full"
    assert "display_name" in (rename[0].external_field or "")


def test_no_drift_when_schema_matches() -> None:
    mappings = [{"internal": "name", "external": "display_name"}]
    result = run_field_drift_job(
        model="ext.partner",
        mappings=mappings,
        remote_schema={"display_name": {"type": "char"}},
        baseline_fields={"display_name"},
    )
    assert result.status == "ok"
    assert result.critical_count == 0


@dataclass
class _MemMap:
    id: uuid.UUID
    tenant_id: uuid.UUID
    connection_id: uuid.UUID
    model: str
    mappings: list[dict[str, Any]] = field(default_factory=list)


class _MemMappingStore:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, _MemMap] = {}

    async def create(self, tenant_id: str) -> uuid.UUID:
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id)
        mid = uuid.uuid4()
        self.rows[mid] = _MemMap(
            id=mid,
            tenant_id=tid,
            connection_id=uuid.uuid4(),
            model="ext.partner",
            mappings=[{"internal": "name", "external": "display_name"}],
        )
        return mid

    async def get(self, key: uuid.UUID, tenant_id: str) -> _MemMap | None:
        tid = uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id)
        row = self.rows.get(key)
        if row is None or row.tenant_id != tid:
            return None
        return row


@pytest.mark.asyncio
async def test_field_mapping_cross_tenant_read_blocked() -> None:
    store = _MemMappingStore()
    await assert_cross_tenant_read_blocked(
        create_as=store.create,
        read_as=store.get,
        tenant_a="tenant-a",
        tenant_b="tenant-b",
    )
