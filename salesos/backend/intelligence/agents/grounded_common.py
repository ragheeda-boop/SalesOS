"""Shared pure helpers for Grounded Phase 3B agents.

These consume the ONE canonical EvidencePack (research_evidence.py). They are
NOT a second evidence system — only indexing/formatting utilities so the eight
deterministic agents produce consistent contracts, citations and honest
degradation.
"""

from __future__ import annotations

from .base import AgentResult, AgentTask


def index_pack(pack):
    """Map (source_type, field) -> list[(eid, value, source_id, basis)]."""

    idx: dict[tuple[str, str], list[tuple[str, str, str | None, str]]] = {}
    for i, it in enumerate(pack.items, 1):
        idx.setdefault((it.source_type, it.field), []).append(
            (f"E{i}", it.value, it.source_id, it.basis)
        )
    return idx


def opportunities_from(pack, idx=None) -> list[dict]:
    """Group opportunity evidence items into per-deal dicts with citations."""

    idx = idx if idx is not None else index_pack(pack)
    deals: dict[str, dict] = {}
    for fld in ("name", "stage", "status", "probability", "value_band"):
        for eid, val, sid, _basis in idx.get(("opportunity", fld), []):
            d = deals.setdefault(sid or "?", {"id": sid})
            d[fld] = {"value": val, "evidence": eid}
    return [deals[k] for k in sorted(deals)]


def facts_map(pack, idx=None) -> dict[str, tuple[str, str]]:
    """All SOURCE company fields as field -> (value, eid)."""

    idx = idx if idx is not None else index_pack(pack)
    out: dict[str, tuple[str, str]] = {}
    for i, it in enumerate(pack.items, 1):
        if it.source_type == "company" and it.field not in out:
            out[it.field] = (it.value, f"E{i}")
    return out


def timeline_events(pack) -> list[dict]:
    out = []
    for i, it in enumerate(pack.items, 1):
        if it.source_type == "timeline":
            out.append({"event": it.field, "detail": it.value, "evidence": f"E{i}"})
    return out


def insufficient(
    task: AgentTask,
    agent_type: str,
    company_id: str,
    missing: list[str],
    summary: str,
    extra_output: dict | None = None,
) -> AgentResult:
    """Standard honest INSUFFICIENT_EVIDENCE result (deterministic, no LLM)."""

    output = {
        "company_id": str(company_id),
        "status": "INSUFFICIENT_EVIDENCE",
        "summary": summary,
        "missing_information": sorted(set(missing)),
        "recommendations": [],
    }
    if extra_output:
        output.update(extra_output)
    return AgentResult(task_id=task.id, agent_type=agent_type, output=output, confidence=0.3)


def metrics(retrieval_ms: float | None, pack) -> dict:
    return {
        "retrieval_ms": round(retrieval_ms, 1) if retrieval_ms is not None else None,
        "evidence_count": len(pack.items),
        "found": bool(pack.found),
        "llm_called": False,
    }
