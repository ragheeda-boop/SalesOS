"""STORY-11-08 — GTM AI Outreach HTTP (CAP-103).

Routed through governed Prompt Registry spend path — not a disconnected tool.
Not Production GO. DEC-085 untouched. feature_ai_copilot remains False.
No live SMTP / LinkedIn / WhatsApp.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.outreach import (
    OUTREACH_PROMPT_ID,
    OUTREACH_PROMPT_VERSION,
    OutreachError,
)
from app.modules.gtm.outreach_store import (
    DEFAULT_OUTREACH_STORE,
    MemOutreachStore,
)

router = APIRouter(prefix="/gtm/outreach", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_OUTREACH_STORE


class OutreachBody(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    contact_name: str = ""
    contact_title: str = ""
    channel: str = "email"
    intent: str = "intro"
    value_prop: str = ""
    website_summary: str = ""
    icp_notes: str = ""
    generator_key: str = ""
    id: str | None = None


class OutreachResponse(BaseModel):
    id: str
    tenant_id: str
    request: dict[str, Any]
    subject: str = ""
    body: str = ""
    channel: str = "email"
    prompt_id: str = OUTREACH_PROMPT_ID
    prompt_version: str = OUTREACH_PROMPT_VERSION
    spend_path: str = "platform_llm_budget"
    generator_key: str = "fixture_outreach"
    delivery_status: str = "draft_only"
    schema_version: int = 1
    created_at: str = ""
    warnings: list[str] = Field(default_factory=list)


@router.get("/meta", dependencies=_AUTH)
async def outreach_meta() -> dict[str, Any]:
    return {
        "object": "OutreachDraft",
        "capability": "CAP-103",
        "prompt_id": OUTREACH_PROMPT_ID,
        "prompt_version": OUTREACH_PROMPT_VERSION,
        "channels": ["email"],
        "intents": ["intro", "follow_up", "breakup"],
        "spend_path": "platform_llm_budget (CAP-023 Prompt Registry — not disconnected tool)",
        "generators_configured": _STORE.generator_keys(),
        "delivery_status": "draft_only",
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": (
            "CI uses FixtureOutreachGenerator + governed prompt-registry key "
            f"{OUTREACH_PROMPT_ID}; live LLM / SMTP / LinkedIn / WhatsApp / RAG GO "
            "not claimed. feature_ai_copilot remains False. FE Decision package is STUB."
        ),
    }


@router.post("", response_model=OutreachResponse, dependencies=_AUTH)
async def create_outreach_draft(
    body: OutreachBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> OutreachResponse:
    try:
        row = await _STORE.draft(
            tenant_id=str(tenant_id),
            company_name=body.company_name,
            contact_name=body.contact_name or None,
            contact_title=body.contact_title or None,
            channel=body.channel or None,
            intent=body.intent or None,
            value_prop=body.value_prop or None,
            website_summary=body.website_summary or None,
            icp_notes=body.icp_notes or None,
            generator_key=body.generator_key or None,
            run_id=body.id,
        )
    except OutreachError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return OutreachResponse.model_validate(row.as_dict())


@router.get("", response_model=list[OutreachResponse], dependencies=_AUTH)
async def list_outreach_drafts(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[OutreachResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [OutreachResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{run_id}", response_model=OutreachResponse, dependencies=_AUTH)
async def get_outreach_draft(
    run_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> OutreachResponse:
    row = _STORE.get(run_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="outreach draft not found")
    return OutreachResponse.model_validate(row.as_dict())


def bind_store(store: MemOutreachStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
