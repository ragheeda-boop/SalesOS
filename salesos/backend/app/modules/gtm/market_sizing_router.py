"""STORY-11-02 — GTM Market Sizing HTTP (CAP-096 TAM/SAM/SOM).

Compute against company universe port (gov-dataset-shaped filters).
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.market_sizing import (
    GOVERNMENT_DATASET_SCALE_HINT,
    MarketSizingError,
)
from app.modules.gtm.market_sizing_store import (
    DEFAULT_MARKET_SIZING_STORE,
    MemMarketSizingStore,
)

router = APIRouter(prefix="/gtm/market-sizing", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_MARKET_SIZING_STORE


class MarketSizingComputeBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    employees_min: int | None = None
    employees_max: int | None = None
    id: str | None = None


class MarketSizingResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    criteria: dict[str, Any]
    tam: int
    sam: int
    som: int
    universe_size: int
    dataset_scale_hint: int = GOVERNMENT_DATASET_SCALE_HINT
    schema_version: int = 1
    created_at: str = ""
    invariant_ok: bool = True


@router.get("/meta", dependencies=_AUTH)
async def market_sizing_meta() -> dict[str, Any]:
    return {
        "dataset_scale_hint": GOVERNMENT_DATASET_SCALE_HINT,
        "filters": ["industries", "cities", "employees_min", "employees_max"],
        "invariant": "SOM <= SAM <= TAM <= universe_size",
        "honesty": (
            "CI uses gov-dataset-shaped in-memory universe; "
            "live 141221 count requires Postgres CompanyUniverse adapter "
            "(not claimed here)."
        ),
    }


@router.post("", response_model=MarketSizingResponse, dependencies=_AUTH)
async def compute_market_sizing(
    body: MarketSizingComputeBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> MarketSizingResponse:
    try:
        snap = _STORE.compute(
            tenant_id=str(tenant_id),
            name=body.name,
            industries=list(body.industries),
            cities=list(body.cities),
            employees_min=body.employees_min,
            employees_max=body.employees_max,
            snapshot_id=body.id,
        )
    except MarketSizingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return MarketSizingResponse.model_validate(snap.as_dict())


@router.get("", response_model=list[MarketSizingResponse], dependencies=_AUTH)
async def list_market_sizing(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[MarketSizingResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [MarketSizingResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{snapshot_id}", response_model=MarketSizingResponse, dependencies=_AUTH)
async def get_market_sizing(
    snapshot_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> MarketSizingResponse:
    row = _STORE.get(snapshot_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="market sizing snapshot not found")
    return MarketSizingResponse.model_validate(row.as_dict())


def bind_store(store: MemMarketSizingStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
