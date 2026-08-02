"""STORY-11-05 — GTM Enrichment Waterfall HTTP (CAP-099).

≥2 swappable providers; first non-empty value wins per field.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.enrichment import ENRICHABLE_FIELDS, EnrichmentError
from app.modules.gtm.enrichment_store import (
    DEFAULT_ENRICHMENT_STORE,
    MemEnrichmentStore,
)

router = APIRouter(prefix="/gtm/enrichment", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_ENRICHMENT_STORE


class EnrichmentBody(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    domain: str = ""
    external_id: str = ""
    known: dict[str, Any] = Field(default_factory=dict)
    provider_order: list[str] = Field(default_factory=list)
    id: str | None = None


class EnrichmentHitResponse(BaseModel):
    field: str
    value: Any
    provider_key: str


class EnrichmentResponse(BaseModel):
    id: str
    tenant_id: str
    request: dict[str, Any]
    filled: dict[str, Any]
    hits: list[EnrichmentHitResponse]
    providers_attempted: list[str]
    providers_configured: list[str]
    missing_fields: list[str]
    schema_version: int = 1
    created_at: str = ""
    complete: bool = False


@router.get("/meta", dependencies=_AUTH)
async def enrichment_meta() -> dict[str, Any]:
    return {
        "enrichable_fields": list(ENRICHABLE_FIELDS),
        "providers_configured": _STORE.provider_keys(),
        "policy": "first non-empty value wins per field; ≥2 swappable providers",
        "honesty": (
            "CI uses in-memory FakeEnrichment providers (fake_a/fake_b); "
            "live Clearbit/Apollo/ERP enrichment not claimed."
        ),
    }


@router.post("", response_model=EnrichmentResponse, dependencies=_AUTH)
async def run_enrichment(
    body: EnrichmentBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrichmentResponse:
    try:
        row = await _STORE.enrich(
            tenant_id=str(tenant_id),
            company_name=body.company_name,
            domain=body.domain,
            external_id=body.external_id,
            known=dict(body.known),
            provider_order=list(body.provider_order),
            run_id=body.id,
        )
    except EnrichmentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return EnrichmentResponse.model_validate(row.as_dict())


@router.get("", response_model=list[EnrichmentResponse], dependencies=_AUTH)
async def list_enrichment(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[EnrichmentResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [EnrichmentResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{run_id}", response_model=EnrichmentResponse, dependencies=_AUTH)
async def get_enrichment(
    run_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrichmentResponse:
    row = _STORE.get(run_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="enrichment run not found")
    return EnrichmentResponse.model_validate(row.as_dict())


def bind_store(store: MemEnrichmentStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
