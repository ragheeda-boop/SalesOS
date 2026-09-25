"""STORY-12-02 — AI Policies HTTP (CAP-091, reuses AI-GR-*).

Not Production GO. DEC-085 untouched. feature_ai_copilot remains False.
No live LLM / RAG GO.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from app.modules.tenant_studio.ai_policies import (
    AI_GUARDRAIL_CATALOG,
    VALID_DATA_CLASSES,
    VALID_MODEL_TIERS,
    AiPolicyError,
    AiPolicySet,
    DataClassRule,
)
from app.modules.tenant_studio.ai_policies_engine import evaluate_policy
from app.modules.tenant_studio.ai_policies_store import MemAiPoliciesStore
from app.modules.tenant_studio.postgres_store import PostgresTenantStudioStore

router = APIRouter(prefix="/studio/ai-policies", tags=["AI Studio"])
_AUTH = [Depends(verify_token)]


class DataClassRuleIn(BaseModel):
    data_class: str
    max_model_tier: str
    require_pii_scrub: bool = True


class AiPolicyUpsert(BaseModel):
    id: str | None = Field(default=None, max_length=64)
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
            "tenant-RLS persisted policy sets + deterministic data-class ceilings. Live LLM / RAG GO "
            "not claimed. feature_ai_copilot remains False."
        ),
    }


def _policy_from_payload(payload: dict[str, Any]) -> AiPolicySet:
    return AiPolicySet(
        id=str(payload["id"]),
        tenant_id=str(payload["tenant_id"]),
        name=str(payload["name"]),
        guardrails={str(k): bool(v) for k, v in (payload.get("guardrails") or {}).items()},
        data_class_rules=[
            DataClassRule(
                data_class=str(rule["data_class"]),
                max_model_tier=str(rule["max_model_tier"]),
                require_pii_scrub=bool(rule.get("require_pii_scrub", True)),
            )
            for rule in payload.get("data_class_rules", [])
        ],
        schema_version=int(payload.get("schema_version") or 1),
        created_at=str(payload.get("created_at") or ""),
        updated_at=str(payload.get("updated_at") or ""),
    )


@router.post("", response_model=AiPolicyResponse, dependencies=_AUTH)
async def upsert_ai_policy(
    body: AiPolicyUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> AiPolicyResponse:
    try:
        repository = PostgresTenantStudioStore(db)
        existing = (
            await repository.get(
                tenant_id=str(tenant_id),
                document_type="ai_policies",
                document_key=body.id,
            )
            if body.id
            else None
        )
        memory_store = MemAiPoliciesStore()
        row = memory_store.upsert(
            tenant_id=str(tenant_id),
            name=body.name,
            guardrails=body.guardrails or None,
            data_class_rules=[r.model_dump() for r in body.data_class_rules] or None,
            policy_id=body.id or (str(existing["id"]) if existing else None),
        )
        if existing:
            row.schema_version = int(existing.get("schema_version") or 1) + 1
            row.created_at = str(existing.get("created_at") or row.created_at)
        if existing:
            stored = await repository.replace_if_version(
                tenant_id=str(tenant_id),
                document_type="ai_policies",
                document_key=row.id,
                payload=row.as_dict(),
                expected_schema_version=int(existing.get("schema_version") or 1),
            )
            if stored is None:
                raise HTTPException(status_code=409, detail="policy changed; reload and retry")
        else:
            stored = await repository.create(
                tenant_id=str(tenant_id),
                document_type="ai_policies",
                document_key=row.id,
                payload=row.as_dict(),
            )
            if stored is None:
                raise HTTPException(status_code=409, detail="policy id already exists")
    except AiPolicyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return AiPolicyResponse.model_validate(stored)


@router.get("", response_model=list[AiPolicyResponse], dependencies=_AUTH)
async def list_ai_policies(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> list[AiPolicyResponse]:
    repository = PostgresTenantStudioStore(db)
    rows = await repository.list_for_tenant(tenant_id=str(tenant_id), document_type="ai_policies")
    if not rows:
        memory_store = MemAiPoliciesStore()
        default = memory_store.ensure_default(tenant_id=str(tenant_id)).as_dict()
        stored = await repository.create(
            tenant_id=str(tenant_id),
            document_type="ai_policies",
            document_key=str(default["id"]),
            payload=default,
        )
        rows = (
            [stored]
            if stored is not None
            else await repository.list_for_tenant(
                tenant_id=str(tenant_id), document_type="ai_policies"
            )
        )
    return [AiPolicyResponse.model_validate(row) for row in rows]


@router.post("/evaluate", dependencies=_AUTH)
async def evaluate_ai_policy(
    body: AiPolicyEvaluateBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        repository = PostgresTenantStudioStore(db)
        if body.policy_id:
            payload = await repository.get(
                tenant_id=str(tenant_id),
                document_type="ai_policies",
                document_key=body.policy_id,
            )
            if payload is None:
                raise AiPolicyError("policy not found")
        else:
            rows = await repository.list_for_tenant(
                tenant_id=str(tenant_id), document_type="ai_policies"
            )
            if rows:
                payload = rows[0]
            else:
                memory_store = MemAiPoliciesStore()
                payload = memory_store.ensure_default(tenant_id=str(tenant_id)).as_dict()
                created = await repository.create(
                    tenant_id=str(tenant_id),
                    document_type="ai_policies",
                    document_key=str(payload["id"]),
                    payload=payload,
                )
                if created is not None:
                    payload = created
                else:
                    existing = await repository.list_for_tenant(
                        tenant_id=str(tenant_id), document_type="ai_policies"
                    )
                    if not existing:
                        raise AiPolicyError("default policy could not be initialized")
                    payload = existing[0]
        return evaluate_policy(
            _policy_from_payload(payload),
            data_class=body.data_class,
            requested_model_tier=body.requested_model_tier,
            sample_text=body.sample_text,
        )
    except AiPolicyError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/{policy_id}", response_model=AiPolicyResponse, dependencies=_AUTH)
async def get_ai_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> AiPolicyResponse:
    payload = await PostgresTenantStudioStore(db).get(
        tenant_id=str(tenant_id), document_type="ai_policies", document_key=policy_id
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="ai policy not found")
    return AiPolicyResponse.model_validate(payload)


@router.delete("/{policy_id}", dependencies=_AUTH)
async def delete_ai_policy(
    policy_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    ok = await PostgresTenantStudioStore(db).delete(
        tenant_id=str(tenant_id), document_type="ai_policies", document_key=policy_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="ai policy not found")
    return {"deleted": True, "id": policy_id}
