"""STORY-10-07 — Tenant Studio Branding HTTP (CAP-092).

Logo / color / display name / locales live per tenant.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.branding import BrandingError
from app.modules.tenant_studio.branding_store import (
    DEFAULT_BRANDING_STORE,
    MemBrandingStore,
)

router = APIRouter(prefix="/studio/branding", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_BRANDING_STORE


class BrandingUpsert(BaseModel):
    display_name: str = Field(default="", max_length=200)
    logo_url: str = Field(default="", max_length=512)
    primary_color: str = Field(default="#0F172A", max_length=7)
    secondary_color: str = Field(default="#334155", max_length=7)
    default_locale: str = Field(default="ar", max_length=8)
    supported_locales: list[str] = Field(default_factory=lambda: ["ar", "en"])


class BrandingResponse(BaseModel):
    tenant_id: str
    display_name: str = ""
    logo_url: str = ""
    primary_color: str = "#0F172A"
    secondary_color: str = "#334155"
    default_locale: str = "ar"
    supported_locales: list[str] = Field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


@router.get("", response_model=BrandingResponse, dependencies=_AUTH)
async def get_branding(
    tenant_id: str = Depends(get_current_tenant_id),
) -> BrandingResponse:
    row = _STORE.get(tenant_id=str(tenant_id))
    return BrandingResponse.model_validate(row.as_dict())


@router.put("", response_model=BrandingResponse, dependencies=_AUTH)
async def upsert_branding(
    body: BrandingUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> BrandingResponse:
    try:
        row = _STORE.upsert(
            tenant_id=str(tenant_id),
            display_name=body.display_name,
            logo_url=body.logo_url,
            primary_color=body.primary_color,
            secondary_color=body.secondary_color,
            default_locale=body.default_locale,
            supported_locales=list(body.supported_locales),
        )
    except BrandingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BrandingResponse.model_validate(row.as_dict())


def bind_store(store: MemBrandingStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
