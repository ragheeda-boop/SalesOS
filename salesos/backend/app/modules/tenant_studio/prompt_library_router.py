"""STORY-12-01 — Prompt Library HTTP (CAP-089, extends CAP-023).

Tenant CRUD + versioning + rollback. Not Production GO. DEC-085 untouched.
feature_ai_copilot remains False. No live LLM / RAG GO.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.prompt_library import PromptLibraryError
from app.modules.tenant_studio.prompt_library_store import (
    DEFAULT_PROMPT_LIBRARY_STORE,
    MemPromptLibraryStore,
)

router = APIRouter(prefix="/studio/prompt-library", tags=["AI Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_PROMPT_LIBRARY_STORE


class PromptCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    key: str = Field(..., min_length=1, max_length=128)
    template: str = Field(..., min_length=1, max_length=20000)
    system: str = ""
    version: str = "1.0.0"
    changelog: str = "initial"
    domain: str = "gtm"
    category: str = "general"
    id: str | None = None


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
            "Tenant Prompt Library is in-memory CI store extending CAP-023 shape; "
            "live LLM execution / RAG GO / Marketplace prompt-pack install not claimed. "
            "feature_ai_copilot remains False."
        ),
    }


@router.post("", response_model=PromptLibraryResponse, dependencies=_AUTH)
async def create_prompt(
    body: PromptCreateBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> PromptLibraryResponse:
    try:
        row = _STORE.create(
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
    except PromptLibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return PromptLibraryResponse.model_validate(row.as_dict())


@router.get("", response_model=list[PromptLibraryResponse], dependencies=_AUTH)
async def list_prompts(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[PromptLibraryResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [PromptLibraryResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{entry_id}", response_model=PromptLibraryResponse, dependencies=_AUTH)
async def get_prompt(
    entry_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> PromptLibraryResponse:
    row = _STORE.get(entry_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    return PromptLibraryResponse.model_validate(row.as_dict())


@router.patch("/{entry_id}", response_model=PromptLibraryResponse, dependencies=_AUTH)
async def patch_prompt_meta(
    entry_id: str,
    body: PromptMetaBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> PromptLibraryResponse:
    try:
        row = _STORE.update_meta(
            tenant_id=str(tenant_id),
            entry_id=entry_id,
            name=body.name,
            domain=body.domain,
            category=body.category,
        )
    except PromptLibraryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PromptLibraryResponse.model_validate(row.as_dict())


@router.post(
    "/{entry_id}/versions",
    response_model=PromptLibraryResponse,
    dependencies=_AUTH,
)
async def add_prompt_version(
    entry_id: str,
    body: PromptVersionBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> PromptLibraryResponse:
    try:
        row = _STORE.add_version(
            tenant_id=str(tenant_id),
            entry_id=entry_id,
            template=body.template,
            version=body.version,
            system=body.system,
            changelog=body.changelog,
            activate=body.activate,
        )
    except PromptLibraryError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return PromptLibraryResponse.model_validate(row.as_dict())


@router.post(
    "/{entry_id}/rollback",
    response_model=PromptLibraryResponse,
    dependencies=_AUTH,
)
async def rollback_prompt(
    entry_id: str,
    body: PromptRollbackBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> PromptLibraryResponse:
    try:
        row = _STORE.rollback(
            tenant_id=str(tenant_id),
            entry_id=entry_id,
            version=body.version,
        )
    except PromptLibraryError as exc:
        status = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return PromptLibraryResponse.model_validate(row.as_dict())


@router.delete("/{entry_id}", dependencies=_AUTH)
async def delete_prompt(
    entry_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    ok = _STORE.delete(entry_id, tenant_id=str(tenant_id))
    if not ok:
        raise HTTPException(status_code=404, detail="prompt entry not found")
    return {"deleted": True, "id": entry_id}


def bind_store(store: MemPromptLibraryStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
