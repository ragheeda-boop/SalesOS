"""Grounded Phase 3B — TenderAgent (deterministic, honest data gap).

SalesOS stores NO tender records. The agent grounds the entity's legal/
classification context (cr_type, legal_form, activity codes) from real
records and answers UNKNOWN for tender status — inventing tender deadlines
or requirements is the exact failure mode this agent exists to prevent.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import facts_map, metrics
from .llm import LLMService

GAP_REASON = (
    "No tender records exist in SalesOS for this company; tender status "
    "cannot be assessed without fabricating data."
)

CONTEXT_FIELDS = ("cr_type", "legal_form", "activity_code", "isic_description", "industry", "country")


def build_tender_context(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "tender_status": None,
            "missing_information": sorted(set(missing + ["company_record"])),
            "metrics": metrics(None, pack),
        }

    facts = facts_map(pack)
    context = [
        {"field": f, "value": v, "evidence": [eid]}
        for f, (v, eid) in facts.items()
        if f in CONTEXT_FIELDS and v
    ]

    return {
        "company_id": pack.company_id,
        "status": "OK",
        "summary": GAP_REASON,
        "tender_status": "UNKNOWN",
        "eligibility_context_only": {
            "fields": context,
            "note": (
                "Classification/legal fields may inform tender eligibility, but "
                "no active tenders are recorded in SalesOS."
            ),
        },
        "recommendations": [],
        "missing_information": sorted(set(missing + ["tender_records"])),
        "metrics": metrics(None, pack),
    }


class TenderAgent(BaseAgent):
    """Tender analysis that refuses to invent tender records."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("tender", "2.1")
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
            out = build_tender_context(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.6 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="tender", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        company_name = task.input.get("company_name", "")
        industry = task.input.get("industry", "")

        if self._llm:
            response = await self._llm.chat(
                system="أنت مستشار مناقصات حكومية.",
                messages=[{"role": "user", "content": f"ابحث عن فرص المناقصات المناسبة لـ {company_name or company_id} في قطاع {industry}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="tender",
                output={"analysis": response.content},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="tender",
            output={"message": "يتطلب تكوين مفتاح OpenAI ومصدر مناقصات حكومية."},
            confidence=0.2,
        )
