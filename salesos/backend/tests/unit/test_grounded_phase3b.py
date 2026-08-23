"""Grounded Phase 3B tests — forecast/pricing/proposal/renewal/tender/
meeting/news/contract over the canonical EvidencePack.

Contracts under test:
- deterministic outputs (zero LLM) built ONLY from pack facts with [E#] citations
- honest INSUFFICIENT/UNKNOWN degradation for data-gap agents
- entity identity = company_id only; caller-supplied misleading names ignored
- legacy paths preserved when no loader injected
"""

import asyncio

import pytest

from intelligence.agents.base import AgentTask
from intelligence.agents.contract import ContractAgent, build_contract_context
from intelligence.agents.forecast import ForecastAgent, build_forecast
from intelligence.agents.grounded_common import index_pack, opportunities_from
from intelligence.agents.meeting import MeetingAgent, build_meeting_brief
from intelligence.agents.news import NewsAgent, build_news_context
from intelligence.agents.pricing import PricingAgent, build_pricing_context
from intelligence.agents.proposal import ProposalAgent, build_proposal_readiness
from intelligence.agents.renewal import RenewalAgent, build_renewal_view
from intelligence.agents.research_evidence import (
    BASIS_SOURCE,
    EvidenceItem,
    EvidencePack,
)
from intelligence.agents.tender import TenderAgent, build_tender_context

TENANT_A = "a0000000-0000-4000-a000-000000000001"
TENANT_B = "b0000000-0000-4000-a000-000000000002"
CID_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
OTHER_TENANT_NAME = "Curl Search Co"  # must NEVER appear in grounded outputs


def rich_pack() -> EvidencePack:
    p = EvidencePack(tenant_id=TENANT_A, company_id=CID_A, found=True)
    items = [
        ("company", "status", "active"),
        ("company", "city", "Riyadh"),
        ("company", "industry", "technology"),
        ("company", "legal_form", "LLC"),
        ("company", "cr_type", "main"),
        ("opportunity", "name", "ERP expansion"),
        ("opportunity", "stage", "proposal"),
        ("opportunity", "status", "open"),
        ("opportunity", "probability", "60%"),
        ("opportunity", "value_band", "100K-1M"),
        ("contact_metadata", "contacts_total", "2"),
        ("contact_metadata", "positions", "IT Manager, Procurement Officer"),
    ]
    kinds = {
        "opportunity": "opp-1",
        "company": "cid",
    }
    for st, f, v in items:
        p.add(EvidenceItem(st, kinds.get(st), f, v, basis=BASIS_SOURCE))
    return p


def empty_pack(found: bool = False) -> EvidencePack:
    p = EvidencePack(tenant_id=TENANT_A, company_id=CID_A, found=found)
    if found:
        p.add(EvidenceItem("company", "cid", "status", "active"))
    return p


def _async_loader(pack):
    async def _load(tenant_id, company_id):
        assert isinstance(tenant_id, str) and isinstance(company_id, str)
        return pack

    return _load


def _task(**extra):
    payload = {"company_id": CID_A, "tenant_id": TENANT_A}
    payload.update(extra)
    return AgentTask(id="t", agent_type="x", input=payload)


def _no_leak(blob: str) -> None:
    assert "@" not in blob
    assert OTHER_TENANT_NAME not in blob


ALL_BUILDERS = [
    build_forecast,
    build_pricing_context,
    build_proposal_readiness,
    build_renewal_view,
    build_tender_context,
    build_meeting_brief,
    build_news_context,
    build_contract_context,
]


# ── shared contracts across all eight agents ────────────────────────────


@pytest.mark.parametrize("builder", ALL_BUILDERS, ids=lambda b: b.__name__)
def test_empty_pack_is_insufficient(builder):
    out = builder(empty_pack(found=False))
    assert out["status"] == "INSUFFICIENT_EVIDENCE"
    assert out["company_id"] == CID_A
    assert out.get("recommendations", []) == []
    _no_leak(str(out))


@pytest.mark.parametrize("builder", ALL_BUILDERS, ids=lambda b: b.__name__)
def test_rich_pack_output_has_metrics_and_no_llm(builder):
    out = builder(rich_pack())
    m = out["metrics"]
    assert m["llm_called"] is False
    assert m["evidence_count"] == len(rich_pack().items)
    assert "found" in m
    _no_leak(str(out))


# ── forecast ────────────────────────────────────────────────────────────


def test_forecast_reads_real_pipeline_with_citations():
    out = build_forecast(rich_pack())
    fc = out["forecast"]
    assert out["status"] == "OK"
    assert fc["total_count"] == 1
    assert fc["by_stage"][0]["stage"] == "proposal"
    assert fc["observed_value_bands"] == [{"band": "100K-1M", "count": 1}]
    deal = fc["deals"][0]
    assert set(deal["evidence"]) <= {f"E{i}" for i in range(1, 13)}
    assert any(e.startswith("E") for e in deal["evidence"])
    assert "confidentiality-banded" in out["limitations"][0]


def test_forecast_no_opportunities_is_insufficient():
    p = empty_pack(found=True)  # company exists, zero deals
    out = build_forecast(p)
    assert out["status"] == "INSUFFICIENT_EVIDENCE"
    assert "opportunities" in out["missing_information"]


# ── pricing / renewal / tender / news / contract (data-gap honesty) ─────


