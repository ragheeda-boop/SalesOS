"""Grounded Phase 3B — MeetingAgent (deterministic brief + agenda).

The brief is built ONLY from real SalesOS facts in the EvidencePack: company
profile fields, attendee ROLES (PII-free metadata), recent timeline activity
and open pipeline. Agenda items are deterministic rules over those facts, each
citing its evidence ids. The caller-supplied company_name is ignored.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import facts_map, index_pack, insufficient, metrics, opportunities_from, timeline_events
from .llm import LLMService

PROFILE_FIELDS = ("status", "city", "region", "industry", "segment", "country", "employees_count")

LATE_STAGES = {"proposal", "negotiation", "closing"}


def build_meeting_brief(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "brief": None,
            "agenda": [],
            "missing_information": sorted(set(missing + ["company_record"])),
            "metrics": metrics(None, pack),
        }

    idx = index_pack(pack)
    facts = facts_map(pack, idx)
    deals = opportunities_from(pack, idx)
    events = timeline_events(pack)

    positions = [
        (v, eid) for eid, v, _sid, _b in idx.get(("contact_metadata", "positions"), [])
    ]
    primary = idx.get(("contact_metadata", "primary_contacts"), [])

    profile = [
        {"field": f, "value": v, "evidence": [eid]}
        for f, (v, eid) in facts.items()
        if f in PROFILE_FIELDS
    ]

    agenda: list[dict] = []
    if deals:
        stages = {(d.get("stage") or {}).get("value", "").lower() for d in deals}
        stage_ev = [(d.get("stage") or {}).get("evidence") for d in deals]
        late = stages & LATE_STAGES
        if late:
            agenda.append({
                "item": "Advance the open proposal/negotiation — confirm scope and timeline.",
                "evidence": [e for e in stage_ev if e],
            })
        else:
            agenda.append({
                "item": "Qualify: needs, budget authority and decision process.",
                "evidence": [e for e in stage_ev if e],
            })
    else:
        agenda.append({
            "item": "Discovery: no pipeline exists yet — qualify fit before offering.",
            "evidence": [],
        })

    role_text = ", ".join(v for v, _ in positions)
    has_decision_maker = any(
        kw in role_text.lower()
        for kw in ("ceo", "cto", "cfo", "COO".lower(), "director", "manager", "owner")
    )
    if positions and not has_decision_maker:
        agenda.append({
            "item": "Identify the economic buyer — recorded roles contain no decision-maker title.",
            "evidence": [eid for _, eid in positions],
        })

    if not primary:
        agenda.append({
            "item": "Confirm the primary contact on the customer side.",
            "evidence": [eid for eid, _v, _s, _b in idx.get(("contact_metadata", "contacts_total"), [])],
        })

    return {
        "company_id": pack.company_id,
        "status": "OK",
        "summary": (
            f"Meeting brief from {len(pack.items)} SalesOS evidence items "
            f"({len(deals)} opportunity(ies), {len(events)} timeline event(s))."
        ),
        "brief": {
            "profile": profile,
            "attendee_roles": [{"role": v, "evidence": [eid]} for v, eid in positions],
            "recent_activity": events[:5],
            "pipeline": [
                {
                    "stage": (d.get("stage") or {}).get("value"),
                    "status": (d.get("status") or {}).get("value"),
                    "evidence": [
                        v.get("evidence") for v in d.values() if isinstance(v, dict)
                    ],
                }
                for d in deals
            ],
        },
        "agenda": agenda,
        "missing_information": sorted(set(missing)),
        "metrics": metrics(None, pack),
    }


class MeetingAgent(BaseAgent):
    """Meeting preparation grounded strictly in real SalesOS records."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("meeting", "2.1")
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
            out = build_meeting_brief(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.8 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="meeting", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        company_name = task.input.get("company_name", "")
        goal = task.input.get("goal", "")

        if self._llm:
            response = await self._llm.chat(
                system="أنت مساعد تحضير اجتماعات مبيعات.",
                messages=[{"role": "user", "content": f"حضر لاجتماع مع {company_name or company_id}. الهدف: {goal}. قدم جدول أعمال ونقاط نقاش."}],
            )
            return AgentResult(
                task_id=task.id, agent_type="meeting",
                output={"preparation": response.content},
                confidence=0.7,
            )

        return AgentResult(
            task_id=task.id, agent_type="meeting",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لتحضير الاجتماع."},
            confidence=0.2,
        )
