"""Grounded Phase 3B — PricingAgent (deterministic, honest data gap).

SalesOS stores NO list prices, discounts or pricing records. The agent reports
observed deal-size BANDS from real opportunities as context only, and answers
UNKNOWN for any pricing strategy question — inventing price points is the
exact failure mode this agent exists to prevent.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import facts_map, metrics, opportunities_from
from .llm import LLMService

GAP_REASON = (
    "No pricing records (list prices, discounts, rate cards) exist in "
    "SalesOS; a pricing strategy cannot be derived without fabricating data."
)


def build_pricing_context(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "pricing_status": None,
            "missing_information": sorted(set(missing + ["company_record"])),
            "metrics": metrics(None, pack),
        }

    deals = opportunities_from(pack)
    facts = facts_map(pack)

    bands: dict[str, int] = {}
    band_evidence: dict[str, list[str]] = {}
    for d in deals:
        b = (d.get("value_band") or {}).get("value")
        e = (d.get("value_band") or {}).get("evidence")
        if b:
            bands[b] = bands.get(b, 0) + 1
            if e:
                band_evidence.setdefault(b, []).append(e)

    segment, seg_ev = facts.get("segment", ("", ""))
    industry, ind_ev = facts.get("industry", ("", ""))

    return {
        "company_id": pack.company_id,
        "status": "OK",
        "summary": GAP_REASON,
        "pricing_status": "UNKNOWN",
        "context_only": {
            "segment": {"value": segment or None, "evidence": [seg_ev] if seg_ev else []},
            "industry": {"value": industry or None, "evidence": [ind_ev] if ind_ev else []},
            "observed_deal_bands": [
                {"band": b, "count": c, "evidence": sorted(band_evidence.get(b, []))}
                for b, c in sorted(bands.items())
            ],
        },
        "recommendations": [],
        "missing_information": sorted(
            set(missing + ["pricing_records", "competitor_pricing", "discount_history"])
        ),
        "metrics": metrics(None, pack),
    }


class PricingAgent(BaseAgent):
    """Pricing analysis that refuses to invent price points."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("pricing", "2.1")
        self._llm = llm
        self._evidence_loader = evidence_loader

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        tenant_id = task.input.get("tenant_id")

        pack = None
        retrieval_ms = None
        if (
            self._evidence_loader is not None
            and tenant_id
            and company_id not in ("", "unknown", None)
        ):
            try:
                t0 = time.monotonic()
                pack = await self._evidence_loader(str(tenant_id), str(company_id))
                retrieval_ms = (time.monotonic() - t0) * 1000
            except Exception:
                pack = None

        if pack is not None:
            out = build_pricing_context(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.6 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="pricing", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        company_name = task.input.get("company_name", "")

        if self._llm:
            response = await self._llm.chat(
                system="أنت محلل تسعير استراتيجي.",
                messages=[{"role": "user", "content": f"حلل استراتيجية التسعير المثلى لـ {company_name or company_id}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="pricing",
                output={"analysis": response.content},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="pricing",
            output={"message": "يتطلب تكوين مفتاح OpenAI لتحليل التسعير."},
            confidence=0.2,
        )
