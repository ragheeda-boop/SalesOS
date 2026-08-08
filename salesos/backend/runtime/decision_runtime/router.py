"""Decision Intelligence Engine REST API (Decision Runtime).

EAB-001-P0-DUP-01 / Completion Program Stream B:
Mounted at ``/api/v1/decision-runtime`` (not ``/api/v1``) so routes no longer
collide with Decision Center (``/api/v1/decisions*``) or Decision Platform
(``/api/v1/decision/*``). See DECISION-API-SOT.md.

Endpoints (after mount prefix ``/api/v1/decision-runtime``):
  POST .../decision/evaluate         — Evaluate company and return NBA
  GET  .../decision/next-best-action — Get highest-priority decision
  GET  .../decisions/:id             — Get single decision
  POST .../decisions/:id/accept      — Accept a decision
  POST .../decisions/:id/execute     — Execute a decision
  POST .../decisions/:id/feedback    — Submit feedback on a decision
  GET  .../decisions/:id/reasoning   — Get explainability for a decision
  GET  .../decisions/history         — Decision timeline for a company
  GET  .../decision/metrics          — Decision engine metrics

Deprecated aliases (do not use): former ``/api/v1/decision/*`` and
``/api/v1/decisions/*`` paths for this engine — those belong to Platform / Center.
Active remount paths are **not** OpenAPI-deprecated (clients may use them for NBA).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token

_RUNTIME_DESC = (
    "Decision Runtime DIE at /api/v1/decision-runtime — not Decision Center SoT. "
    "Prefer /api/v1/decisions* for governed ledger. Former /api/v1 aliases removed. "
    "EAB-001-P0-DUP-01 / DECISION-API-SOT.md."
)

router = APIRouter(dependencies=[Depends(verify_token)])


class EvaluateRequest(BaseModel):
    company_id: str


class FeedbackRequest(BaseModel):
    accepted: bool
    executed: bool = False
    outcome: Optional[str] = None
    outcome_value: Optional[float] = None
    notes: Optional[str] = None


@router.post(
    "/decision/evaluate",
    summary="Runtime evaluate (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def evaluate(
    body: EvaluateRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    result = await engine.evaluate(body.company_id, tenant_id)
    return result


@router.get(
    "/decision/next-best-action",
    summary="Runtime NBA (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def next_best_action(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    company_id: str = Query(..., description="Company ID"),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    result = await engine.get_next_best_action(company_id, tenant_id)
    return result


@router.get(
    "/decisions/history",
    summary="Runtime history (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def decision_history(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    company_id: str = Query(..., description="Company ID"),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    return engine.get_history(company_id, tenant_id)


@router.get(
    "/decisions/{decision_id}",
    summary="Runtime get decision (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def get_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    result = engine.get_decision(decision_id, tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Decision not found")
    return result


@router.get(
    "/decisions/{decision_id}/reasoning",
    summary="Runtime reasoning (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def get_reasoning(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    result = await engine.get_reasoning(decision_id, tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Decision not found")
    return result


@router.post(
    "/decisions/{decision_id}/accept",
    summary="Runtime accept (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def accept_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    ok = await engine.accept_decision(decision_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Decision cannot be accepted")
    return {"status": "accepted", "decision_id": decision_id}


@router.post(
    "/decisions/{decision_id}/execute",
    summary="Runtime execute (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def execute_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    ok = await engine.execute_decision(decision_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Decision cannot be executed")
    return {"status": "executed", "decision_id": decision_id}


@router.post(
    "/decisions/{decision_id}/feedback",
    summary="Runtime feedback (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def submit_feedback(
    decision_id: str,
    body: FeedbackRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    ok = await engine.submit_feedback(
        decision_id=decision_id,
        accepted=body.accepted,
        tenant_id=tenant_id,
        executed=body.executed,
        outcome=body.outcome,
        outcome_value=body.outcome_value,
        notes=body.notes,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"status": "feedback_received", "decision_id": decision_id}


@router.get(
    "/decision/metrics",
    summary="Runtime metrics (remounted DIE)",
    description=_RUNTIME_DESC,
)
async def decision_metrics(request: Request, tenant_id: str = Depends(get_current_tenant_id)):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        return {"status": "not_initialized"}
    return engine.get_metrics()
