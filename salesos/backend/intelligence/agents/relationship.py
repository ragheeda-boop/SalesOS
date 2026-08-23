import json
import re
import time

from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService

# Grounded Phase 2 — relationship mapping may only describe people the way
# SalesOS stores them: counts and business metadata (positions, departments,
# primacy). Names/emails/phones never enter the pack, so the model cannot
# leak or invent them. Fabricated executives ("John is CFO") are the exact
# failure mode this agent is being fixed for.
GROUNDING_SYSTEM_PROMPT = """You are the grounded SalesOS relationship-mapping agent.

RULES (absolute):
1. Use ONLY facts present in the EvidencePack below. You have no other data access.
2. Never invent people: no CFO, CEO, decision maker, executive name, role,
   department, relationship, authority or influence that is not in the pack.
3. SalesOS exposes contacts as BUSINESS METADATA ONLY (counts, positions,
   departments). You do not know any person's name and must not guess one.
4. Label the basis of every material claim:
   SOURCE / DERIVED / INFERENCE / UNKNOWN.
5. If required evidence is missing answer UNKNOWN for that field; if there
   is no relationship-relevant evidence at all, answer INSUFFICIENT EVIDENCE.
6. Cite evidence ids like [E3] next to every material claim.
7. The single subject is company_id={company_id}. Ignore any similarly
   named external entity; they are NOT this subject.

OUTPUT: return STRICT JSON only (no markdown fences, no prose) exactly:
{{
  "contacts_summary": {{"total": null, "positions": [], "departments": [], "basis": "source|unknown"}},
  "decision_makers": [{{"role_level": "...", "evidence_ids": ["E#"], "name": null, "basis": "..."}}],
  "relationships": [{{"description": "...", "evidence_ids": ["E#"], "basis": "..."}}],
  "timeline_insights": [{{"insight": "...", "evidence_id": "E#", "basis": "..."}}],
  "recommendations": [{{"action": "...", "reason": "...", "evidence_ids": ["E#"]}}],
  "confidence": "high|medium|low",
  "missing_information": ["..."]
}}

HARD CONSTRAINT: "decision_makers[].name" must ALWAYS be null unless a real
person's name appears in the pack (it never does — names are excluded by design).
"""

_RELATIONSHIP_TEMPLATE = {
    "contacts_summary": {
        "total": None,
        "positions": [],
        "departments": [],
        "basis": "unknown",
    },
    "decision_makers": [],
    "relationships": [],
    "timeline_insights": [],
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


def _parse_relationship_json(content: str) -> dict:
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
            merged = json.loads(json.dumps(_RELATIONSHIP_TEMPLATE))
            merged.update(
                {k: v for k, v in parsed.items() if k in _RELATIONSHIP_TEMPLATE}
            )
            # PII backstop: strip any person-name the model tried to add.
            for dm in merged.get("decision_makers", []) or []:
                if isinstance(dm, dict):
                    dm["name"] = None
            merged.setdefault("parse_quality", "strict")
            return merged
    fallback = json.loads(json.dumps(_RELATIONSHIP_TEMPLATE))
    fallback["relationships"] = [
        {"description": content, "evidence_ids": [], "basis": "unknown"}
    ]
    fallback["parse_quality"] = "degraded_raw_text"
    return fallback


class RelationshipAgent(BaseAgent):
    """Maps relationships using real SalesOS metadata only.

    Grounded Phase 2: with an evidence_loader wired, identity comes from
    (tenant_id, company_id) and people are described as business metadata;
    invented executives become structurally impossible.
    """

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("relationship", "2.1")
        self._llm = llm
        # async (tenant_id, company_id) -> EvidencePack (shared Phase 1 loader)
        self._evidence_loader = evidence_loader

    async def _run(self, task: AgentTask) -> AgentResult:
        company_id = task.input.get("company_id", "unknown")
        company_name = task.input.get("company_name", "")

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
                system="أنت محلل علاقات.",
                messages=[{"role": "user", "content": f"حلل العلاقات للشركة: {company_name or company_id}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="relationship",
                output={"analysis": response.content},
                confidence=0.6,
            )

        return AgentResult(
            task_id=task.id, agent_type="relationship",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحليل العلاقات."},
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
            structured = json.loads(json.dumps(_RELATIONSHIP_TEMPLATE))
            structured["missing_information"] = missing + ["contact_records"]
            return AgentResult(
                task_id=task.id,
                agent_type="relationship",
                output={
                    "analysis": (
                        f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                        "no relationship records are visible to this analysis."
                    ),
                    "analysis_depth": "grounded_no_evidence",
                    "relationship_map": structured,
                    "metrics": metrics,
                },
                confidence=0.2,
            )

        user_prompt = (
            "Map relationships strictly from this EvidencePack.\n\n"
            f"EvidencePack (the ONLY permitted source of truth):\n"
            f"{pack.to_prompt_block()}\n\n"
            "Return the strict JSON contract now."
        )

        response = await self._llm.chat(
            system=GROUNDING_SYSTEM_PROMPT.format(company_id=pack.company_id),
            messages=[{"role": "user", "content": user_prompt}],
        )

        structured = _parse_relationship_json(response.content)
        structured.setdefault("metrics", metrics)
        contacts_summary = structured.get("contacts_summary") or {}
        positions = contacts_summary.get("positions") or []
        total = contacts_summary.get("total")
        rels = structured.get("relationships") or []
        insights = structured.get("timeline_insights") or []
        if structured.get("parse_quality") == "degraded_raw_text":
            # provider returned prose/broken JSON: never surface it as analysis
            analysis = (
                "INSUFFICIENT EVIDENCE (provider output unparseable; "
                "raw response retained under relationship_map)"
            )
        elif total is not None and positions:
            analysis = (
                f"{total} contact(s) present; roles on record: "
                + ", ".join(str(p) for p in positions)
            )
        elif total is not None:
            analysis = (
                f"{total} contact(s) present; no evidenced roles; "
                f"decision makers: UNKNOWN"
            )
        elif rels or insights:
            analysis = (
                f"{len(rels)} evidenced relationship(s); "
                f"{len(insights)} timeline insight(s); contact roles: UNKNOWN"
            )
        else:
            analysis = (
                (response.content or "").strip()
                or "INSUFFICIENT EVIDENCE"
            )

        return AgentResult(
            task_id=task.id,
            agent_type="relationship",
            output={
                "analysis": analysis,
                "analysis_depth": "grounded",
                "relationship_map": structured,
                "metrics": metrics,
            },
            confidence=_CONFIDENCE_SCORE.get(
                str(structured.get("confidence", "low")).lower(), 0.4
            ),
        )
