"""STORY-12-02 — AI Policies HTTP (CAP-091, reuses AI-GR-*).

Not Production GO. DEC-085 untouched. feature_ai_copilot remains False.
No live LLM / RAG GO.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.ai_policies import (
    AI_GUARDRAIL_CATALOG,
    VALID_DATA_CLASSES,
    VALID_MODEL_TIERS,
    AiPolicyError,
)
from app.modules.tenant_studio.ai_policies_store import (
    DEFAULT_AI_POLICIES_STORE,
    MemAiPoliciesStore,
)

router = APIRouter(prefix="/studio/ai-policies", tags=["AI Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_AI_POLICIES_STORE


class DataClassRuleIn(BaseModel):
    data_class: str
    max_model_tier: str
    require_pii_scrub: bool = True


class AiPolicyUpsert(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    guardrails: dict[str, bool] = Field(default_factory=dict)
    data_class_rules: list[DataClassRuleIn] = Field(default_factory=list)


class AiPolicyResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    guardrails: dict[str, bool]
    data_class_rules: list[dict[str, Any]]
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


class AiPolicyEvaluateBody(BaseModel):
    data_class: str = Field(..., min_length=1, max_length=32)
    requested_model_tier: str = "economy"
    sample_text: str = ""
    policy_id: str | None = None


@router.get("/meta", dependencies=_AUTH)
async def ai_policies_meta() -> dict[str, Any]:
    return {
        "object": "AiPolicySet",
        "capability": "CAP-091",
        "reuses": list(AI_GUARDRAIL_CATALOG.keys()),
        "guardrail_catalog": dict(AI_GUARDRAIL_CATALOG),
        "data_classes": list(VALID_DATA_CLASSES),
        "model_tiers": list(VALID_MODEL_TIERS),
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": (
            "Reuses existing AI-GR-* primitives (intelligence.guardrails); "
            "in-memory tenant toggles + data-class ceilings. Live LLM / RAG GO "
            "not claimed. feature_ai_copilot remains False."
        ),
    }


@router.post("", response_model=AiPolicyResponse, dependencies=_AUTH)
async def upsert_ai_policy(
    body: AiPolicyUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> AiPolicyResponse:
    try:
        row = _STORE.upsert(
            tenant_id=str(tenant_id),
            name=body.name,
            guardrails=body.guardrails or None,
            data_class_rules=[r.model_dump() for r in body.data_class_rules] or None,
            policy_id=body.id,
        )
    except AiPolicyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return AiPolicyResponse.model_validate(row.as_dict())


@router.get("", response_model=list[AiPolicyResponse], dependencies=_AUTH)
async def list_ai_policies(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[AiPolicyResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    if not rows:
        rows = [_STORE.ensure_default(tenant_id=str(tenant_id))]
    return [AiPolicyResponse.model_validate(r.as_dict()) for r in rows]


@router.post("/evaluate", dependencies=_AUTH)
async def evaluate_ai_policy(
    body: AiPolicyEvaluateBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    try:
        return _STORE.evaluate(
            tenant_id=str(tenant_id),
            data_class=body.data_class,
            requested_model_tier=body.requested_model_tier,
            sample_text=body.sample_text,
            policy_id=body.policy_id,
        )
    except AiPolicyError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/{policy_id}", response_model=AiPolicyResponse, dependencies=_AUTH)
async def get_ai_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> AiPolicyResponse:
    row = _STORE.get(policy_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="ai policy not found")
    return AiPolicyResponse.model_validate(row.as_dict())


@router.delete("/{policy_id}", dependencies=_AUTH)
async def delete_ai_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    ok = _STORE.delete(policy_id, tenant_id=str(tenant_id))
    if not ok:
        raise HTTPException(status_code=404, detail="ai policy not found")
    return {"deleted": True, "id": policy_id}


def bind_store(store: MemAiPoliciesStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
