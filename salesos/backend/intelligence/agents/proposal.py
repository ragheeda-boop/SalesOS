"""Grounded Phase 3B — ProposalAgent (deterministic readiness gate).

Readiness is derived ONLY from real SalesOS facts: open pipeline stage, contact
primacy and recent activity. When data does not support a proposal, the answer
is NOT_READY / INSUFFICIENT — never a fabricated draft.
"""

import time

from .base import AgentResult, AgentTask, BaseAgent
from .grounded_common import index_pack, insufficient, metrics, opportunities_from
from .llm import LLMService

LATE_STAGES = {"proposal", "negotiation", "closing"}
OPEN_STATUSES = {"open", "in_progress", "qualified", "proposal", "negotiation"}


def build_proposal_readiness(pack) -> dict:
    missing = list(pack.missing_data)
    if not pack.found or not pack.items:
        return {
            "company_id": pack.company_id,
            "status": "INSUFFICIENT_EVIDENCE",
            "summary": (
                f"INSUFFICIENT EVIDENCE for company_id={pack.company_id}: "
                "no SalesOS records are visible to this analysis."
            ),
            "readiness": None,
            "checks": [],
            "next_actions": [],
            "missing_information": sorted(set(missing + ["company_record"])),
            "metrics": metrics(None, pack),
        }

    idx = index_pack(pack)
    deals = opportunities_from(pack, idx)

    checks: list[dict] = []

    if not deals:
        return {
            "company_id": pack.company_id,
            "status": "OK",
            "summary": "No pipeline exists — a proposal would be premature.",
            "readiness": "BLOCKED_NO_PIPELINE",
            "checks": [
                {
                    "check": "open_opportunity",
                    "result": "FAIL",
                    "basis": "derived",
                    "evidence": [],
                }
            ],
            "next_actions": [],
            "missing_information": sorted(set(missing + ["opportunities"])),
            "metrics": metrics(None, pack),
        }

    open_deals = []
    late_evidence = []
    for d in deals:
        status = ((d.get("status") or {}).get("value") or "").lower()
        if status in OPEN_STATUSES or status == "":
            open_deals.append(d)
            stage = ((d.get("stage") or {}).get("value") or "").lower()
            st_eid = (d.get("stage") or {}).get("evidence")
            if stage in LATE_STAGES and st_eid:
                late_evidence.append(st_eid)
    checks.append({
        "check": "open_opportunity",
        "result": "PASS" if open_deals else "FAIL",
        "basis": "source",
        "evidence": [
            (d.get("stage") or {}).get("evidence") for d in deals
        ],
    })
    checks.append({
        "check": "late_stage",
        "result": "PASS" if late_evidence else "FAIL",
        "basis": "derived",
        "evidence": late_evidence,
    })

    primary = idx.get(("contact_metadata", "primary_contacts"), [])
    total_contacts_ev = idx.get(("contact_metadata", "contacts_total"), [])
    checks.append({
        "check": "primary_contact",
        "result": "PASS" if primary else "FAIL",
        "basis": "source",
        "evidence": [eid for eid, _v, _s, _b in total_contacts_ev],
    })

    if late_evidence and primary:
        readiness = "READY"
    elif open_deals:
        readiness = "NOT_READY"
    else:
        readiness = "BLOCKED_NO_PIPELINE"

    next_actions = []
    if readiness == "READY":
        next_actions.append({
            "action": "Prepare proposal: scope, commercial terms and approval chain.",
            "evidence": late_evidence + [eid for eid, _v, _s, _b in total_contacts_ev],
        })
    else:
        if not late_evidence:
            next_actions.append({
                "action": "Move the open opportunity to proposal/negotiation stage first.",
                "evidence": [(d.get("stage") or {}).get("evidence") for d in deals],
            })
        if not primary:
            next_actions.append({
                "action": "Flag a primary business contact before drafting.",
                "evidence": [eid for eid, _v, _s, _b in total_contacts_ev],
            })

    return {
        "company_id": pack.company_id,
        "status": "OK",
        "summary": f"Proposal readiness {readiness} from real pipeline/contact records.",
        "readiness": readiness,
        "checks": checks,
        "next_actions": next_actions,
        "missing_information": sorted(set(missing)),
        "metrics": metrics(None, pack),
    }


class ProposalAgent(BaseAgent):
    """Proposal readiness grounded strictly in real SalesOS records."""

    def __init__(self, llm: LLMService | None = None, evidence_loader=None):
        super().__init__("proposal", "2.1")
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
            out = build_proposal_readiness(pack)
            out["metrics"]["retrieval_ms"] = (
                round(retrieval_ms, 1) if retrieval_ms is not None else None
            )
            conf = 0.8 if out["status"] == "OK" else 0.3
            return AgentResult(
                task_id=task.id, agent_type="proposal", output=out, confidence=conf
            )

        # ── Legacy path (no loader injected): preserved verbatim behaviour ──
        company_name = task.input.get("company_name", "")
        goal = task.input.get("goal", "")

        if self._llm:
            response = await self._llm.chat(
                system="أنت كاتب مقترحات تجارية محترف.",
                messages=[{"role": "user", "content": f"اكتب مقترحاً تجارياً لـ {company_name or company_id}. الهدف: {goal}"}],
            )
            return AgentResult(
                task_id=task.id, agent_type="proposal",
                output={"proposal": response.content, "status": "draft"},
                confidence=0.65,
            )

        return AgentResult(
            task_id=task.id, agent_type="proposal",
            output={"company_id": company_id, "message": "يتطلب تكوين مفتاح OpenAI لإنشاء المقترح."},
            confidence=0.2,
        )
