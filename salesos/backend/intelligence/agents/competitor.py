import json
import re
import time

from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService

# Grounded Phase 2 — competitor analysis may only use supplied SalesOS
# evidence. Competitor identities absent from the pack must stay UNKNOWN;
# fabricated competitors/market-shares/budgets are the failure mode this
# agent is being fixed for.
GROUNDING_SYSTEM_PROMPT = """You are the grounded SalesOS competitor-analysis agent.

RULES (absolute):
1. Use ONLY facts present in the EvidencePack below. You have no other data access.
2. Never invent competitors, market shares, budgets, revenue figures,
   employee counts or customer relationships.
3. Label the basis of every material claim:
   SOURCE (stated in the pack) / DERIVED (computed only from pack values) /
   INFERENCE (clear reasoning beyond the pack, flagged as such) /
   UNKNOWN (not in the pack).
4. A competitor whose identity is not evidenced in the pack must NOT be
   listed — competitor facts are UNKNOWN.
5. If there is no commercial evidence at all, answer INSUFFICIENT EVIDENCE.
6. Cite evidence ids like [E3] next to every material claim.
7. The single subject is company_id={company_id}. Ignore any similarly
   named external entity; they are NOT this subject.

OUTPUT: return STRICT JSON only (no markdown fences, no prose) exactly:
{{
  "competitors": [{{"name": "string or null", "evidence_ids": ["E#"], "confidence": "high|medium|low|unknown", "basis": "source|derived|inference|unknown"}}],
  "market_positioning": {{"value": "string or null", "basis": "source|derived|inference|unknown"}},
  "commercial_context": [{{"fact": "...", "evidence_id": "E#", "basis": "..."}}],
  "risks": [{{"risk": "...", "basis": "..."}}],
  "recommendations": [{{"action": "...", "reason": "...", "evidence_ids": ["E#"]}}],
  "confidence": "high|medium|low",
  "missing_information": ["..."]
}}
"""

_COMPETITOR_TEMPLATE = {
    "competitors": [],
    "market_positioning": {"value": None, "basis": "unknown"},
    "commercial_context": [],
    "risks": [],
    "recommendations": [],
    "confidence": "low",
    "missing_information": [],
}

_CONFIDENCE_SCORE = {"high": 0.9, "medium": 0.7, "low": 0.4}


def _loads_lenient(text: str):
    """strict json.loads, then retry after stripping trailing commas —
    Horde models (Cydonia-24B) commonly emit both."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        cleaned = re.sub(r",\s*([}\]])", r"\1", text)
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None


def _parse_competitor_json(content: str) -> dict:
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
        parsed = _loads_lenient(cand)
        if isinstance(parsed, dict):
            merged = json.loads(json.dumps(_COMPETITOR_TEMPLATE))
            merged.update(
                {k: v for k, v in parsed.items() if k in _COMPETITOR_TEMPLATE}
            )
            merged.setdefault("parse_quality", "strict")
            return merged
    fallback = json.loads(json.dumps(_COMPETITOR_TEMPLATE))
    fallback["market_positioning"] = {"value": content, "basis": "unknown"}
    fallback["parse_quality"] = "degraded_raw_text"
    return fallback


class CompetitorAgent(BaseAgent):
    """Tracks competitor movements using real SalesOS evidence only.

    Grounded Phase 2: with an evidence_loader wired, the agent retrieves an
    EvidencePack for (tenant_id, company_id) first; absent competitor
    evidence yields UNKNOWN / INSUFFICIENT EVIDENCE instead of fabrication.
    """

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("competitor", "2.1")
        self._llm = llm
        # async (tenant_id, company_id) -> EvidencePack (shared Phase 1 loader)
        self._evidence_loader = evidence_loader

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")
        industry = task.input.get("industry", "")

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
                pack = None

        if pack is not None:
            return await self._run_grounded(task, pack, retrieval_ms)

        if self._llm:
            response = await self._llm.chat(
                system="أنت محلل استراتيجي. حلل المشهد التنافسي.",
                messages=[{"role": "user", "content": f"حلل المشهد التنافسي للشركة: {company_name or company_id} في قطاع: {industry}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="competitor",
                output={"analysis": response.content, "competitors": []},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="competitor",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحليل المنافسين."},
            confidence=0.2,
        )

    async def _run_grounded(
        self, task: AgentTask, pack, retrieval_ms: float | None
    ) -> AgentResult:
        metrics = {
            "retrieval_ms": round(retrieval_ms or 0.0, 1),
            "evidence_count": len(pack.items),
            "found": pack.found,
        }

        if not pack.found or not pack.items:
            missing = list(pack.missing_data) or ["no_evidence_items"]
            structured = json.loads(json.dumps(_COMPETITOR_TEMPLATE))
            structured["missing_information"] = missing + ["company_record"]
            structured["market_positioning"] = {
                "value": (
                    f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                    "no SalesOS records are visible to this analysis."
                ),
                "basis": "unknown",
            }
            return AgentResult(
                task_id=task.id,
                agent_type="competitor",
                output={
                    "analysis": structured["market_positioning"]["value"],
                    "competitors": [],
                    "analysis_depth": "grounded_no_evidence",
                    "competitor_analysis": structured,
                    "metrics": metrics,
                },
                confidence=0.2,
            )

        user_prompt = (
            "Analyze the competitive landscape strictly from this EvidencePack.\n\n"
            f"EvidencePack (the ONLY permitted source of truth):\n"
            f"{pack.to_prompt_block()}\n\n"
            "Return the strict JSON contract now."
        )

        response = await self._llm.chat(
            system=GROUNDING_SYSTEM_PROMPT.format(company_id=pack.company_id),
            messages=[{"role": "user", "content": user_prompt}],
        )

        structured = _parse_competitor_json(response.content)
        structured.setdefault("metrics", metrics)
        positioning = structured.get("market_positioning") or {}
        competitors = structured.get("competitors") or []
        ctx = structured.get("commercial_context") or []
        if structured.get("parse_quality") == "degraded_raw_text":
            # provider returned prose/broken JSON: never surface it as analysis
            analysis = (
                "INSUFFICIENT EVIDENCE (provider output unparseable; "
                "raw response retained under competitor_analysis)"
            )
        else:
            analysis = (
                positioning.get("value")
                or (
                    f"{len(competitors)} evidenced competitor(s); "
                    f"{len(ctx)} sourced commercial fact(s); "
                    f"missing: {', '.join(structured.get('missing_information') or []) or 'none'}"
                )
            ) or "INSUFFICIENT EVIDENCE"

        return AgentResult(
            task_id=task.id,
            agent_type="competitor",
            output={
                "analysis": analysis,
                "competitors": competitors,
                "analysis_depth": "grounded",
                "competitor_analysis": structured,
                "metrics": metrics,
            },
            confidence=_CONFIDENCE_SCORE.get(
                str(structured.get("confidence", "low")).lower(), 0.4
            ),
        )
