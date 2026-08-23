"""Grounded Phase 3B — RenewalAgent (deterministic, honest data gap).

SalesOS currently stores NO contract/subscription/renewal records in the
EvidencePack. The agent therefore answers UNKNOWN with the exact gap list.
Inventing renewal dates or churn risk is the exact failure mode this agent
exists to prevent. Context (activity recency, open pipeline) is cited where
it exists.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import facts_map, insufficient, metrics, opportunities_from, timeline_events
from .llm import LLMService

GAP_REASON = (
    "No contract or renewal records exist in SalesOS for this company; "
    "renewal status cannot be assessed without fabricating data."
)


def build_renewal_view(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "renewal_status": None,
            "missing_information": sorted(set(missing + ["company_record"])),
            "metrics": metrics(None, pack),
        }

    deals = opportunities_from(pack)
    events = timeline_events(pack)
    facts = facts_map(pack)

    return {
        "company_id": pack.company_id,
        "status": "OK",
        "summary": GAP_REASON,
        "renewal_status": "UNKNOWN",
        "context": {
            "customer_status": facts.get("status", (None, []))[0],
            "open_opportunities": len(deals),
            "timeline_event_count": len(events),
            "recent_activity": events[:3],
            "evidence": [e.get("evidence") for e in events[:3]],
        },
        "risks": [
            "Renewal risk is UNASSESSABLE without contract data — do not "
            "infer churn risk from pipeline alone."
        ],
        "recommendations": [],
        "missing_information": sorted(
            set(missing + ["contracts", "subscription_terms", "renewal_dates"])
        ),
        "metrics": metrics(None, pack),
    }


class RenewalAgent(BaseAgent):
    """Renewal analysis that refuses to invent contract data."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("renewal", "2.1")
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
            out = build_renewal_view(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.6 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="renewal", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        company_name = task.input.get("company_name", "")

        if self._llm:
            response = await self._llm.chat(
                system="أنت مدير نجاح عملاء. حلل مخاطر التجديد وقدم استراتيجيات الاحتفاظ.",
                messages=[{"role": "user", "content": f"حلل مخاطر تجديد العقد لـ {company_name or company_id}."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="renewal",
                output={"analysis": response.content},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="renewal",
            output={"message": "يتطلب تكوين مفتاح OpenAI لتحليل التجديد."},
            confidence=0.2,
        )
