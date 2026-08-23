import json
import time

from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService
from sdk.config import sdk_settings

# Grounded Phase 1 — the LLM may only use supplied evidence and must label
# the basis of every claim. Any database fact absent from the pack is UNKNOWN.
GROUNDING_SYSTEM_PROMPT = """You are the grounded SalesOS research agent.

RULES (absolute):
1. Use ONLY facts present in the EvidencePack below. You have no other data access.
2. Never infer a database fact that is not present: no names, revenue figures,
   employee counts, competitors, decision makers or financial values.
3. Distinguish and label the basis of every material claim:
   SOURCE (stated directly in the pack) / DERIVED (computed only from pack
   values) / INFERENCE (clear reasoning beyond the pack, flagged as such) /
   UNKNOWN (not in the pack).
4. If required evidence is missing, answer UNKNOWN for that field.
5. Cite evidence ids like [E3] next to every material claim.
6. The single subject of analysis is company_id={company_id}. Ignore any
   similarly named external entity; they are NOT this subject.

OUTPUT: return STRICT JSON only (no markdown fences, no prose) exactly:
{{
  "company_summary": "string",
  "industry": {{"value": "string or null", "basis": "source|derived|inference|unknown"}},
  "business_signals": [{{"signal": "...", "evidence_id": "E#", "strength": "low|medium|high", "basis": "..."}}],
  "commercial_context": [{{"fact": "...", "evidence_id": "E#", "basis": "..."}}],
  "opportunities": [{{"description": "...", "evidence_ids": ["E#"], "basis": "..."}}],
  "risks": [{{"risk": "...", "basis": "..."}}],
  "recommendations": [{{"action": "...", "reason": "...", "evidence_ids": ["E#"]}}],
  "confidence": "high|medium|low",
  "missing_information": ["..."]
}}
"""

_RESEARCH_TEMPLATE = {
    "company_summary": "",
    "industry": {"value": None, "basis": "unknown"},
    "business_signals": [],
    "commercial_context": [],
    "opportunities": [],
    "risks": [],
    "recommendations": [],
    "confidence": "low",
    "missing_information": [],
}

_CONFIDENCE_SCORE = {"high": 0.9, "medium": 0.7, "low": 0.4}


def _parse_research_json(content: str) -> dict:
    """Robustly extract the research contract; degrade honestly on failure."""
    text = (content or "").strip()
    candidates = [text]
    if text.startswith("```"):
        body = text.strip("`")
        if body.lower().startswith("json"):
            body = body[4:]
        candidates.insert(0, body.strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for cand in candidates:
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, dict):
                merged = json.loads(json.dumps(_RESEARCH_TEMPLATE))  # deep copy
                merged.update({k: v for k, v in parsed.items() if k in _RESEARCH_TEMPLATE})
                merged.setdefault("parse_quality", "strict")
                return merged
        except (json.JSONDecodeError, ValueError):
            continue
    fallback = json.loads(json.dumps(_RESEARCH_TEMPLATE))
    fallback["company_summary"] = content
    fallback["parse_quality"] = "degraded_raw_text"
    return fallback


