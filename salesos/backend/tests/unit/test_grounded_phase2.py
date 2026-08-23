"""Grounded Intelligence Phase 2 — Competitor + Relationship grounding.

Unit-level coverage using fakes; live DB/tenant-isolation/entity-confusion
probes are run separately against the local stack (validation report).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from intelligence.agents.base import AgentTask
from intelligence.agents.competitor import (
    CompetitorAgent,
    _parse_competitor_json,
)
from intelligence.agents.relationship import (
    RelationshipAgent,
    _parse_relationship_json,
)
from intelligence.agents.research_evidence import EvidenceItem, EvidencePack

TENANT = "a0000000-0000-4000-a000-000000000001"
CID_A = "25ea3f23-a0a6-4bb5-b91e-59d8e5f402e5"
OTHER_TENANT_NAME = "Curl Search Co"  # belongs to tenant 796b129a…, NOT ours

COMPETITOR_JSON = json.dumps(
    {
        "competitors": [],
        "market_positioning": {"value": None, "basis": "unknown"},
        "commercial_context": [
            {"fact": "one open deal at prospecting stage [E3]", "evidence_id": "E3", "basis": "source"}
        ],
        "risks": [],
        "recommendations": [],
        "confidence": "medium",
        "missing_information": ["competitors"],
    }
)

RELATIONSHIP_JSON = json.dumps(
    {
        "contacts_summary": {"total": 2, "positions": ["ceo", "manager"], "departments": [], "basis": "source"},
        "decision_makers": [
            {"role_level": "executive", "evidence_ids": ["E4"], "name": None, "basis": "source"}
        ],
        "relationships": [],
        "timeline_insights": [],
        "recommendations": [],
        "confidence": "medium",
        "missing_information": ["names_by_design"],
    }
)


class FakeLLM:
    def __init__(self, content=COMPETITOR_JSON):
        self.content = content
        self.calls = []

    async def chat(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=self.content)


def _rich_pack() -> EvidencePack:
    pack = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=True)
    for f, v in [("status", "active"), ("city", "الرياض")]:
        pack.add(EvidenceItem("company", CID_A, f, v))
    pack.add(EvidenceItem("opportunity", "opp-1", "stage", "prospecting"))
    pack.add(EvidenceItem("contact_metadata", None, "positions", "ceo"))
    pack.add(EvidenceItem("contact_metadata", None, "positions", "manager"))
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
        # deliberate trap: caller text carries another tenant's company NAME
        "company_name": OTHER_TENANT_NAME,
        "industry": "technology",
        "topic": "analyze",
    }
    base.update(extra)
    return AgentTask(id="t", agent_type="x", input=base)


# ── Competitor ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_comp_loader_receives_tenant_and_company_ids():
    seen = {}
    llm = FakeLLM()
    await CompetitorAgent(llm, evidence_loader=_seen_loader(seen, _rich_pack())).execute(
        _task()
    )
    assert seen == {"t": TENANT, "c": CID_A}
    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_comp_prompt_has_evidence_rules_and_subject_id():
    llm = FakeLLM()
    await CompetitorAgent(llm, evidence_loader=_async_loader()).execute(_task())
    assert "Never invent competitors" in llm.calls[0]["system"]
    assert CID_A in llm.calls[0]["system"]
    user_prompt = llm.calls[0]["messages"][0]["content"]
    assert "[E1]" in user_prompt and "[E5]" in user_prompt
    assert "stage = prospecting" in user_prompt


@pytest.mark.asyncio
async def test_comp_structured_output_contract():
    llm = FakeLLM(COMPETITOR_JSON)
    result = await CompetitorAgent(llm, evidence_loader=_async_loader()).execute(_task())
    out = result.output
    assert out["analysis_depth"] == "grounded"
    ca = out["competitor_analysis"]
    for key in (
        "competitors",
        "market_positioning",
        "commercial_context",
        "risks",
        "recommendations",
        "confidence",
        "missing_information",
    ):
        assert key in ca
    assert out["metrics"]["evidence_count"] == 5
    assert out["metrics"]["found"] is True


@pytest.mark.asyncio
async def test_comp_insufficient_short_circuit_no_llm_call():
    empty = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=False)
    llm = FakeLLM()
    result = await CompetitorAgent(llm, evidence_loader=_async_loader(empty)).execute(
        _task()
    )
    assert llm.calls == []
    assert result.output["analysis"].startswith("INSUFFICIENT EVIDENCE")
    assert result.output["analysis_depth"] == "grounded_no_evidence"
    assert result.confidence == 0.2


@pytest.mark.asyncio
async def test_comp_no_pii_and_no_foreign_names_in_prompt():
    llm = FakeLLM()
    await CompetitorAgent(llm, evidence_loader=_async_loader()).execute(_task())
    blob = llm.calls[0]["system"] + llm.calls[0]["messages"][0]["content"]
    assert "@" not in blob  # tripwire: no emails
    assert "john" not in blob.lower()  # no invented person
    # entity confusion guard: foreign tenant's company name never becomes subject
    assert OTHER_TENANT_NAME not in llm.calls[0]["system"]


@pytest.mark.asyncio
async def test_comp_entity_identity_follows_company_id_not_name():
    llm = FakeLLM()
    await CompetitorAgent(llm, evidence_loader=_async_loader()).execute(_task())
    user_prompt = llm.calls[0]["messages"][0]["content"]
    assert f"SUBJECT company_id={CID_A}" in user_prompt


@pytest.mark.asyncio
async def test_comp_legacy_path_preserved_without_loader():
    llm = FakeLLM("تحليل تنافسي قديم")
    task = _task()
    task.input.pop("tenant_id")
    result = await CompetitorAgent(llm).execute(task)
    assert result.output["analysis"] == "تحليل تنافسي قديم"
    assert result.output["competitors"] == []
    assert result.confidence == 0.6
    assert len(llm.calls) == 1


# ── Relationship ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rel_loader_receives_tenant_and_company_ids():
    seen = {}
    llm = FakeLLM(RELATIONSHIP_JSON)
    await RelationshipAgent(llm, evidence_loader=_seen_loader(seen, _rich_pack())).execute(
        _task()
    )
    assert seen == {"t": TENANT, "c": CID_A}
    assert len(llm.calls) == 1


@pytest.mark.asyncio
async def test_rel_prompt_has_no_invention_rules():
    llm = FakeLLM(RELATIONSHIP_JSON)
    await RelationshipAgent(llm, evidence_loader=_async_loader()).execute(_task())
    system = llm.calls[0]["system"]
    assert "Never invent people" in system
    assert "BUSINESS METADATA ONLY" in system
    assert "must ALWAYS be null" in system


@pytest.mark.asyncio
async def test_rel_structured_output_contract():
    llm = FakeLLM(RELATIONSHIP_JSON)
    result = await RelationshipAgent(llm, evidence_loader=_async_loader()).execute(_task())
    out = result.output
    assert out["analysis_depth"] == "grounded"
    rm = out["relationship_map"]
    assert rm["contacts_summary"]["total"] == 2
    assert set(rm["contacts_summary"]["positions"]) == {"ceo", "manager"}
    assert all(dm["name"] is None for dm in rm["decision_makers"])
    # honest metadata-only digest, not person narratives
    assert "2 contact(s)" in out["analysis"]


@pytest.mark.asyncio
async def test_rel_parser_strips_model_injected_person_names():
    hostile = json.dumps(
        {
            "contacts_summary": {"total": 1, "positions": ["ceo"], "departments": [], "basis": "source"},
            "decision_makers": [
                {"role_level": "CFO", "name": "John Doe", "evidence_ids": [], "basis": "inference"}
            ],
            "confidence": "high",
        }
    )
    parsed = _parse_relationship_json(hostile)
    assert parsed["decision_makers"][0]["name"] is None


def test_comp_parser_degraded_keeps_raw_text_honest():
    parsed = _parse_competitor_json("not json at all")
    assert parsed["parse_quality"] == "degraded_raw_text"
    assert parsed["market_positioning"]["basis"] == "unknown"


def test_parsers_survive_horde_fences_and_trailing_commas():
    hostile_comp = (
        "Here is the analysis:\n```json\n"
        + json.dumps(
            {
                "competitors": [{"name": None, "evidence_ids": [], "confidence": "unknown", "basis": "unknown"},],
                "market_positioning": {"value": "UNKNOWN", "basis": "unknown",},
            }
        )
        + "\n```\nLet me know if you need more."
    )
    pc = _parse_competitor_json(hostile_comp)
    assert pc["parse_quality"] == "strict"
    assert pc["market_positioning"]["value"] == "UNKNOWN"

    hostile_rel = (
        "```json\n"
        + json.dumps(
            {
                "contacts_summary": {"total": 2, "positions": ["ceo",], "departments": [], "basis": "source",},
                "decision_makers": [{"role_level": "ceo", "name": None, "evidence_ids": ["E4"], "basis": "source",},],
            }
        )
        + "\n```"
    )
    pr = _parse_relationship_json(hostile_rel)
    assert pr["parse_quality"] == "strict"
    assert pr["contacts_summary"]["total"] == 2
    assert pr["decision_makers"][0]["name"] is None


@pytest.mark.asyncio
async def test_rel_insufficient_short_circuit_no_llm_call():
    empty = EvidencePack(tenant_id=TENANT, company_id=CID_A, found=False)
    llm = FakeLLM(RELATIONSHIP_JSON)
    result = await RelationshipAgent(llm, evidence_loader=_async_loader(empty)).execute(_task())
    assert llm.calls == []
    assert result.output["analysis"].startswith("INSUFFICIENT EVIDENCE")
    assert result.output["analysis_depth"] == "grounded_no_evidence"


@pytest.mark.asyncio
async def test_rel_no_pii_and_no_foreign_names_in_prompt():
    llm = FakeLLM(RELATIONSHIP_JSON)
    await RelationshipAgent(llm, evidence_loader=_async_loader()).execute(_task())
    blob = llm.calls[0]["system"] + llm.calls[0]["messages"][0]["content"]
    assert "@" not in blob
    assert OTHER_TENANT_NAME not in llm.calls[0]["system"]
    assert f"SUBJECT company_id={CID_A}" in llm.calls[0]["messages"][0]["content"]


@pytest.mark.asyncio
async def test_rel_legacy_path_preserved_without_loader():
    llm = FakeLLM("تحليل علاقات قديم")
    task = _task()
    task.input.pop("tenant_id")
    result = await RelationshipAgent(llm).execute(task)
    assert result.output["analysis"] == "تحليل علاقات قديم"
    assert result.confidence == 0.6


# ── Provider failure (AI Horde 406 / empty completions) ────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_cls,json_content",
    [(CompetitorAgent, COMPETITOR_JSON), (RelationshipAgent, RELATIONSHIP_JSON)],
)
async def test_empty_completion_yields_honest_fallback(agent_cls, json_content):
    llm = FakeLLM(content="")
    result = await agent_cls(llm, evidence_loader=_async_loader()).execute(_task())
    assert result.output["analysis"].startswith("INSUFFICIENT EVIDENCE")
    structured_key = (
        "competitor_analysis" if agent_cls is CompetitorAgent else "relationship_map"
    )
    assert result.output[structured_key]["parse_quality"] == "degraded_raw_text"
    assert result.success is True  # controlled failure, not a crash
