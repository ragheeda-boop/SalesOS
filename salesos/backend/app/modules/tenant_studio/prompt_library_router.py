"""STORY-12-01 — Prompt Library HTTP (CAP-089, extends CAP-023).

Tenant CRUD + versioning + rollback. Not Production GO. DEC-085 untouched.
feature_ai_copilot remains False. No live LLM / RAG GO.

EAB-001-P1-DUP-02 quarantine: dual prompt surface with ``app.routers.ai``
``/api/v1/ai/prompts*`` — Studio library is experimental, not single SoT.
See CAPABILITY-DUP-REGISTER.md. Do not remount as mega Prompt API without DEC.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from app.modules.tenant_studio.postgres_store import PostgresTenantStudioStore
from app.modules.tenant_studio.prompt_library import (
    PromptLibraryEntry,
    PromptLibraryError,
    PromptVersionRecord,
)
from app.modules.tenant_studio.prompt_library_store import MemPromptLibraryStore

router = APIRouter(
    prefix="/studio/prompt-library",
    tags=["AI Studio (experimental; prompt dual-registry)"],
)
_AUTH = [Depends(verify_token)]


class PromptCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    key: str = Field(..., min_length=1, max_length=128)
    template: str = Field(..., min_length=1, max_length=20000)
    system: str = ""
    version: str = "1.0.0"
    changelog: str = "initial"
    domain: str = "gtm"
    category: str = "general"
    id: str | None = Field(default=None, max_length=64)


class PromptVersionBody(BaseModel):
    template: str = Field(..., min_length=1, max_length=20000)
    version: str = Field(..., min_length=1, max_length=32)
    system: str = ""
    changelog: str = ""
    activate: bool = True


class PromptRollbackBody(BaseModel):
    version: str = Field(..., min_length=1, max_length=32)


class PromptMetaBody(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    domain: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)


class PromptVersionResponse(BaseModel):
    version: str
    template: str
    system: str = ""
    changelog: str = ""
    created_at: str = ""


class PromptLibraryResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    key: str
    active_version: str
    versions: list[PromptVersionResponse]
    domain: str = "gtm"
    category: str = "general"
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""
    version_count: int = 0


@router.get("/meta", dependencies=_AUTH)
async def prompt_library_meta() -> dict[str, Any]:
    return {
        "object": "PromptLibraryEntry",
        "capability": "CAP-089",
        "extends": "CAP-023 AI Prompt Registry",
        "operations": ["create", "list", "get", "add_version", "rollback", "delete"],
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": (
            "DUP-02: dual with /api/v1/ai/prompts* — not single prompt SoT. "
            "Tenant Prompt Library is persisted with tenant RLS; it is not the canonical "
            "CAP-023 registry. Live LLM execution / RAG GO / Marketplace prompt-pack install "
            "not claimed. "
            "feature_ai_copilot remains False."
        ),
    }


def _entry_from_payload(payload: dict[str, Any]) -> PromptLibraryEntry:
    return PromptLibraryEntry(
        id=str(payload["id"]),
        tenant_id=str(payload["tenant_id"]),
        name=str(payload["name"]),
        key=str(payload["key"]),
        active_version=str(payload["active_version"]),
        versions=[PromptVersionRecord(**version) for version in payload.get("versions", [])],
        domain=str(payload.get("domain") or "gtm"),
        category=str(payload.get("category") or "general"),
        schema_version=int(payload.get("schema_version") or 1),
        created_at=str(payload.get("created_at") or ""),
        updated_at=str(payload.get("updated_at") or ""),
    )


@router.post("", response_model=PromptLibraryResponse, dependencies=_AUTH)
async def create_prompt(
    body: PromptCreateBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> PromptLibraryResponse:
    try:
        row = MemPromptLibraryStore().create(
            tenant_id=str(tenant_id),
            name=body.name,
            key=body.key,
            template=body.template,
            system=body.system,
            version=body.version,
            changelog=body.changelog,
            domain=body.domain,
            category=body.category,
            entry_id=body.id,
        )
        stored = await PostgresTenantStudioStore(db).create(
            tenant_id=str(tenant_id),
            document_type="prompt_library",
            document_key=row.id,
            logical_key=row.key,
            payload=row.as_dict(),
        )
        if stored is None:
            raise PromptLibraryError("prompt key or id already exists")
    except PromptLibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return PromptLibraryResponse.model_validate(stored)


@router.get("", response_model=list[PromptLibraryResponse], dependencies=_AUTH)
async def list_prompts(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> list[PromptLibraryResponse]:
    rows = await PostgresTenantStudioStore(db).list_for_tenant(
        tenant_id=str(tenant_id), document_type="prompt_library"
    )
    return [PromptLibraryResponse.model_validate(row) for row in rows]


@router.get("/{entry_id}", response_model=PromptLibraryResponse, dependencies=_AUTH)
async def get_prompt(
    entry_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> PromptLibraryResponse:
    payload = await PostgresTenantStudioStore(db).get(
        tenant_id=str(tenant_id), document_type="prompt_library", document_key=entry_id
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    return PromptLibraryResponse.model_validate(payload)


@router.patch("/{entry_id}", response_model=PromptLibraryResponse, dependencies=_AUTH)
async def patch_prompt_meta(
    entry_id: str,
    body: PromptMetaBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> PromptLibraryResponse:
    repository = PostgresTenantStudioStore(db)
    payload = await repository.get(
        tenant_id=str(tenant_id), document_type="prompt_library", document_key=entry_id
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    try:
        memory_store = MemPromptLibraryStore()
        memory_store.restore(_entry_from_payload(payload))
        row = memory_store.update_meta(
            tenant_id=str(tenant_id),
            entry_id=entry_id,
            name=body.name,
            domain=body.domain,
            category=body.category,
        )
        stored = await repository.replace_if_version(
            tenant_id=str(tenant_id),
            document_type="prompt_library",
            document_key=entry_id,
            logical_key=row.key,
            payload=row.as_dict(),
            expected_schema_version=int(payload.get("schema_version") or 1),
        )
    except PromptLibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if stored is None:
        raise HTTPException(status_code=409, detail="prompt changed; reload and retry")
    return PromptLibraryResponse.model_validate(stored)


@router.post(
    "/{entry_id}/versions",
    response_model=PromptLibraryResponse,
    dependencies=_AUTH,
)
async def add_prompt_version(
    entry_id: str,
    body: PromptVersionBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> PromptLibraryResponse:
    repository = PostgresTenantStudioStore(db)
    payload = await repository.get(
        tenant_id=str(tenant_id), document_type="prompt_library", document_key=entry_id
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    try:
        memory_store = MemPromptLibraryStore()
        memory_store.restore(_entry_from_payload(payload))
        row = memory_store.add_version(
            tenant_id=str(tenant_id),
            entry_id=entry_id,
            template=body.template,
            version=body.version,
            system=body.system,
            changelog=body.changelog,
            activate=body.activate,
        )
        stored = await repository.replace_if_version(
            tenant_id=str(tenant_id),
            document_type="prompt_library",
            document_key=entry_id,
            logical_key=row.key,
            payload=row.as_dict(),
            expected_schema_version=int(payload.get("schema_version") or 1),
        )
    except PromptLibraryError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    if stored is None:
        raise HTTPException(status_code=409, detail="prompt changed; reload and retry")
    return PromptLibraryResponse.model_validate(stored)


@router.post(
    "/{entry_id}/rollback",
    response_model=PromptLibraryResponse,
    dependencies=_AUTH,
)
async def rollback_prompt(
    entry_id: str,
    body: PromptRollbackBody,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> PromptLibraryResponse:
    repository = PostgresTenantStudioStore(db)
    payload = await repository.get(
        tenant_id=str(tenant_id), document_type="prompt_library", document_key=entry_id
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    try:
        memory_store = MemPromptLibraryStore()
        memory_store.restore(_entry_from_payload(payload))
        row = memory_store.rollback(
            tenant_id=str(tenant_id),
            entry_id=entry_id,
            version=body.version,
        )
        row.updated_at = datetime.now(UTC).isoformat()
        stored = await repository.replace_if_version(
            tenant_id=str(tenant_id),
            document_type="prompt_library",
            document_key=entry_id,
            logical_key=row.key,
            payload=row.as_dict(),
            expected_schema_version=int(payload.get("schema_version") or 1),
        )
    except PromptLibraryError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    if stored is None:
        raise HTTPException(status_code=409, detail="prompt changed; reload and retry")
    return PromptLibraryResponse.model_validate(stored)


@router.delete("/{entry_id}", dependencies=_AUTH)
async def delete_prompt(
    entry_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    ok = await PostgresTenantStudioStore(db).delete(
        tenant_id=str(tenant_id), document_type="prompt_library", document_key=entry_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    return {"deleted": True, "id": entry_id}
