"""STORY-12-03 — AI Memory HTTP (CAP-063 conversation-level MVP).

Opt-in tenant memory. Not Production GO. DEC-085 untouched.
feature_ai_copilot remains False. No live LLM / RAG GO.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.ai_memory import (
    DEFAULT_MAX_TURNS,
    DEFAULT_RETENTION_HOURS,
    AiMemoryError,
)
from app.modules.tenant_studio.ai_memory_store import (
    DEFAULT_AI_MEMORY_STORE,
    MemAiMemoryStore,
)

router = APIRouter(prefix="/studio/ai-memory", tags=["AI Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_AI_MEMORY_STORE


class MemorySettingsBody(BaseModel):
    enabled: bool = False
    max_turns: int = Field(default=DEFAULT_MAX_TURNS, ge=1, le=200)
    retention_hours: int = Field(default=DEFAULT_RETENTION_HOURS, ge=1, le=168)


class MemoryTurnBody(BaseModel):
    role: str = Field(..., min_length=1, max_length=16)
    content: str = Field(..., min_length=1, max_length=8000)


class AdversarialProbeBody(BaseModel):
    owner_tenant_id: str = Field(..., min_length=1, max_length=64)
    attacker_tenant_id: str = Field(..., min_length=1, max_length=64)
    conversation_id: str = Field(..., min_length=1, max_length=128)


class MemoryTurnResponse(BaseModel):
    role: str
    content: str
    created_at: str = ""
    encryption: dict[str, str] = Field(default_factory=dict)


class ConversationMemoryResponse(BaseModel):
    id: str
    tenant_id: str
    conversation_id: str
    turns: list[MemoryTurnResponse]
    turn_count: int = 0
    provider_cache_key: str = ""
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""
    scope: str = "conversation"


class MemorySettingsResponse(BaseModel):
    tenant_id: str
    enabled: bool = False
    max_turns: int = DEFAULT_MAX_TURNS
    retention_hours: int = DEFAULT_RETENTION_HOURS
    updated_at: str = ""
    opt_in: bool = True
    cross_session: bool = False
    feature_ai_copilot: bool = False


@router.get("/meta", dependencies=_AUTH)
async def ai_memory_meta() -> dict[str, Any]:
    return {
        "object": "ConversationMemory",
        "capability": "CAP-063",
        "scope": "conversation",
        "cross_session": False,
        "opt_in_default": False,
        "retention_policy": (
            f"Conversation-scoped only; default max_turns={DEFAULT_MAX_TURNS}, "
            f"retention_hours={DEFAULT_RETENTION_HOURS}. Cross-session long-term "
            "memory deferred (DEC-007)."
        ),
        "provider_cache": "tenant-bound fixture keys (pcm:…:t=<tenant_id>:…)",
        "encryption": "fixture-hmac-sha256-v1 tenant-bound at-rest envelope (not KMS)",
        "deletion_policy": "DELETE /conversations/{id} + retention_hours auto-purge",
        "policy_count_delta": 0,
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": (
            "In-memory CI store; opt-in per tenant. Live LLM / RAG GO / "
            "cross-session memory not claimed. feature_ai_copilot remains False. "
            "FE Decision package is STUB."
        ),
    }


@router.get("/settings", response_model=MemorySettingsResponse, dependencies=_AUTH)
async def get_memory_settings(
    tenant_id: str = Depends(get_current_tenant_id),
) -> MemorySettingsResponse:
    row = _STORE.get_settings(tenant_id=str(tenant_id))
    return MemorySettingsResponse.model_validate(row.as_dict())


@router.put("/settings", response_model=MemorySettingsResponse, dependencies=_AUTH)
async def put_memory_settings(
    body: MemorySettingsBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> MemorySettingsResponse:
    try:
        row = _STORE.set_settings(
            tenant_id=str(tenant_id),
            enabled=body.enabled,
            max_turns=body.max_turns,
            retention_hours=body.retention_hours,
        )
    except AiMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MemorySettingsResponse.model_validate(row.as_dict())


@router.get("/conversations", response_model=list[ConversationMemoryResponse], dependencies=_AUTH)
async def list_conversations(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[ConversationMemoryResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [ConversationMemoryResponse.model_validate(r.as_dict()) for r in rows]


@router.post(
    "/conversations/{conversation_id}/turns",
    response_model=ConversationMemoryResponse,
    dependencies=_AUTH,
)
async def append_turn(
    conversation_id: str,
    body: MemoryTurnBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ConversationMemoryResponse:
    try:
        row = _STORE.append_turn(
            tenant_id=str(tenant_id),
            conversation_id=conversation_id,
            role=body.role,
            content=body.content,
        )
    except AiMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConversationMemoryResponse.model_validate(row.as_dict())


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationMemoryResponse,
    dependencies=_AUTH,
)
async def get_conversation(
    conversation_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ConversationMemoryResponse:
    try:
        row = _STORE.get_conversation(
            tenant_id=str(tenant_id),
            conversation_id=conversation_id,
        )
    except AiMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="conversation memory not found")
    return ConversationMemoryResponse.model_validate(row.as_dict())


@router.delete("/conversations/{conversation_id}", dependencies=_AUTH)
async def delete_conversation(
    conversation_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    try:
        ok = _STORE.delete_conversation(
            tenant_id=str(tenant_id),
            conversation_id=conversation_id,
        )
    except AiMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=404, detail="conversation memory not found")
    return {"deleted": True, "conversation_id": conversation_id}


@router.post("/adversarial/probe", dependencies=_AUTH)
async def adversarial_probe(
    body: AdversarialProbeBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """CI/ops probe helper — does not invent live LLM. Auth required."""
    _ = tenant_id  # caller must be authenticated; probe uses explicit tenant ids
    try:
        return _STORE.adversarial_isolation_report(
            owner_tenant_id=body.owner_tenant_id,
            attacker_tenant_id=body.attacker_tenant_id,
            conversation_id=body.conversation_id,
        )
    except AiMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def bind_store(store: MemAiMemoryStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
