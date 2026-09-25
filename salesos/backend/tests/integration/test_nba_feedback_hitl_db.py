"""POST /opportunities/{id}/nba/feedback records through the HITL feedback path
(PO decision B4, report 99). The former NBAEngine.record_feedback wrote columns
nba_feedback does not have (report 92) and was removed."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import async_session, engine
from app.dependencies import get_current_tenant_id, get_current_user_id, verify_token
from runtime.nba_engine.api.router import router as nba_router


async def _seed(tid: str) -> str:
    opp = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tid})
        await s.execute(text("INSERT INTO tenants (id, name, slug) VALUES (:i, 'NBA FB', :s)"),
                        {"i": tid, "s": f"nbafb-{tid[:8]}"})
        await s.execute(text("INSERT INTO companies (id, tenant_id, name_ar, name_en) "
                             "VALUES (:i, :t, 'شركة', 'Feedback Co')"), {"i": cid, "t": tid})
        await s.execute(text("INSERT INTO commercial_opportunities (id, tenant_id, company_id, name) "
                             "VALUES (:i, :t, :c, 'Deal')"), {"i": opp, "t": tid, "c": cid})
        await s.commit()
    return opp


async def _rows(tid: str):
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tid})
        return (await s.execute(text(
            "SELECT company_name, action_id::text, recommendation_id::text, seller_id, decision, "
            "original_action_type, notes FROM nba_feedback"))).mappings().all()


def test_feedback_is_recorded_through_hitl_path(monkeypatch):
    tid, seller = str(uuid.uuid4()), str(uuid.uuid4())
    opp = asyncio.run(_seed(tid))
    asyncio.run(engine.dispose())

    async def _allow(*a, **k):
        return True

    monkeypatch.setattr("app.dependencies.require_permission", _allow)
    app = FastAPI()
    app.include_router(nba_router)
    app.dependency_overrides[verify_token] = lambda: {"sub": seller, "tenant_id": tid}
    app.dependency_overrides[get_current_tenant_id] = lambda: tid
    app.dependency_overrides[get_current_user_id] = lambda: seller

    nba_id = str(uuid.uuid4())
    with TestClient(app) as c:
        ok = c.post(f"/opportunities/{opp}/nba/feedback", headers={"Authorization": "Bearer x"},
                    json={"nba_id": nba_id, "action": "dismissed",
                          "original_action_type": "send_follow_up", "reason": "bad timing"})
        missing = c.post(f"/opportunities/{uuid.uuid4()}/nba/feedback", headers={"Authorization": "Bearer x"},
                         json={"nba_id": nba_id, "action": "accepted", "original_action_type": "call"})
        cached = c.post(f"/opportunities/{opp}/nba/feedback", headers={"Authorization": "Bearer x"},
                        json={"nba_id": "cached", "action": "accepted", "original_action_type": "call"})
    asyncio.run(engine.dispose(close=False))

    assert ok.status_code == 200, ok.text
    assert missing.status_code == 404
    assert cached.status_code == 422

    rows = asyncio.run(_rows(tid))
    asyncio.run(engine.dispose())
    assert [dict(r) for r in rows] == [{
        "company_name": "Feedback Co", "action_id": nba_id, "recommendation_id": nba_id,
        "seller_id": seller, "decision": "rejected", "original_action_type": "send_follow_up",
        "notes": "bad timing",
    }]
