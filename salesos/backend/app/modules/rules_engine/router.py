from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.common.exceptions import safe_error_detail
from app.dependencies import verify_token
from app.modules.rules_engine.engine import RulesEngine, _rules_engine
from app.modules.rules_engine.models import (
    Action,
    ConditionGroup,
    DomainType,
    Rule,
    RuleEvaluationContext,
)

router = APIRouter(prefix="/api/v1/rules")


def _engine() -> RulesEngine:
    return _rules_engine


def _rule_to_response(rule: Rule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "enabled": rule.enabled,
        "domain": rule.domain,
        "conditions": rule.conditions.model_dump()
        if hasattr(rule.conditions, "model_dump")
        else rule.conditions,
        "actions": [a.model_dump() if hasattr(a, "model_dump") else a for a in rule.actions],
        "priority": rule.priority,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


class RuleCreateRequest(BaseModel):
    name: str
    description: str = ""
    enabled: bool = True
    domain: DomainType = "company"
    conditions: dict = {"type": "and", "conditions": []}
    actions: list[dict] = []
    priority: int = 0


class RuleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    domain: DomainType | None = None
    conditions: dict | None = None
    actions: list[dict] | None = None
    priority: int | None = None


@router.get("")
async def list_rules(
    domain: DomainType | None = Query(None),
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    rules = engine.list_rules(domain=domain)
    return [_rule_to_response(r) for r in rules]


@router.post("", status_code=201)
async def create_rule(
    body: RuleCreateRequest,
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    rule_id = f"rule-{uuid.uuid4().hex[:12]}"

    rule = Rule(
        id=rule_id,
        name=body.name,
        description=body.description,
        enabled=body.enabled,
        domain=body.domain,
        conditions=ConditionGroup(**body.conditions),
        actions=[Action(**a) for a in body.actions],
        priority=body.priority,
    )

    try:
        created = engine.create_rule(rule)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=safe_error_detail(e, "Rule conflict")) from e

    return _rule_to_response(created)


@router.get("/{rule_id}")
async def get_rule(
    rule_id: str,
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    rule = engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _rule_to_response(rule)


@router.put("/{rule_id}")
async def update_rule(
    rule_id: str,
    body: RuleUpdateRequest,
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        updated = engine.update_rule(rule_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_error_detail(e, "Rule not found")) from e
    return _rule_to_response(updated)


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    deleted = engine.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"deleted": True, "id": rule_id}


@router.post("/{rule_id}/evaluate")
async def evaluate_rule_endpoint(
    rule_id: str,
    context: RuleEvaluationContext,
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    try:
        result = engine.evaluate(rule_id, context)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_error_detail(e, "Rule not found")) from e
    return result.model_dump() if hasattr(result, "model_dump") else result


@router.post("/evaluate-batch")
async def evaluate_batch(
    context: RuleEvaluationContext,
    _token: dict = Depends(verify_token),
):
    engine = _engine()
    result = engine.evaluate_batch(context)
    return result.model_dump() if hasattr(result, "model_dump") else result
