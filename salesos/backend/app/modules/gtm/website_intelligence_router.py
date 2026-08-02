"""STORY-11-07 — GTM Website Intelligence HTTP (CAP-101 / OBJ-355).

Reuses platform Prompt Registry spend path — no Claygent/Clay vendor call.
Not Production GO. DEC-085 untouched. feature_ai_copilot remains False.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.website_intelligence import (
    WEBSITE_INTEL_PROMPT_ID,
    WEBSITE_INTEL_PROMPT_VERSION,
    WebsiteIntelligenceError,
)
from app.modules.gtm.website_intelligence_store import (
    DEFAULT_WEBSITE_INTEL_STORE,
    MemWebsiteIntelligenceStore,
)

router = APIRouter(prefix="/gtm/website-intelligence", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_WEBSITE_INTEL_STORE


class WebsiteIntelligenceBody(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    company_name: str = ""
    page_snippet: str = ""
    analyzer_key: str = ""
    id: str | None = None


class WebsiteSignalResponse(BaseModel):
    key: str
    value: str
    confidence: float = 0.0


class WebsiteIntelligenceResponse(BaseModel):
    id: str
    tenant_id: str
    request: dict[str, Any]
    summary: str = ""
    signals: list[WebsiteSignalResponse]
    prompt_id: str = WEBSITE_INTEL_PROMPT_ID
    prompt_version: str = WEBSITE_INTEL_PROMPT_VERSION
    spend_path: str = "platform_llm_budget"
    analyzer_key: str = "fixture_website"
    schema_version: int = 1
    created_at: str = ""
    signal_count: int = 0


@router.get("/meta", dependencies=_AUTH)
async def website_intelligence_meta() -> dict[str, Any]:
    return {
        "object": "WebsiteIntelligenceSnapshot",
        "capability": "CAP-101",
        "prompt_id": WEBSITE_INTEL_PROMPT_ID,
        "prompt_version": WEBSITE_INTEL_PROMPT_VERSION,
        "spend_path": "platform_llm_budget (CAP-023/024 — no separate per-row vendor)",
        "analyzers_configured": _STORE.analyzer_keys(),
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "honesty": (
            "CI uses FixtureWebsiteAnalyzer + governed prompt-registry key "
            f"{WEBSITE_INTEL_PROMPT_ID}; live crawl / live LLM / Claygent / RAG GO "
            "not claimed. feature_ai_copilot remains False. FE Decision package is STUB."
        ),
    }


@router.post("", response_model=WebsiteIntelligenceResponse, dependencies=_AUTH)
async def run_website_intelligence(
    body: WebsiteIntelligenceBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> WebsiteIntelligenceResponse:
    try:
        row = await _STORE.analyze(
            tenant_id=str(tenant_id),
            url=body.url,
            company_name=body.company_name or None,
            page_snippet=body.page_snippet or None,
            analyzer_key=body.analyzer_key or None,
            run_id=body.id,
        )
    except WebsiteIntelligenceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return WebsiteIntelligenceResponse.model_validate(row.as_dict())


@router.get("", response_model=list[WebsiteIntelligenceResponse], dependencies=_AUTH)
async def list_website_intelligence(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[WebsiteIntelligenceResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [WebsiteIntelligenceResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{run_id}", response_model=WebsiteIntelligenceResponse, dependencies=_AUTH)
async def get_website_intelligence(
    run_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> WebsiteIntelligenceResponse:
    row = _STORE.get(run_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="website intelligence snapshot not found")
    return WebsiteIntelligenceResponse.model_validate(row.as_dict())


def bind_store(store: MemWebsiteIntelligenceStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
