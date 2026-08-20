"""STORY-13-01/02/04 — MarketplaceListing HTTP (OBJ-325 / CAP-094 / publish pack).

Single object across connector/app/prompt_pack/playbook.
Not Production GO. DEC-085 untouched. No FORCE RLS.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import get_current_tenant_id, verify_token
from app.modules.marketplace_listings.catalog_install import (
    DEFAULT_CATALOG_INSTALL_STORE,
    MemCatalogInstallStore,
    listing_is_installable,
)
from app.modules.marketplace_listings.models import (
    VALID_LISTING_STATUSES,
    VALID_LISTING_TYPES,
    MarketplaceListingError,
)
from app.modules.marketplace_listings.pipeline import (
    run_certification_pipeline,
    submit_for_certification,
)
from app.modules.marketplace_listings.publish import publish_listing
from app.modules.marketplace_listings.store import (
    DEFAULT_MARKETPLACE_LISTING_STORE,
    MemMarketplaceListingStore,
)

router = APIRouter(prefix="/marketplace/listings", tags=["Marketplace Listings"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_MARKETPLACE_LISTING_STORE
_INSTALLS = DEFAULT_CATALOG_INSTALL_STORE


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
    installable: bool = False


def _listing_response(row: Any) -> ListingResponse:
    data = row.as_dict()
    data["installable"] = listing_is_installable(row)
    return ListingResponse.model_validate(data)


@router.get("/meta", dependencies=_AUTH)
async def listings_meta() -> dict[str, Any]:
    return {
        "listing_types": sorted(VALID_LISTING_TYPES),
        "statuses": sorted(VALID_LISTING_STATUSES),
        "object": "MarketplaceListing",
        "obj_id": "OBJ-325",
        "persistence": "memory",
        "policy_count_delta": 0,
        "publish_pack": {
            "story": "STORY-13-04",
            "min_connectors": 3,
            "min_playbooks": 1,
            "seed_slugs": [
                "connector-odoo",
                "connector-hubspot",
                "connector-rest-csv",
                "playbook-gcc-outbound",
            ],
            "connector_keys": ["odoo", "hubspot", "rest_csv"],
        },
        "honesty": (
            "Catalog + CAP-094 certify + STORY-13-04 publish pack. "
            "Catalog install ≠ live HubSpot/Odoo sync. Not Production GO."
        ),
        "certify_stages": [
            "conformance",
            "security_checklist",
            "sandboxed_trial",
        ],
    }


@router.get("/certify/meta", dependencies=_AUTH)
async def certify_pipeline_meta() -> dict[str, Any]:
    return {
        "capability": "CAP-094",
        "stages": ["conformance", "security_checklist", "sandboxed_trial"],
        "conformance_suite": "certify_source_connector",
        "via": "/api/v1/integrations/certify/{connector_key}",
        "trial_sandbox": "marketplace_listings.trial_sandbox",
        "not_domains_marketplace_sandbox": True,
        "first_party_checklist_exception": False,
        "feature_ai_copilot": settings.feature_ai_copilot,
        "honesty": ("CI pipeline only; production pilot sync OPEN. Not Production GO."),
    }


@router.post("/seed-first-party", response_model=list[ListingResponse], dependencies=_AUTH)
async def seed_first_party_listings() -> list[ListingResponse]:
    """Idempotent STORY-13-04 publish pack (≥3 connectors + ≥1 playbook)."""
    rows = _STORE.seed_publish_pack()
    return [_listing_response(r) for r in rows]


@router.post("/seed-publish-pack", response_model=list[ListingResponse], dependencies=_AUTH)
async def seed_publish_pack_listings() -> list[ListingResponse]:
    """Explicit STORY-13-04 seed alias."""
    rows = _STORE.seed_publish_pack()
    return [_listing_response(r) for r in rows]


class CertifyBody(BaseModel):
    real_tenant_ids: list[str] = Field(default_factory=list)
    auto_submit: bool = True


class CertifyReportResponse(BaseModel):
    listing_id: str
    ok: bool
    status_before: str
    status_after: str
    stages: list[dict[str, Any]] = Field(default_factory=list)
    ran_at: str = ""
    honesty: str = ""


class CatalogInstallResponse(BaseModel):
    id: str
    tenant_id: str
    listing_id: str
    listing_slug: str
    listing_type: str
    connector_key: str = ""
    installed_at: str = ""
    honesty: str = ""


@router.get("/installs", response_model=list[CatalogInstallResponse], dependencies=_AUTH)
async def list_catalog_installs(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[CatalogInstallResponse]:
    rows = _INSTALLS.list_for_tenant(tenant_id=str(tenant_id))
    return [CatalogInstallResponse.model_validate(r.as_dict()) for r in rows]


@router.post(
    "/{listing_id}/submit",
    response_model=ListingResponse,
    dependencies=_AUTH,
)
async def submit_listing(listing_id: str) -> ListingResponse:
    try:
        row = submit_for_certification(_STORE, listing_id)
    except MarketplaceListingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _listing_response(row)


@router.post(
    "/{listing_id}/certify",
    response_model=CertifyReportResponse,
    dependencies=_AUTH,
)
async def certify_listing(
    listing_id: str,
    body: CertifyBody | None = None,
) -> CertifyReportResponse:
    payload = body or CertifyBody()
    try:
        report = await run_certification_pipeline(
            _STORE,
            listing_id,
            real_tenant_ids=list(payload.real_tenant_ids),
            auto_submit=payload.auto_submit,
        )
    except MarketplaceListingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CertifyReportResponse.model_validate(report.as_dict())


@router.post(
    "/{listing_id}/publish",
    response_model=ListingResponse,
    dependencies=_AUTH,
)
async def publish_listing_route(listing_id: str) -> ListingResponse:
    try:
        row = publish_listing(_STORE, listing_id)
    except MarketplaceListingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _listing_response(row)


@router.post(
    "/{listing_id}/install",
    response_model=CatalogInstallResponse,
    dependencies=_AUTH,
)
async def install_listing(
    listing_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> CatalogInstallResponse:
    """Catalog install receipt for published/certified listing (not live ERP GO)."""
    row = _STORE.get(listing_id) or _STORE.get_by_slug(listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="marketplace listing not found")
    try:
        rec = _INSTALLS.install(row, tenant_id=str(tenant_id))
    except MarketplaceListingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CatalogInstallResponse.model_validate(rec.as_dict())


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
    return _listing_response(row)


@router.get("", response_model=list[ListingResponse], dependencies=_AUTH)
async def list_listings(
    listing_type: str | None = Query(None),
    status: str | None = Query(None),
) -> list[ListingResponse]:
    rows = _STORE.list_listings(listing_type=listing_type, status=status)
    return [_listing_response(r) for r in rows]


@router.get("/{listing_id}", response_model=ListingResponse, dependencies=_AUTH)
async def get_listing(listing_id: str) -> ListingResponse:
    row = _STORE.get(listing_id)
    if row is None:
        # Allow slug lookup for FE convenience.
        row = _STORE.get_by_slug(listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="marketplace listing not found")
    return _listing_response(row)


@router.delete("/{listing_id}", dependencies=_AUTH)
async def delete_listing(listing_id: str) -> dict[str, Any]:
    ok = _STORE.delete(listing_id)
    if not ok:
        raise HTTPException(status_code=404, detail="marketplace listing not found")
    return {"deleted": True, "id": listing_id}


def bind_store(store: MemMarketplaceListingStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store


def bind_install_store(store: MemCatalogInstallStore) -> None:
    global _INSTALLS  # noqa: PLW0603
    _INSTALLS = store
