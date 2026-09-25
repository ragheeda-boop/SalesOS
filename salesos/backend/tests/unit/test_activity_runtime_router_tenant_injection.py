"""DEC-157: activity ingest-batch must never trust a client-supplied tenant_id.

Regression for a real cross-tenant injection bug found while implementing
DEC-157 GUC pinning (project-audit/59, /67): the batch endpoint used to do
``r.get("tenant_id", tenant_id)`` — a client-supplied "tenant_id" field in the
request body silently overrode the authenticated caller's tenant, letting an
authenticated tenant-A user write activity records under an arbitrary
tenant_id. The fix forces every enriched record's tenant_id to the
authenticated tenant, ignoring any body-supplied value.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dependencies import get_current_tenant_id, verify_token
from runtime.activity_runtime.router import router as activity_router


@pytest.fixture
def app_and_runtime():
    app = FastAPI()
    app.include_router(activity_router, prefix="/api/v1")
    app.dependency_overrides[verify_token] = lambda: {"sub": "u1", "tenant_id": "tenant-a"}
    app.dependency_overrides[get_current_tenant_id] = lambda: "tenant-a"

    fake_runtime = AsyncMock()

    async def _fake_ingest_batch(records):
        # Mirror ActivityRuntime.ingest_batch's return contract closely enough
        # for the router to build its response.
        class _Rec:
            def __init__(self, tenant_id):
                self.id = "rec-1"
                self.tenant_id = tenant_id

        fake_runtime.received_records = records
        return [_Rec(r.get("tenant_id")) for r in records]

    fake_runtime.ingest_batch.side_effect = _fake_ingest_batch
    app.state.activity_runtime = fake_runtime
    return app, fake_runtime


def test_ingest_batch_ignores_client_supplied_tenant_id(app_and_runtime):
    app, fake_runtime = app_and_runtime
    client = TestClient(app)

    resp = client.post(
        "/api/v1/activities/ingest-batch",
        json=[
            {
                "actor": "user-1",
                "action": "note.created",
                "entity_type": "company",
                "entity_id": "c1",
                # Attempted cross-tenant injection via the request body.
                "tenant_id": "tenant-b-victim",
            }
        ],
        headers={"Authorization": "Bearer faketoken"},
    )

    assert resp.status_code == 200
    sent_records = fake_runtime.received_records
    assert len(sent_records) == 1
    # The authenticated tenant must win — never the body-supplied value.
    assert sent_records[0]["tenant_id"] == "tenant-a"
    assert sent_records[0]["tenant_id"] != "tenant-b-victim"


def test_ingest_batch_stamps_tenant_id_even_when_absent_from_body(app_and_runtime):
    app, fake_runtime = app_and_runtime
    client = TestClient(app)

    resp = client.post(
        "/api/v1/activities/ingest-batch",
        json=[
            {
                "actor": "user-1",
                "action": "note.created",
                "entity_type": "company",
                "entity_id": "c1",
            }
        ],
        headers={"Authorization": "Bearer faketoken"},
    )

    assert resp.status_code == 200
    assert fake_runtime.received_records[0]["tenant_id"] == "tenant-a"
