"""STORY-13-01 — MarketplaceListing (OBJ-325 / CAP-071/072).

Single object across connector / app / prompt_pack / playbook types.
Owner-platform catalog (in-memory). Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ListingType = Literal["connector", "app", "prompt_pack", "playbook"]
ListingStatus = Literal[
    "draft",
    "pending_certification",
    "certified",
    "published",
    "rejected",
    "revoked",
]

VALID_LISTING_TYPES = frozenset({"connector", "app", "prompt_pack", "playbook"})
VALID_LISTING_STATUSES = frozenset(
    {
        "draft",
        "pending_certification",
        "certified",
        "published",
        "rejected",
        "revoked",
    }
)


class MarketplaceListingError(ValueError):
    """Invalid MarketplaceListing definition."""


@dataclass
class MarketplaceListing:
    """OBJ-325 — one listing shape for all marketplace content types."""

    id: str
    slug: str
    name: str
    listing_type: ListingType
    version: str
    status: ListingStatus = "draft"
    description: str = ""
    publisher: str = "SalesOS"
    first_party: bool = True
    # Connector listings bind to Integration Hub connector_key (odoo/hubspot/…).
    connector_key: str = ""
    tags: list[str] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "listing_type": self.listing_type,
            "version": self.version,
            "status": self.status,
            "description": self.description,
            "publisher": self.publisher,
            "first_party": self.first_party,
            "connector_key": self.connector_key,
            "tags": list(self.tags),
            "manifest": dict(self.manifest),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _semver_ok(version: str) -> bool:
    parts = (version or "").strip().split(".")
    if len(parts) != 3:
        return False
    return all(p.isdigit() for p in parts)


def build_marketplace_listing(
    *,
    slug: str,
    name: str,
    listing_type: str,
    version: str,
    status: str = "draft",
    description: str = "",
    publisher: str = "SalesOS",
    first_party: bool = True,
    connector_key: str = "",
    tags: list[str] | None = None,
    manifest: dict[str, Any] | None = None,
    listing_id: str = "",
    schema_version: int = 1,
) -> MarketplaceListing:
    sl = (slug or "").strip().lower()
    if not sl or not all(c.isalnum() or c in "-_" for c in sl):
        raise MarketplaceListingError("slug required (alnum, -, _)")
    nm = (name or "").strip()
    if not nm:
        raise MarketplaceListingError("name required")
    lt = (listing_type or "").strip().lower()
    if lt not in VALID_LISTING_TYPES:
        raise MarketplaceListingError(f"listing_type must be one of {sorted(VALID_LISTING_TYPES)}")
    ver = (version or "").strip()
    if not _semver_ok(ver):
        raise MarketplaceListingError("version must be semver MAJOR.MINOR.PATCH")
    st = (status or "draft").strip().lower()
    if st not in VALID_LISTING_STATUSES:
        raise MarketplaceListingError(f"status must be one of {sorted(VALID_LISTING_STATUSES)}")
    ck = (connector_key or "").strip().lower()
    if lt == "connector" and not ck:
        raise MarketplaceListingError("connector listings require connector_key")
    if lt != "connector" and ck:
        raise MarketplaceListingError("connector_key only allowed for connector listings")
    return MarketplaceListing(
        id=listing_id,
        slug=sl,
        name=nm,
        listing_type=lt,  # type: ignore[arg-type]
        version=ver,
        status=st,  # type: ignore[arg-type]
        description=(description or "").strip(),
        publisher=(publisher or "SalesOS").strip() or "SalesOS",
        first_party=bool(first_party),
        connector_key=ck,
        tags=[str(t).strip() for t in (tags or []) if str(t).strip()],
        manifest=dict(manifest or {}),
        schema_version=max(int(schema_version), 1),
    )
