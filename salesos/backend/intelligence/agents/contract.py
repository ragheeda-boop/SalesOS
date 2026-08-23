"""Grounded Phase 3B — ContractAgent (deterministic, honest data gap).

SalesOS stores NO contract records in the EvidencePack. The agent grounds the
entity's legal context (legal_form, cr_type) from real records and answers
UNKNOWN — inventing contract terms or obligations is the exact failure mode
this agent exists to prevent.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import facts_map, metrics
from .llm import LLMService

GAP_REASON = (
    "No contract records exist in SalesOS for this company; contract "
    "analysis cannot be performed without fabricating data."
)

CONTEXT_FIELDS = ("legal_form", "cr_type", "country", "industry")


def build_contract_context(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "contract_status": None,
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
        "contract_status": "UNKNOWN",
        "entity_legal_context_only": {
            "fields": context,
            "note": (
                "Legal/classification fields may inform contract drafting, but "
                "no executed contracts are recorded in SalesOS."
            ),
        },
        "recommendations": [],
        "missing_information": sorted(set(missing + ["contracts"])),
        "metrics": metrics(None, pack),
    }


class ContractAgent(BaseAgent):
    """Contract analysis that refuses to invent contract records."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("contract", "2.1")
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
            out = build_contract_context(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.6 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="contract", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        if self._llm:
            response = await self._llm.chat(
                system="أنت مستشار قانوني متخصص في العقود التجارية.",
                messages=[{"role": "user", "content": f"حلل معلومات العقود للشركة {company_id} وقدم توصيات."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="contract",
                output={"analysis": response.content},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="contract",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحليل العقود."},
            confidence=0.2,
        )
