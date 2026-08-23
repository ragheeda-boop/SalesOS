"""Grounded Phase 3A — ICP evaluation agent.

Uses ONLY the real runtime ICP framework (app.modules.gtm.icp_store /
icp_engine). If the tenant has no active ICP profile the answer is
UNKNOWN — inventing criteria or weights is the exact failure mode this
agent exists to prevent.
"""

import json
import time

from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService

NO_PROFILE_REASON = "No active ICP profile is available for this tenant."

# Fit bands derived from the engine's own fit_ratio (0..1). These are agent
# presentation thresholds, NOT invented profile weights.
_FIT_HIGH = 0.7
_FIT_MEDIUM = 0.4


def _company_facts_from_pack(pack):
    """Map SOURCE company/contact fields from the EvidencePack to the
    payload shape expected by score_company_against_profile, keeping the
    evidence ids per field for traceability."""
    facts: dict[str, str] = {}
    ev: dict[str, list[str]] = {}
    positions_ev: list[str] = []
    positions: list[str] = []
    for i, item in enumerate(pack.items, 1):
        eid = f"E{i}"
        f = (item.field or "").lower()
        v = item.value
        if item.source_type == "company":
            facts.setdefault(f, v)
            ev.setdefault(f, []).append(eid)
        elif item.source_type == "contact_metadata" and f == "positions":
            positions.append(v)
            positions_ev.append(eid)
        elif item.source_type == "contact_metadata" and f == "primary_contacts":
            try:
                data = json.loads(v)
                if isinstance(data, dict):
                    for p in data.get("positions", []) or []:
                        positions.append(str(p))
                        positions_ev.append(eid)
            except (json.JSONDecodeError, ValueError):
                pass
    return facts, ev, positions, positions_ev


def _active_profiles(store, tenant_id: str):
    try:
        return [p for p in store.list_for_tenant(tenant_id=tenant_id) if p.is_active]
    except Exception:
        return []


def evaluate_icp(pack, store, tenant_id: str) -> dict:
    """Pure deterministic ICP evaluation over an EvidencePack.

    Returns the full ICP output contract. No LLM involved."""
    missing = list(pack.missing_data)

    if not pack.found or not pack.items:
        return {
            "fit": "UNKNOWN",
            "criteria": [],
            "profiles_evaluated": [],
            "confidence": 0.2,
            "missing_information": sorted(set(missing + ["company_record"])),
            "reason": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "metrics": {
                "retrieval_ms": None,
                "evidence_count": len(pack.items),
                "found": False,
            },
        }

    profiles = _active_profiles(store, tenant_id)
    if not profiles:
        return {
            "fit": "UNKNOWN",
            "criteria": [],
            "profiles_evaluated": [],
            "confidence": 0.2,
            "missing_information": sorted(set(missing + ["icp_profile"])),
            "reason": NO_PROFILE_REASON,
            "metrics": {
                "retrieval_ms": None,
                "evidence_count": len(pack.items),
                "found": True,
                "llm_called": False,
            },
        }

    facts, ev, positions, positions_ev = _company_facts_from_pack(pack)

    def emp_val():
        raw = facts.get("employees_count") or facts.get("employees")
        try:
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    company_payload = {
        "industry": facts.get("industry", ""),
        "city": facts.get("city", ""),
        "title": positions[0] if positions else "",
        "employees_count": emp_val(),
        "keywords": " ".join(
            filter(None, [facts.get("name"), facts.get("description")])
        ),
    }

    from app.modules.gtm.icp_engine import score_company_against_profile

    criteria_out = []
    profiles_evaluated = []

    # field-name candidates per criterion → evidence ids
    ev_for = {
        "industry": ev.get("industry", []),
        "city": ev.get("city", []),
        "employees": ev.get("employees_count", []) + ev.get("employees", []),
        "titles": positions_ev,
        "keywords": ev.get("name", []) + ev.get("description", []),
    }

    best_ratio = None
    for prof in profiles:
        res = score_company_against_profile(prof, company_payload)
        profiles_evaluated.append(res.as_dict())
        ratio = res.fit_ratio
        best_ratio = ratio if best_ratio is None else max(best_ratio, ratio)

        crit = prof.criteria
        w = prof.weights
        pairs = [
            ("industry", bool(crit.industries), bool(res.matched.get("industry"))),
            ("city", bool(crit.cities), bool(res.matched.get("city"))),
            (
                "employees",
                crit.employees_min is not None or crit.employees_max is not None,
                bool(res.matched.get("employees")),
            ),
            ("titles", bool(crit.titles), bool(res.matched.get("titles"))),
            ("keywords", bool(crit.keywords), bool(res.matched.get("keywords"))),
        ]
        for name, active, ok in pairs:
            if not active or float(getattr(w, name, 0) or 0) <= 0:
                continue
            criteria_out.append(
                {
                    "criterion": name,
                    "result": "PASS" if ok else "FAIL",
                    # values were SOURCE from SalesOS; the match itself is DERIVED
                    "basis": "DERIVED",
                    "evidence": ev_for.get(name, []),
                }
            )

    if best_ratio is None:
        fit = "UNKNOWN"
    elif best_ratio >= _FIT_HIGH:
        fit = "HIGH"
    elif best_ratio >= _FIT_MEDIUM:
        fit = "MEDIUM"
    else:
        fit = "LOW"

    return {
        "fit": fit,
        "criteria": criteria_out,
        "profiles_evaluated": [
            {
                k: v
                for k, v in p.items()
                if k in ("profile_id", "schema_version", "score", "max_score", "fit_ratio")
            }
            for p in profiles_evaluated
        ],
        "confidence": 0.8 if criteria_out else 0.5,
        "evidence": sorted({e for c in criteria_out for e in c["evidence"]}),
        "missing_information": missing
        + ([] if criteria_out else ["matching_criteria"]),
        "reason": None,
        "metrics": {
            "retrieval_ms": None,
            "evidence_count": len(pack.items),
            "found": True,
            "llm_called": False,
        },
    }


class ICPAgent(BaseAgent):
    """Evaluates Ideal Customer Profile fit using ONLY real runtime ICP
    profiles scored against EvidencePack facts (deterministic engine)."""

    def __init__(
        self,
        llm: LLMService | None = None,
        evidence_loader=None,
        icp_store=None,
    ):
        super().__init__("icp", "2.1")
        self._llm = llm
        self._evidence_loader = evidence_loader
        self._icp_store = icp_store

    def _store(self):
        if self._icp_store is not None:
            return self._icp_store
        from app.modules.gtm.icp_store import DEFAULT_ICP_STORE

        return DEFAULT_ICP_STORE

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

        if pack is None:
            return AgentResult(
                task_id=task.id,
                agent_type="icp",
                output={
                    "analysis": "يتطلب تكوين مفتاح OpenAI وبيانات الشركة لتقييم ICP.",
                    "message": "ICP evaluation requires company context.",
                },
                confidence=0.2,
            )

        result = evaluate_icp(pack, self._store(), str(tenant_id))
        metrics = result.get("metrics") or {}
        metrics["retrieval_ms"] = round(retrieval_ms or 0.0, 1)
        result["metrics"] = metrics

        analysis = result.get("reason") or (
            f"ICP fit={result['fit']} across "
            f"{len(result.get('profiles_evaluated') or [])} active profile(s); "
            f"{len(result.get('criteria') or [])} criteria evaluated from evidence."
        )
        result["analysis"] = analysis

        return AgentResult(
            task_id=task.id,
            agent_type="icp",
            output=result,
            confidence=float(result.get("confidence") or 0.2),
        )