def test_pricing_reports_bands_only_status_unknown():
    out = build_pricing_context(rich_pack())
    assert out["pricing_status"] == "UNKNOWN"
    bands = out["context_only"]["observed_deal_bands"]
    assert bands and bands[0]["band"] == "100K-1M" and bands[0]["evidence"]
    assert "pricing_records" in out["missing_information"]


def test_renewal_never_invents_contract_data():
    out = build_renewal_view(rich_pack())
    assert out["renewal_status"] == "UNKNOWN"
    assert out["recommendations"] == []
    assert "renewal_dates" in out["missing_information"]
    assert "UNASSESSABLE" in out["risks"][0]


def test_tender_gives_legal_context_only():
    out = build_tender_context(rich_pack())
    assert out["tender_status"] == "UNKNOWN"
    fields = {f["field"] for f in out["eligibility_context_only"]["fields"]}
    assert {"cr_type", "legal_form"} <= fields
    assert all(f["evidence"] for f in out["eligibility_context_only"]["fields"])
    assert "tender_records" in out["missing_information"]


def test_news_returns_zero_fabricated_articles():
    out = build_news_context(rich_pack())
    assert out["news_status"] == "UNKNOWN"
    assert out["articles"] == []
    assert "news_corpus" in out["missing_information"]
    assert "not news evidence" in out["entity_context_only"]["note"]


def test_contract_legal_context_only():
    out = build_contract_context(rich_pack())
    assert out["contract_status"] == "UNKNOWN"
    fields = {f["field"]: f["evidence"] for f in out["entity_legal_context_only"]["fields"]}
    assert fields["legal_form"] and fields["cr_type"]
    assert "contracts" in out["missing_information"]


# ── proposal readiness gate ─────────────────────────────────────────────


def test_proposal_ready_requires_late_stage_and_primary():
    out = build_proposal_readiness(rich_pack())
    # late stage PASS but no primary contact → NOT_READY with next action
    checks = {c["check"]: c for c in out["checks"]}
    assert checks["late_stage"]["result"] == "PASS"
    assert checks["primary_contact"]["result"] == "FAIL"
    assert out["readiness"] == "NOT_READY"
    assert any("primary business contact" in a["action"] for a in out["next_actions"])


def test_proposal_blocked_without_pipeline():
    p = empty_pack(found=True)
    out = build_proposal_readiness(p)
    assert out["readiness"] == "BLOCKED_NO_PIPELINE"


# ── meeting brief ───────────────────────────────────────────────────────


def test_meeting_brief_roles_are_metadata_only_with_agenda():
    out = build_meeting_brief(rich_pack())
    br = out["brief"]
    roles = [r["role"] for r in br["attendee_roles"]]
    assert roles == ["IT Manager, Procurement Officer"]
    blob = str(out)
    assert "@" not in blob  # PII never present
    agenda_ev = [e for a in out["agenda"] for e in a["evidence"]]
    assert agenda_ev, "agenda items must cite evidence when facts exist"
    # late-stage deal → qualification replaced by advance action
    assert any("Advance" in a["item"] for a in out["agenda"])


# ── helpers sanity ──────────────────────────────────────────────────────


def test_index_and_group_helpers_consistent():
    p = rich_pack()
    idx = index_pack(p)
    deals = opportunities_from(p, idx)
    assert len(deals) == 1
    d = deals[0]
    assert d["stage"]["value"] == "proposal"
    assert d["value_band"]["value"] == "100K-1M"


# ── agent-level behaviour: loader wiring, identity, legacy preservation ──


@pytest.mark.asyncio
async def test_agent_grounding_ignores_caller_supplied_name():
    seen = {}

    async def loader(tenant_id, company_id):
        seen["ids"] = (tenant_id, company_id)
        return rich_pack()

    result = await ForecastAgent(None, evidence_loader=loader).execute(
        _task(company_name=OTHER_TENANT_NAME)
    )
    assert seen["ids"] == (TENANT_A, CID_A)
    _no_leak(str(result.output))


@pytest.mark.asyncio
async def test_loader_exception_degrades_not_crashes():
    async def boom(tenant_id, company_id):
        raise RuntimeError("db down")

    for agent_cls in (ForecastAgent, ProposalAgent, RenewalAgent):
        r = await agent_cls(None, evidence_loader=boom).execute(_task())
        assert r.success is True or r.output  # honest fallback output, no crash


def _legacy_task():
    return AgentTask(id="t2", agent_type="x", input={"company_id": CID_A})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_cls",
    [ForecastAgent, PricingAgent, ProposalAgent, RenewalAgent, TenderAgent,
     MeetingAgent, NewsAgent, ContractAgent],
)
async def test_legacy_path_preserved_without_loader(agent_cls):
    r = await agent_cls(None).execute(_legacy_task())
    blob = str(r.output)
    # original Arabic stub messages retained verbatim
    assert ("يتطلب تكوين مفتاح OpenAI" in blob) or ("بيانات الأنابيب" in blob)


@pytest.mark.asyncio
async def test_tender_legacy_gate_does_not_need_client_attr():
    class FakeLLM:  # deliberately NO .client attribute (F1-5 contract)

        async def chat(self, **kw):
            class R:
                content = "ok"

            return R()

    r = await TenderAgent(FakeLLM()).execute(_legacy_task())
    assert r.output == {"analysis": "ok"}
