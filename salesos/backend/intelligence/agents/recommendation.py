"""Grounded Phase 3A — evidence-backed sales recommendation agent.

Deterministic rules over the shared EvidencePack (+ optional ICP result).
No independent retrieval; no fabricated urgency; every action cites [E#].
"""

import time

from .base import BaseAgent, AgentTask, AgentResult
from .llm import LLMService


def _pack_index(pack):
    """field-keyed view of pack items with their E# ids."""
    by_field: dict[str, list[tuple[str, str, str]]] = {}
    stages: list[tuple[str, str]] = []  # (stage_value, eid)
    for i, item in enumerate(pack.items, 1):
        eid = f"E{i}"
        f = (item.field or "").lower()
        by_field.setdefault(f, []).append((item.value, item.source_type, eid))
        if item.source_type == "opportunity" and f == "stage":
            stages.append((str(item.value).lower(), eid))
    return by_field, stages


def _rec(priority, action, reason, evidence, confidence):
    return {
        "priority": priority,
        "action": action,
        "reason": reason,
        "evidence": evidence,
        "confidence": confidence,
    }


NO_ACTION = {
    "priority": "UNKNOWN",
    "action": "NO ACTION / INSUFFICIENT EVIDENCE",
    "reason": (
        "No SalesOS commercial records are visible for this company; "
        "any recommendation would be fabricated."
    ),
    "evidence": [],
    "confidence": 0.2,
}


def build_recommendations(pack, icp_result: dict | None) -> dict:
    """Pure deterministic recommendation builder over an EvidencePack."""
    if not pack.found or not pack.items:
        missing = list(pack.missing_data) or ["no_evidence_items"]
        return {
            "recommendations": [dict(NO_ACTION)],
            "icp_fit": "UNKNOWN",
            "risks": [],
            "missing_information": sorted(set(missing)),
            "metrics": {"found": False, "evidence_count": len(pack.items)},
            "analysis": NO_ACTION["action"],
            "confidence": 0.2,
        }

    by_field, stages = _pack_index(pack)
    recs: list[dict] = []
    risks: list[str] = []
    missing: list[str] = list(pack.missing_data)

    icp_fit = (icp_result or {}).get("fit", "UNKNOWN")

    # Opportunity-stage driven actions (SOURCE facts → DERIVED actions)
    for stage, eid in stages:
        if stage in ("prospecting", "qualification"):
            recs.append(
                _rec(
                    "HIGH",
                    "Run qualification before proposing a commercial offer.",
                    f"Opportunity is at '{stage}' stage — proposal readiness unproven.",
                    [eid],
                    0.8,
                )
            )
        elif stage in ("proposal", "negotiation"):
            recs.append(
                _rec(
                    "MEDIUM",
                    "Prepare close plan and confirm decision timeline.",
                    f"Opportunity at '{stage}' stage needs momentum management.",
                    [eid],
                    0.7,
                )
            )
        elif stage in ("won", "closed_won"):
            recs.append(
                _rec(
                    "LOW",
                    "Open expansion conversation after onboarding completes.",
                    f"Deal at '{stage}' — expansion is lower urgency than delivery.",
                    [eid],
                    0.6,
                )
            )
        else:
            risks.append(f"Unrecognized opportunity stage '{stage}' [{eid}]")

    # Contact metadata driven actions
    pos_entries = by_field.get("positions", [])
    primary = by_field.get("primary_contacts", [])
    has_primary = any(
        ("true" in v.lower()) for v, _t, _e in primary
    )
    if pos_entries and not has_primary:
        eids = [e for _v, _t, e in pos_entries]
        recs.append(
            _rec(
                "MEDIUM",
                "Identify and validate the primary business contact before outreach.",
                "Contacts exist but no primary stakeholder is flagged.",
                eids,
                0.7,
            )
        )

    # New-account signal from timeline
    created = [
        e for v, t, e in by_field.get("event", [])
        if "created" in v.lower()
    ] + [e for v, t, e in by_field.get("action", []) if "created" in v.lower()]
    if created:
        recs.append(
            _rec(
                "MEDIUM",
                "Schedule an initial discovery session with the account.",
                "Timeline shows the account record was recently created with no "
                "subsequent activity evidenced.",
                created[:2],
                0.6,
            )
        )

    # ICP chain: boost/cap priority, keep original evidence ids
    if icp_result and icp_result.get("fit") == "HIGH" and recs:
        top = max(recs, key=lambda r: r["confidence"])
        if top["priority"] != "HIGH":
            top["priority"] = "HIGH"
        top["reason"] += " Boosted by HIGH ICP fit."
        icp_ev = icp_result.get("evidence") or []
        top["evidence"] = list(dict.fromkeys(top["evidence"] + icp_ev))
    elif icp_result and icp_result.get("fit") == "UNKNOWN":
        risks.append(
            "ICP fit is UNKNOWN — "
            + (icp_result.get("reason") or "no active ICP profile for this tenant.")
        )
        for r in recs:
            if r["priority"] == "HIGH":
                r["priority"] = "MEDIUM"

    if "signals" in missing:
        risks.append(
            "No observable market signals recorded for this company in SalesOS."
        )

    if not recs:
        recs.append(
            dict(
                NO_ACTION,
                reason=(
                    "Evidence exists but supports no specific commercial action; "
                    "uncertainty is explicit rather than fabricated."
                ),
                confidence=0.3,
            )
        )

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNKNOWN": 3}
    recs.sort(key=lambda r: order.get(r["priority"], 9))

    analysis = "; ".join(f"[{r['priority']}] {r['action']}" for r in recs[:2])
    return {
        "recommendations": recs,
        "icp_fit": icp_fit,
        "risks": risks,
        "missing_information": sorted(set(missing)),
        "metrics": {"found": True, "evidence_count": len(pack.items)},
        "analysis": analysis,
        "confidence": recs[0]["confidence"] if recs else 0.2,
    }


