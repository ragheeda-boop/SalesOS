"""STORY-13-01 — MarketplaceListing HTTP (CAP-071/072 / OBJ-325).

Single object across connector/app/prompt_pack/playbook.
Not Production GO. DEC-085 untouched. No FORCE RLS.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies import verify_token
from app.modules.marketplace_listings.models import (
    VALID_LISTING_STATUSES,
    VALID_LISTING_TYPES,
    MarketplaceListingError,
)
from app.modules.marketplace_listings.store import (
    DEFAULT_MARKETPLACE_LISTING_STORE,
    MemMarketplaceListingStore,
)

router = APIRouter(prefix="/marketplace/listings", tags=["Marketplace Listings"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_MARKETPLACE_LISTING_STORE


class ListingUpsert(BaseModel):
    id: str | None = None
    slug: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    listing_type: Literal["connector", "app", "prompt_pack", "playbook"]
    version: str = Field(..., min_length=5, max_length=32)
    status: Literal[
        "draft",
        "pending_certification",
        "certified",
        "published",
        "rejected",
        "revoked",
    ] = "draft"
    description: str = Field(default="", max_length=2000)
    publisher: str = Field(default="SalesOS", max_length=128)
    first_party: bool = True
    connector_key: str = Field(default="", max_length=64)
    tags: list[str] = Field(default_factory=list)
    manifest: dict[str, Any] = Field(default_factory=dict)


class ListingResponse(BaseModel):
    id: str
    slug: str
    name: str
    listing_type: str
    version: str
    status: str
    description: str = ""
    publisher: str = "SalesOS"
    first_party: bool = True
    connector_key: str = ""
    tags: list[str] = Field(default_factory=list)
    manifest: dict[str, Any] = Field(default_factory=dict)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


@router.get("/meta", dependencies=_AUTH)
async def listings_meta() -> dict[str, Any]:
    return {
        "listing_types": sorted(VALID_LISTING_TYPES),
        "statuses": sorted(VALID_LISTING_STATUSES),
        "object": "MarketplaceListing",
        "obj_id": "OBJ-325",
        "persistence": "memory",
        "policy_count_delta": 0,
        "honesty": (
            "Catalog object only; certification pipeline is STORY-13-02. "
            "Production pilot sync / R-02 soak not claimed. Not Production GO."
        ),
    }


@router.post("/seed-first-party", response_model=list[ListingResponse], dependencies=_AUTH)
async def seed_first_party_listings() -> list[ListingResponse]:
    """Idempotent seed of Odoo + HubSpot connector listings."""
    rows = _STORE.seed_first_party_connectors()
    return [ListingResponse.model_validate(r.as_dict()) for r in rows]


@router.post("", response_model=ListingResponse, dependencies=_AUTH)
async def upsert_listing(body: ListingUpsert) -> ListingResponse:
    try:
        row = _STORE.upsert(
            slug=body.slug,
            name=body.name,
            listing_type=body.listing_type,
            version=body.version,
            status=body.status,
            description=body.description,
            publisher=body.publisher,
            first_party=body.first_party,
            connector_key=body.connector_key,
            tags=list(body.tags),
            manifest=dict(body.manifest),
            listing_id=body.id,
        )
    except MarketplaceListingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ListingResponse.model_validate(row.as_dict())


@router.get("", response_model=list[ListingResponse], dependencies=_AUTH)
async def list_listings(
    listing_type: str | None = Query(None),
    status: str | None = Query(None),
) -> list[ListingResponse]:
    rows = _STORE.list_listings(listing_type=listing_type, status=status)
    return [ListingResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{listing_id}", response_model=ListingResponse, dependencies=_AUTH)
async def get_listing(listing_id: str) -> ListingResponse:
    row = _STORE.get(listing_id)
    if row is None:
        # Allow slug lookup for FE convenience.
        row = _STORE.get_by_slug(listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="marketplace listing not found")
    return ListingResponse.model_validate(row.as_dict())


@router.delete("/{listing_id}", dependencies=_AUTH)
async def delete_listing(listing_id: str) -> dict[str, Any]:
    ok = _STORE.delete(listing_id)
    if not ok:
        raise HTTPException(status_code=404, detail="marketplace listing not found")
    return {"deleted": True, "id": listing_id}


def bind_store(store: MemMarketplaceListingStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
