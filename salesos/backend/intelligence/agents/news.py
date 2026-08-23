"""Grounded Phase 3B — NewsAgent (deterministic, honest data gap).

SalesOS has NO connected news corpus or RAG index for external articles.
The agent grounds the entity's profile context from real records and returns
an empty article list with UNKNOWN status — fabricating headlines is the
exact failure mode this agent exists to prevent.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import facts_map, metrics
from .llm import LLMService

GAP_REASON = (
    "No news corpus is connected to SalesOS; no article can be cited, so "
    "none will be invented."
)

CONTEXT_FIELDS = ("industry", "city", "region", "country", "segment")


def build_news_context(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "news_status": None,
            "articles": [],
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
        "news_status": "UNKNOWN",
        "articles": [],
        "entity_context_only": {
            "fields": context,
            "note": "Profile fields only; they are not news evidence.",
        },
        "recommendations": [],
        "missing_information": sorted(set(missing + ["news_corpus", "rag_snippets"])),
        "metrics": metrics(None, pack),
    }


class NewsAgent(BaseAgent):
    """News monitoring that refuses to invent articles."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("news", "2.1")
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
            out = build_news_context(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.6 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="news", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        company_name = task.input.get("company_name", "")

        if self._llm:
            response = await self._llm.chat(
                system="أنت محلل أخبار تجاري. قدم ملخصاً للأخبار والتوجهات.",
                messages=[{"role": "user", "content": f"ابحث عن آخر الأخبار والتوجهات للشركة: {company_name or company_id}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="news",
                output={"summary": response.content, "articles": []},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="news",
            output={"company_id": company_id, "articles": [], "message": "يتطلب تكوين مفتاح OpenAI ومصدر أخبار."},
            confidence=0.2,
        )
