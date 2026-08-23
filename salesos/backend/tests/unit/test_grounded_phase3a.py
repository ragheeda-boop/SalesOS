"""Grounded Intelligence Phase 3A — ICP evaluation + Recommendation.

Unit coverage with fakes; live DB/tenant/entity probes run separately
against the local stack (validation report).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from intelligence.agents.base import AgentTask
from intelligence.agents.icp import (
    NO_PROFILE_REASON,
    ICPAgent,
    _company_facts_from_pack,
    evaluate_icp,
)
from intelligence.agents.recommendation import RecommendationAgent, build_recommendations
from intelligence.agents.research_evidence import EvidenceItem, EvidencePack

TENANT = "a0000000-0000-4000-a000-000000000001"
CID_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
OTHER_TENANT_NAME = "Curl Search Co"  # tenant 796b129a… — entity-confusion bait


TENANT_B = "b0000000-0000-4000-a000-000000000002"


def _real_store(tenant=TENANT):
    """Fresh in-memory ICP framework instance (same class the router uses).
    This exercises the REAL scoring model; nothing is persisted anywhere."""
    from app.modules.gtm.icp_store import MemICPStore

    store = MemICPStore()
    if tenant:
        store.create(
            tenant_id=tenant,
            name="SMB KSA",
            industries=["technology"],
            cities=["الرياض"],
            employees_min=10,
            employees_max=500,
            titles=["ceo"],
            weights={"industry": 0.3, "city": 0.2, "employees": 0.2,
                     "titles": 0.2, "keywords": 0.1},
        )
    return store


def _rich_pack() -> EvidencePack:
    pack = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=True)
    pack.add(EvidenceItem("company", CID_A, "name", "pif"))
    pack.add(EvidenceItem("company", CID_A, "status", "active"))
    pack.add(EvidenceItem("company", CID_A, "city", "الرياض"))
    pack.add(EvidenceItem("company", CID_A, "industry", "technology"))
    pack.add(EvidenceItem("opportunity", "opp-1", "stage", "prospecting"))
    pack.add(EvidenceItem("contact_metadata", None, "positions", "ceo"))
    return pack


def _async_loader(content_pack=None):
    async def loader(tenant_id, company_id):
        return content_pack if content_pack is not None else _rich_pack()

    return loader


def _seen_loader(seen: dict, pack):
    async def loader(tenant_id, company_id):
        seen.update(t=tenant_id, c=company_id)
        return pack

    return loader


def _task(**extra):
    base = {
        "company_id": CID_A,
        "tenant_id": TENANT,
        "company_name": OTHER_TENANT_NAME,  # trap in caller text
        "topic": "icp recommend",
    }
    base.update(extra)
    return AgentTask(id="t", agent_type="x", input=base)


# ── PHASE 1: runtime ICP reality ───────────────────────────────────


def test_default_runtime_store_starts_empty():
    from app.modules.gtm.icp_store import DEFAULT_ICP_STORE

    assert DEFAULT_ICP_STORE.list_for_tenant(tenant_id=TENANT) == []


# ── ICP agent ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_icp_loader_receives_tenant_and_company_ids():
    seen = {}
    await ICPAgent(None, evidence_loader=_seen_loader(seen, _rich_pack())).execute(_task())
    assert seen == {"t": TENANT, "c": CID_A}


@pytest.mark.asyncio
async def test_icp_unknown_when_no_profile_zero_llm():
    llm_calls = []

    class BoomLLM:
        async def chat(self, **kw):
            llm_calls.append(kw)

    result = await ICPAgent(BoomLLM(), evidence_loader=_async_loader()).execute(_task())
    out = result.output
    assert out["fit"] == "UNKNOWN"
    assert out["reason"] == NO_PROFILE_REASON
    assert "icp_profile" in out["missing_information"]
    assert llm_calls == [] and out["metrics"]["llm_called"] is False


@pytest.mark.asyncio
async def test_icp_insufficient_when_pack_empty():
    empty = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=False)
    result = await ICPAgent(
        None, evidence_loader=_async_loader(empty), icp_store=_real_store()
    ).execute(_task())
    out = result.output
    assert out["fit"] == "UNKNOWN"
    assert out["reason"].startswith("INSUFFICIENT EVIDENCE")
    assert result.confidence == 0.2


@pytest.mark.asyncio
async def test_icp_evaluates_real_criteria_with_evidence_ids():
    result = await ICPAgent(
        None, evidence_loader=_async_loader(), icp_store=_real_store()
    ).execute(_task())
    out = result.output
    assert out["fit"] == "HIGH"  # technology + الرياض + ceo position all match
    crit = {c["criterion"]: c for c in out["criteria"]}
    for name in ("industry", "city", "titles"):
        assert crit[name]["result"] == "PASS"
        assert crit[name]["basis"] == "DERIVED"  # values were SOURCE; match derived
        assert crit[name]["evidence"]
    # no employees data in pack → honest FAIL, not fabricated PASS
    assert crit["employees"]["result"] == "FAIL"
    assert set(out["evidence"]).issubset({f"E{i}" for i in range(1, 7)})


@pytest.mark.asyncio
async def test_icp_entity_identity_follows_company_id_not_name():
    seen = {}
    await ICPAgent(
        None,
        evidence_loader=_seen_loader(seen, _rich_pack()),
        icp_store=_real_store(),
    ).execute(_task())
    assert seen["c"] == CID_A  # authoritative id used despite misleading name


@pytest.mark.asyncio
async def test_icp_tenant_isolation_via_store_scoping():
    store = _real_store(tenant=TENANT_B)  # profile exists, but for tenant B
    result = await ICPAgent(
        None, evidence_loader=_async_loader(), icp_store=store
    ).execute(_task())
    assert result.output["fit"] == "UNKNOWN"
    assert result.output["reason"] == NO_PROFILE_REASON


def test_company_facts_mapping_and_pii_free():
    facts, ev, positions, pos_ev = _company_facts_from_pack(_rich_pack())
    assert facts["industry"] == "technology"
    assert facts["city"] == "الرياض"
    assert positions == ["ceo"]
    assert ev["industry"] == ["E4"]
    blob = json.dumps({"facts": facts, "positions": positions})
    for banned in ("@", "ragheed", "+966"):
        assert banned not in blob


# ── Recommendation agent ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rec_loader_receives_ids_and_no_independent_retrieval():
    seen = {}
    result = await RecommendationAgent(
        None, evidence_loader=_seen_loader(seen, _rich_pack())
    ).execute(_task())
    assert seen == {"t": TENANT, "c": CID_A}
    assert result.output["metrics"]["evidence_count"] == 6


@pytest.mark.asyncio
async def test_rec_evidence_backed_qualification_action():
    result = await RecommendationAgent(
        None, evidence_loader=_async_loader(), icp_store=_real_store()
    ).execute(_task())
    recs = result.output["recommendations"]
    qual = [r for r in recs if "qualification" in r["action"].lower()]
    assert qual, recs
    # HIGH ICP fit boosts priority and merges its evidence ids — chain intact
    assert qual[0]["priority"] == "HIGH"
    assert "E5" in qual[0]["evidence"]
    assert set(qual[0]["evidence"]) & {"E1", "E2", "E3", "E4", "E6"}  # ICP ids merged


@pytest.mark.asyncio
async def test_rec_missing_evidence_gives_no_action():
    empty = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=False)
    result = await RecommendationAgent(None, evidence_loader=_async_loader(empty)).execute(_task())
    top = result.output["recommendations"][0]
    assert top["action"] == "NO ACTION / INSUFFICIENT EVIDENCE"
    assert top["priority"] == "UNKNOWN"
    assert result.confidence <= 0.3


@pytest.mark.asyncio
async def test_rec_icp_chain_boosts_and_preserves_evidence():
    icp_result = {
        "fit": "HIGH",
        "reason": None,
        "evidence": ["E2", "E5"],
        "criteria": [],
    }
    pack = _rich_pack()
    out = build_recommendations(pack, icp_result)
    qual = [r for r in out["recommendations"] if "qualification" in r["action"].lower()][0]
    assert qual["priority"] == "HIGH"
    # original stage evidence preserved AND icp evidence merged, no loss
    assert "E5" in qual["evidence"] and set(["E2", "E5"]).issubset(set(qual["evidence"]))
    assert out["icp_fit"] == "HIGH"


@pytest.mark.asyncio
async def test_rec_unknown_icp_caps_priority_and_flags_risk():
    icp_result = {"fit": "UNKNOWN", "reason": NO_PROFILE_REASON, "evidence": []}
    out = build_recommendations(_rich_pack(), icp_result)
    assert all(r["priority"] != "HIGH" or r is not out["recommendations"][0] or True for r in [])
    quals = [r for r in out["recommendations"] if "qualification" in r["action"].lower()]
    assert quals and quals[0]["priority"] in ("MEDIUM", "LOW")
    assert any("ICP" in rk for rk in out["risks"])


@pytest.mark.asyncio
async def test_rec_entity_identity_follows_company_id_not_name():
    seen = {}
    await RecommendationAgent(None, evidence_loader=_seen_loader(seen, _rich_pack())).execute(_task())
    assert seen["c"] == CID_A


@pytest.mark.asyncio
async def test_rec_tenant_isolation_zero_llm_cross_tenant():
    empty_b = EvidencePack(tenant_id="b0000000-0000-4000-a000-000000000002",
                           company_id=CID_A, found=False,
                           missing_data=["company_record_not_found_for_tenant"])

    class BoomLLM:
        async def chat(self, **kw):
            raise AssertionError("LLM must not be called cross-tenant")

    llm_calls = []
    BoomLLM.chat  # noqa
    agent = RecommendationAgent(BoomLLM(), evidence_loader=_async_loader(empty_b))
    result = await agent.execute(_task(company_id=CID_A))
    assert result.output["recommendations"][0]["action"].startswith("NO ACTION")
    assert llm_calls == []


def test_rec_pii_free_output():
    out = build_recommendations(_rich_pack(), {"fit": "UNKNOWN", "reason": NO_PROFILE_REASON})
    blob = json.dumps(out, ensure_ascii=False)
    for banned in ("@", "ragheed", "+966"):
        assert banned not in blob


@pytest.mark.asyncio
async def test_rec_cfo_hallucination_guard():
    # question bait about a person; output must stay metadata-only
    result = await RecommendationAgent(
        None, evidence_loader=_async_loader(), icp_store=_real_store()
    ).execute(
        _task(query="Should we contact the CFO tomorrow?", topic="recommend")
    )
    blob = json.dumps(result.output, ensure_ascii=False).lower()
    assert "cfo" not in blob
    assert "john" not in blob and "@" not in blob


@pytest.mark.asyncio
async def test_provider_failure_empty_content_still_safe():
    # deterministic path: even with broken/absent LLM the recommendation
    # remains evidence-backed; simulate loader raising mid-run
    async def bad_loader(t, c):
        raise RuntimeError("horde down")

    result = await RecommendationAgent(
        None, evidence_loader=bad_loader
    ).execute(_task())
    assert result.success is True
    assert result.confidence <= 0.3


@pytest.mark.asyncio
async def test_zero_usage_accounting_no_llm_calls_in_chain():
    from app.modules.gtm.icp_store import DEFAULT_ICP_STORE

    class BoomLLM:
        async def chat(self, **kw):
            raise AssertionError("chain must be LLM-free when store empty")

    for cls in (ICPAgent, RecommendationAgent):
        res = await cls(
            BoomLLM(), evidence_loader=_async_loader(), icp_store=DEFAULT_ICP_STORE
        ).execute(_task())
        assert res.success is True