class ResearchAgent(BaseAgent):
    """Researches companies using real SalesOS evidence before LLM analysis.

    Grounded Phase 1: when an evidence_loader is wired, the agent retrieves an
    EvidencePack from SalesOS records first; the LLM only reasons over that
    pack under strict grounding rules. Without a loader the legacy behaviour
    is preserved unchanged.
    """

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("research", "2.1")
        self._llm = llm
        # async (tenant_id, company_id) -> EvidencePack
        self._evidence_loader = evidence_loader

    async def execute_grounded(self, task: AgentTask, **kwargs) -> AgentResult:
        """Shim matching GroundedBaseAgent.execute_grounded(task) call shape.

        Extra kwargs are merged into task.input, then delegated to execute → _run.
        Does not open LLM HTTP on its own; uses the existing execute path.
        """
        if kwargs:
            task.input = {**task.input, **kwargs}
        return await self.execute(task)

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        cr_number = task.input.get("cr_number", "")
        city = task.input.get("city", "")
        topic = task.input.get("topic", "")

        pack = None
        retrieval_ms = None
        tenant_id = task.input.get("tenant_id")
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
                pack = None  # retrieval must never break the request path

        if pack is not None:
            return await self._run_grounded(task, pack, topic, retrieval_ms)

        # ── Legacy path (unchanged): caller-context-only research ──
        system_prompt = "أنت باحث مبيعات في السعودية. قدم معلومات دقيقة ومفيدة عن الشركات."
        user_prompt = f"""الرجاء البحث عن معلومات عن الشركة التالية:
- الاسم: {company_name}
- السجل التجاري: {cr_number}
- المدينة: {city}
- الموضوع: {topic or 'عام'}

قدم باللغة العربية:
1. معلومات أساسية (النشاط، الحجم المتوقع، السوق)
2. فرص بيع محتملة
3. توصيات للتواصل"""

        # Legacy contract: a client-less LLMService must NOT open HTTP here
        # (tests/unit/intelligence/test_research_agent.py). Only services that
        # expose an underlying .client may be called from the legacy path.
        if self._llm is not None and getattr(self._llm, "client", None):
            response = await self._llm.chat(
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=sdk_settings.llm_temperature,
                max_tokens=sdk_settings.llm_research_max_tokens,
            )
            return AgentResult(
                task_id=task.id, agent_type="research",
                success=True,
                output={"summary": response.content, "sources": [], "research_depth": "llm"},
                confidence=0.7,
            )

        # Fallback if no LLM available
        return AgentResult(
            task_id=task.id, agent_type="research",
            success=True,
            output={
                "company_id": company_id,
                "summary": f"معلومات عن {company_name or company_id} — يتطلب تكوين مفتاح OpenAI لتوليد تحليل كامل.",
                "research_depth": "minimal",
            },
            confidence=0.3,
        )

    async def _run_grounded(
        self, task: AgentTask, pack, topic: str, retrieval_ms: float | None
    ) -> AgentResult:
        metrics = {
            "retrieval_ms": round(retrieval_ms or 0.0, 1),
            "evidence_count": len(pack.items),
            "found": pack.found,
        }

        # Deterministic short-circuit: with zero evidence the LLM must not be
        # given any chance to invent database facts.
        if not pack.found or not pack.items:
            missing = list(pack.missing_data) or ["no_evidence_items"]
            research = json.loads(json.dumps(_RESEARCH_TEMPLATE))
            research["missing_information"] = missing + ["company_record"]
            research["company_summary"] = (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                f"no SalesOS records are visible to this analysis."
            )
            return AgentResult(
                task_id=task.id,
                agent_type="research",
                output={
                    "summary": research["company_summary"],
                    "sources": [],
                    "research_depth": "grounded_no_evidence",
                    "research": research,
                    "metrics": metrics,
                },
                confidence=0.2,
            )

        user_prompt = (
            f"Research question/topic: {topic or 'general company analysis'}\n\n"
            f"EvidencePack (the ONLY permitted source of truth):\n"
            f"{pack.to_prompt_block()}\n\n"
            f"Return the strict JSON contract now."
        )

        response = await self._llm.chat(
            system=GROUNDING_SYSTEM_PROMPT.format(company_id=pack.company_id),
            messages=[{"role": "user", "content": user_prompt}],
            temperature=sdk_settings.llm_temperature,
            max_tokens=sdk_settings.llm_research_max_tokens,
        )

        structured = _parse_research_json(response.content)
        structured.setdefault("metrics", metrics)
        summary = (
            structured.get("company_summary")
            or (response.content or "").strip()
            or "INSUFFICIENT EVIDENCE"
        )
        evidence_refs = []
        for e in structured.get("evidence", []) if isinstance(structured.get("evidence"), list) else []:
            evidence_refs.append(str(e))

        return AgentResult(
            task_id=task.id,
            agent_type="research",
            output={
                "summary": summary,
                "sources": evidence_refs,
                "research_depth": "grounded",
                "research": structured,
                "metrics": metrics,
            },
            confidence=_CONFIDENCE_SCORE.get(
                str(structured.get("confidence", "low")).lower(), 0.4
            ),
        )
