"""STORY-11-03 — GTM Lead Discovery HTTP (CAP-097).

Government-data-first sourcing with Integration Hub provider fallback.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.lead_discovery import (
    LeadDiscoveryError,
)
from app.modules.gtm.lead_discovery_store import (
    DEFAULT_LEAD_DISCOVERY_STORE,
    MemLeadDiscoveryStore,
)
from app.modules.gtm.market_sizing import GOVERNMENT_DATASET_SCALE_HINT

router = APIRouter(prefix="/gtm/lead-discovery", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_LEAD_DISCOVERY_STORE


class LeadDiscoveryBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    employees_min: int | None = None
    employees_max: int | None = None
    limit: int = Field(default=25, ge=1, le=200)
    id: str | None = None
    use_provider_fallback: bool = True


class DiscoveredLeadResponse(BaseModel):
    id: str
    company_name: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    source: str
    external_id: str = ""


class LeadDiscoveryResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    query: dict[str, Any]
    leads: list[DiscoveredLeadResponse]
    government_hit_count: int
    provider_hit_count: int
    provider_key: str = ""
    dataset_scale_hint: int = GOVERNMENT_DATASET_SCALE_HINT
    schema_version: int = 1
    created_at: str = ""
    government_first_ok: bool = True
    total_hits: int = 0


@router.get("/meta", dependencies=_AUTH)
async def lead_discovery_meta() -> dict[str, Any]:
    return {
        "dataset_scale_hint": GOVERNMENT_DATASET_SCALE_HINT,
        "filters": ["industries", "cities", "employees_min", "employees_max", "limit"],
        "sourcing_order": ["government", "provider_via_integration_hub"],
        "honesty": (
            "CI uses gov-dataset-shaped in-memory universe + FakeSourceConnector "
            "provider fallback; live 141221 Postgres / live ERP pull not claimed."
        ),
    }


@router.post("", response_model=LeadDiscoveryResponse, dependencies=_AUTH)
async def run_lead_discovery(
    body: LeadDiscoveryBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> LeadDiscoveryResponse:
    try:
        run = await _STORE.discover(
            tenant_id=str(tenant_id),
            name=body.name,
            industries=list(body.industries),
            cities=list(body.cities),
            employees_min=body.employees_min,
            employees_max=body.employees_max,
            limit=body.limit,
            run_id=body.id,
            use_provider_fallback=body.use_provider_fallback,
        )
    except LeadDiscoveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return LeadDiscoveryResponse.model_validate(run.as_dict())


@router.get("", response_model=list[LeadDiscoveryResponse], dependencies=_AUTH)
async def list_lead_discovery(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[LeadDiscoveryResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [LeadDiscoveryResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{run_id}", response_model=LeadDiscoveryResponse, dependencies=_AUTH)
async def get_lead_discovery(
    run_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> LeadDiscoveryResponse:
    row = _STORE.get(run_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="lead discovery run not found")
    return LeadDiscoveryResponse.model_validate(row.as_dict())


def bind_store(store: MemLeadDiscoveryStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