class RecommendationAgent(BaseAgent):
    """Produces evidence-cited sales recommendations from the shared
    EvidencePack plus the deterministic ICP evaluation when available."""

    def __init__(
        self,
        llm: LLMService | None = None,
        evidence_loader=None,
        icp_store=None,
    ):
        super().__init__("recommendation", "2.1")
        self._llm = llm
        self._evidence_loader = evidence_loader
        self._icp_store = icp_store

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
                agent_type="recommendation",
                output={
                    "analysis": "يتطلب سياق الشركة لتوليد توصيات مبنية على الأدلة.",
                    "message": "Recommendation requires company context.",
                },
                confidence=0.2,
            )

        # ICP → Recommendation chain: reuse supplied result, else evaluate
        # deterministically against the SAME pack (no independent retrieval).
        icp_result = task.input.get("icp_result")
        icp_eval_ms = None
        if icp_result is None:
            try:
                from .icp import evaluate_icp

                def _store():
                    if self._icp_store is not None:
                        return self._icp_store
                    from app.modules.gtm.icp_store import DEFAULT_ICP_STORE

                    return DEFAULT_ICP_STORE

                t0 = time.monotonic()
                icp_result = evaluate_icp(pack, _store(), str(tenant_id))
                icp_eval_ms = (time.monotonic() - t0) * 1000
            except Exception:
                icp_result = None

        result = build_recommendations(pack, icp_result)
        metrics = result.get("metrics") or {}
        metrics["retrieval_ms"] = round(retrieval_ms or 0.0, 1)
        if icp_eval_ms is not None:
            metrics["icp_eval_ms"] = round(icp_eval_ms, 1)
        result["metrics"] = metrics

        return AgentResult(
            task_id=task.id,
            agent_type="recommendation",
            output=result,
            confidence=float(result.get("confidence") or 0.2),
        )
