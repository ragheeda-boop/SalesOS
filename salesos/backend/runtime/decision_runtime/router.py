"""Decision Intelligence Engine REST API.

Endpoints:
  POST /api/v1/decision/evaluate         — Evaluate company and return NBA
  GET  /api/v1/decision/next-best-action — Get highest-priority decision
  GET  /api/v1/decisions                 — List decisions for a company
  GET  /api/v1/decisions/:id             — Get single decision
  POST /api/v1/decisions/:id/accept      — Accept a decision
  POST /api/v1/decisions/:id/execute     — Execute a decision
  POST /api/v1/decisions/:id/feedback    — Submit feedback on a decision
  GET  /api/v1/decisions/:id/reasoning   — Get explainability for a decision
  GET  /api/v1/decisions/history         — Decision timeline for a company
  GET  /api/v1/decision/metrics          — Decision engine metrics
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token

router = APIRouter(dependencies=[Depends(verify_token)])


class EvaluateRequest(BaseModel):
    company_id: str


class FeedbackRequest(BaseModel):
    accepted: bool
    executed: bool = False
    outcome: Optional[str] = None
    outcome_value: Optional[float] = None
    notes: Optional[str] = None


@router.post("/decision/evaluate")
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


@router.get("/decision/next-best-action")
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


@router.get("/decisions/history")
async def decision_history(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    company_id: str = Query(..., description="Company ID"),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    return engine.get_history(company_id, tenant_id)


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    result = engine.get_decision(decision_id)
    if not result:
        raise HTTPException(status_code=404, detail="Decision not found")
    return result


@router.get("/decisions/{decision_id}/reasoning")
async def get_reasoning(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    result = await engine.get_reasoning(decision_id)
    if not result:
        raise HTTPException(status_code=404, detail="Decision not found")
    return result


@router.post("/decisions/{decision_id}/accept")
async def accept_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    ok = await engine.accept_decision(decision_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Decision cannot be accepted")
    return {"status": "accepted", "decision_id": decision_id}


@router.post("/decisions/{decision_id}/execute")
async def execute_decision(
    decision_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail="Decision Engine not initialized")
    ok = await engine.execute_decision(decision_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Decision cannot be executed")
    return {"status": "executed", "decision_id": decision_id}


@router.post("/decisions/{decision_id}/feedback")
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
        executed=body.executed,
        outcome=body.outcome,
        outcome_value=body.outcome_value,
        notes=body.notes,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"status": "feedback_received", "decision_id": decision_id}


@router.get("/decision/metrics")
async def decision_metrics(request: Request, tenant_id: str = Depends(get_current_tenant_id)):
    engine = getattr(request.app.state, "decision_engine", None)
    if not engine:
        return {"status": "not_initialized"}
    return engine.get_metrics()
