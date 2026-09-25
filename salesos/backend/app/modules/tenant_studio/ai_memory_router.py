"""STORY-12-03 — AI Memory HTTP (CAP-063 conversation-level MVP).

Opt-in tenant memory. feature_ai_copilot is gated by settings.feature_ai_copilot.
Conversation turns are encrypted before tenant-scoped PostgreSQL persistence.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from app.modules.tenant_studio.ai_memory import (
    DEFAULT_MAX_TURNS,
    DEFAULT_RETENTION_HOURS,
    AiMemoryError,
)
from app.modules.tenant_studio.postgres_ai_memory_store import PostgresAiMemoryStore

router = APIRouter(prefix="/studio/ai-memory", tags=["AI Studio"])
_AUTH = [Depends(verify_token)]

class MemorySettingsBody(BaseModel):
    enabled: bool = False
    max_turns: int = Field(default=DEFAULT_MAX_TURNS, ge=1, le=200)
    retention_hours: int = Field(default=DEFAULT_RETENTION_HOURS, ge=1, le=168)


class MemoryTurnBody(BaseModel):
    role: str = Field(..., min_length=1, max_length=16)
    content: str = Field(..., min_length=1, max_length=8000)


class AdversarialProbeBody(BaseModel):
    owner_tenant_id: UUID
    attacker_tenant_id: UUID
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
    feature_ai_copilot: bool = False  # overridden at runtime by settings


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
        "encryption": "Fernet application encryption with tenant-derived keys; requires AI_MEMORY_ENCRYPTION_KEY",
        "deletion_policy": "DELETE /conversations/{id}, opt-out purge, and retention_hours auto-purge",
        "policy_count_delta": 0,
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": (
            "Encrypted tenant-scoped PostgreSQL persistence; opt-in per tenant. "
            "Live LLM / RAG GO / cross-session recall not claimed. Copilot remains "
            "gated by settings.feature_ai_copilot. Key rotation is an operator-managed prerequisite."
        ),
    }


@router.get("/settings", response_model=MemorySettingsResponse, dependencies=_AUTH)
async def get_memory_settings(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> MemorySettingsResponse:
    row = await PostgresAiMemoryStore(db).get_settings(tenant_id=str(tenant_id))
    return MemorySettingsResponse.model_validate(row.as_dict())


@router.put("/settings", response_model=MemorySettingsResponse, dependencies=_AUTH)
async def put_memory_settings(
    body: MemorySettingsBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> MemorySettingsResponse:
    try:
        row = await PostgresAiMemoryStore(db).set_settings(
            tenant_id=str(tenant_id),
            enabled=body.enabled,
            max_turns=body.max_turns,
            retention_hours=body.retention_hours,
        )
    except AiMemoryError as exc:
        status = 503 if "encryption key is not configured" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return MemorySettingsResponse.model_validate(row.as_dict())


@router.get("/conversations", response_model=list[ConversationMemoryResponse], dependencies=_AUTH)
async def list_conversations(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> list[ConversationMemoryResponse]:
    try:
        rows = await PostgresAiMemoryStore(db).list_for_tenant(tenant_id=str(tenant_id))
    except AiMemoryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
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
    db: AsyncSession = Depends(get_db_session),
) -> ConversationMemoryResponse:
    try:
        row = await PostgresAiMemoryStore(db).append_turn(
            tenant_id=str(tenant_id),
            conversation_id=conversation_id,
            role=body.role,
            content=body.content,
        )
    except AiMemoryError as exc:
        status = 503 if "encryption key is not configured" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return ConversationMemoryResponse.model_validate(row.as_dict())


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationMemoryResponse,
    dependencies=_AUTH,
)
async def get_conversation(
    conversation_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ConversationMemoryResponse:
    try:
        row = await PostgresAiMemoryStore(db).get_conversation(
            tenant_id=str(tenant_id),
            conversation_id=conversation_id,
        )
    except AiMemoryError as exc:
        status = 503 if "encryption key is not configured" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="conversation memory not found")
    return ConversationMemoryResponse.model_validate(row.as_dict())


@router.delete("/conversations/{conversation_id}", dependencies=_AUTH)
async def delete_conversation(
    conversation_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        ok = await PostgresAiMemoryStore(db).delete_conversation(
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
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Development-only tenant isolation probe; never usable as cross-tenant access."""
    if str(settings.env).lower() in {"production", "prod", "staging"}:
        raise HTTPException(status_code=404, detail="probe is unavailable")
    if body.owner_tenant_id != UUID(tenant_id):
        raise HTTPException(status_code=403, detail="probe owner must match authenticated tenant")
    try:
        return await PostgresAiMemoryStore(db).adversarial_isolation_report(
            owner_tenant_id=str(body.owner_tenant_id),
            attacker_tenant_id=str(body.attacker_tenant_id),
            conversation_id=body.conversation_id,
        )
    except AiMemoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
