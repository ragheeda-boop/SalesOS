"""Grounded Research Phase 1 — evidence retrieval, grounding guards, PII policy.

Unit-level coverage using fakes; live DB/tenant-isolation probes are run
separately against the local stack (see validation report).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from intelligence.agents.base import AgentTask
from intelligence.agents.research import (
    GROUNDING_SYSTEM_PROMPT,
    ResearchAgent,
    _parse_research_json,
)
from intelligence.agents.research_evidence import (
    EvidenceItem,
    EvidencePack,
    contact_metadata_items,
    value_band,
)

TENANT = "a0000000-0000-4000-a000-000000000001"
CID_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
CID_C = "e91b3d62-5342-4364-847e-bc6e7cf8af97"

GOOD_JSON = json.dumps(
    {
        "company_summary": "Grounded summary citing [E1].",
        "industry": {"value": None, "basis": "unknown"},
        "business_signals": [],
        "commercial_context": [
            {"fact": "one open deal at prospecting stage", "evidence_id": "E4", "basis": "source"}
        ],
        "opportunities": [],
        "risks": [],
        "recommendations": [],
        "confidence": "medium",
        "missing_information": ["industry"],
    }
)


class FakeLLM:
    def __init__(self, content=GOOD_JSON):
        self.content = content
        self.calls = []
        # legacy research path only calls services exposing .client
        self.client = object()

    async def chat(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=self.content)


def _rich_pack() -> EvidencePack:
    pack = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=True)
    for f, v in [("status", "active"), ("city", "الرياض")]:
        pack.add(EvidenceItem("company", CID_A, f, v))
    pack.add(EvidenceItem("opportunity", "opp-1", "stage", "prospecting"))
    pack.add(EvidenceItem("contact_metadata", None, "positions", "ceo"))
    return pack


def _task(**extra):
    base = {
        "company_id": CID_A,
        "tenant_id": TENANT,
        "topic": "analyze",
        "goal": "research",
    }
    base.update(extra)
    return AgentTask(id="t", agent_type="research", input=base)


# ── 1+2. Retrieval wiring ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_loader_receives_tenant_and_company_ids():
    seen = {}

    async def loader(tenant_id, company_id):
        seen.update(t=tenant_id, c=company_id)
        return _rich_pack()

    llm = FakeLLM()
    await ResearchAgent(llm, evidence_loader=loader).execute(_task())
    assert seen == {"t": TENANT, "c": CID_A}
    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_grounded_prompt_contains_evidence_and_subject():
    llm = FakeLLM()
    result = await ResearchAgent(llm, evidence_loader=_async_loader()).execute(_task())
    user_prompt = llm.calls[0]["messages"][0]["content"]
    assert "[E1]" in user_prompt and "[E3]" in user_prompt
    assert CID_A in llm.calls[0]["system"]
    assert "stage = prospecting" in user_prompt


def _async_loader():
    async def loader(tenant_id, company_id):
        return _rich_pack()

    return loader


# ── 3. Evidence construction helpers ───────────────────────────────


def test_contact_metadata_strips_pii():
    rows = [
        SimpleNamespace(
            position="CEO", position_ar=None, department="Sales", is_primary=True
        ),
        SimpleNamespace(position="مدير", position_ar=None, department=None, is_primary=False),
    ]
    items = {i.field: i.value for i in contact_metadata_items(rows)}
    assert items["contacts_total"] == "2"
    assert items["primary_contacts"] == "1"
    assert "CEO" in items["positions"] and "مدير" in items["positions"]


def test_pii_fields_never_reach_prompt_block():
    pack = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=True)
    for it in contact_metadata_items(
        [SimpleNamespace(position="ceo", department=None, is_primary=True)]
    ):
        pack.add(it)
    block = pack.to_prompt_block()
    for banned in ("email", "phone", "@", "hattan", "rea@mnb"):
        assert banned.lower() not in block.lower()


def test_value_banding_hides_exact_amount():
    assert value_band(1_000_000) == "100K-1M"
    assert value_band(50_000) == "<100K"
    assert value_band(5_000_000) == ">1M"
    assert value_band(None) == "unknown"


def test_loader_pins_tenant_guc_dec085():
    """RLS is fail-closed; the evidence loader MUST pin app.tenant_id or it
    sees nothing (and any future 'fix' that removes this fails closed again)."""
    import inspect

    from intelligence.agents import research_evidence as re_mod

    src = inspect.getsource(re_mod.build_company_evidence)
    assert "set_config" in src and "app.tenant_id" in src


def test_loader_uses_audit_store_and_real_signal_columns():
    """Timeline evidence must come from audit.audit_log (via AuditTrail — the
    store /360 renders), and the signals query must reference columns that
    actually exist (signal_type/severity/status/confidence_score)."""
    import inspect

    from intelligence.agents import research_evidence as re_mod

    src = inspect.getsource(re_mod.build_company_evidence)
    assert "AuditTrail" in src and "audit" in src.lower()
    assert "severity" in src and "confidence_score" in src
    assert "strength" not in src  # column never existed; was a live bug


# ── 4+8. Missing data / entity identity ────────────────────────────


@pytest.mark.asyncio
async def test_insufficient_evidence_short_circuits_without_llm():
    llm = FakeLLM()

    async def loader(tenant_id, company_id):
        return EvidencePack(
            tenant_id=tenant_id,
            company_id=company_id,
            found=False,
            missing_data=["company_record_not_found_for_tenant"],
        )

    result = await ResearchAgent(llm, evidence_loader=loader).execute(
        _task(company_id=CID_C)
    )
    assert llm.calls == []
    assert result.output["summary"].startswith("INSUFFICIENT EVIDENCE")
    assert result.output["research_depth"] == "grounded_no_evidence"
    assert "company_record_not_found_for_tenant" in result.output["research"]["missing_information"]


@pytest.mark.asyncio
async def test_invalid_company_uuid_short_circuits():
    llm = FakeLLM()
    called = {"n": 0}

    from intelligence.agents.research_evidence import build_company_evidence

    class NeverSession:
        def __call__(self):
            called["n"] += 1
            raise AssertionError("DB must not be opened for an invalid UUID")

    pack = await build_company_evidence(NeverSession(), TENANT, "not-a-uuid")
    assert pack.found is False
    assert "company_or_tenant_id_not_valid_uuid" in pack.missing_data


# ── 5. Tenant identity flows through ───────────────────────────────


@pytest.mark.asyncio
async def test_wrong_tenant_arg_changes_loader_scope():
    other_tenant = "b0000000-0000-4000-a000-000000000002"
    seen = {}

    async def loader(tenant_id, company_id):
        seen["t"] = tenant_id
        return _rich_pack()

    await ResearchAgent(FakeLLM(), evidence_loader=loader).execute(
        _task(tenant_id=other_tenant)
    )
    assert seen["t"] == other_tenant


# ── 6+7. Grounding guards ──────────────────────────────────────────


def test_system_prompt_contains_grounding_rules():
    p = GROUNDING_SYSTEM_PROMPT.format(company_id="X")
    for marker in ("ONLY facts", "Never infer", "UNKNOWN", "SOURCE", "DERIVED", "INFERENCE", "[E3]"):
        assert marker in p


@pytest.mark.asyncio
async def test_structured_output_contract_complete():
    result = await ResearchAgent(FakeLLM(), evidence_loader=_async_loader()).execute(_task())
    r = result.output["research"]
    for key in (
        "company_summary", "industry", "business_signals", "commercial_context",
        "opportunities", "risks", "recommendations", "confidence", "missing_information",
    ):
        assert key in r
    assert result.output["research_depth"] == "grounded"
    assert result.output["metrics"]["evidence_count"] == 4
    assert result.confidence == 0.7  # medium mapping


@pytest.mark.asyncio
async def test_degraded_parse_is_honest_not_fabricated():
    result = await ResearchAgent(
        FakeLLM(content="```json\n{broken json"), evidence_loader=_async_loader()
    ).execute(_task())
    r = result.output["research"]
    assert r["parse_quality"] == "degraded_raw_text"
    assert r["industry"]["basis"] == "unknown"
    assert "{broken json" in r["company_summary"] or "broken" in r["company_summary"]


# ── Legacy behaviour preserved (regression guard) ──────────────────


@pytest.mark.asyncio
async def test_legacy_path_unchanged_without_loader():
    legacy = FakeLLM(content="تحليل تقليدي")
    result = await ResearchAgent(legacy).execute(_task())
    assert result.output["research_depth"] == "llm"
    assert "الاسم:" in legacy.calls[0]["messages"][0]["content"]
    assert legacy.calls[0]["messages"][0]["content"].count(CID_A) == 0


@pytest.mark.asyncio
async def test_legacy_minimal_fallback_without_llm():
    result = await ResearchAgent(None).execute(_task())
    assert result.output["research_depth"] == "minimal"


@pytest.mark.asyncio
async def test_loader_absent_ids_keep_legacy_path():
    llm = FakeLLM()

    async def loader(t, c):  # must never be reached
        raise AssertionError("loader requires tenant+company ids")

    result = await ResearchAgent(llm, evidence_loader=loader).execute(
        _task(company_id="", tenant_id=None)
    )
    assert result.output["research_depth"] == "llm"
