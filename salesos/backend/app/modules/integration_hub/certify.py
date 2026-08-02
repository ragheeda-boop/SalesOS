"""STORY-08-01 — SourceConnector certification suite (adapter-agnostic).

Any adapter that passes can be treated as interface-conformant.
Not Production GO.
"""

from __future__ import annotations

from typing import Any

from app.modules.integration_hub.source_connector import SourceConnector
from app.modules.integration_hub.types import WriteBackRequest


async def certify_source_connector(adapter: SourceConnector) -> dict[str, Any]:
    """Exercise the three mandatory methods; raise AssertionError on contract break."""
    if not isinstance(adapter, SourceConnector):
        raise AssertionError("adapter does not satisfy SourceConnector protocol")
    key = adapter.connector_key
    if not isinstance(key, str) or not key.strip():
        raise AssertionError("connector_key must be a non-empty str")

    probe = await adapter.test_connection(
        credential_ref="vault://cert/test",
        config={"mode": "certify"},
    )
    if not getattr(probe, "ok", False):
        raise AssertionError(f"test_connection failed: {getattr(probe, 'message', probe)}")

    wb = await adapter.write_back(
        credential_ref="vault://cert/test",
        config={"mode": "certify"},
        request=WriteBackRequest(
            model="cert.entity",
            payload={"name": "cert-row", "n": 1},
        ),
    )
    if not wb.ok or not wb.external_id:
        raise AssertionError(f"write_back failed: {wb}")

    first = await adapter.pull_incremental(
        credential_ref="vault://cert/test",
        config={"mode": "certify"},
        model="cert.entity",
        cursor=None,
        limit=10,
    )
    if not first.records:
        raise AssertionError("pull_incremental returned no records after write_back")
    if first.records[0].external_id != wb.external_id:
        raise AssertionError("pull_incremental did not surface write_back external_id")

    second = await adapter.pull_incremental(
        credential_ref="vault://cert/test",
        config={"mode": "certify"},
        model="cert.entity",
        cursor=first.next_cursor,
        limit=10,
    )
    if second.records and any(r.external_id == wb.external_id for r in second.records):
        raise AssertionError("cursor did not advance past already-pulled record")

    return {
        "ok": True,
        "connector_key": key,
        "external_id": wb.external_id,
        "pulled": len(first.records),
    }
