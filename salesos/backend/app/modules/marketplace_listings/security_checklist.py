"""STORY-13-02 — CAP-094 security review checklist (all listings, no first-party skip).

Declarative checks only — does not invent live security scans.
Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.marketplace_listings.models import MarketplaceListing

# Forbidden key fragments that look like embedded secrets in manifests.
_SECRET_KEY_FRAGMENTS = frozenset(
    {
        "password",
        "secret",
        "api_key",
        "apikey",
        "token",
        "private_key",
        "client_secret",
    }
)


@dataclass
class ChecklistItemResult:
    id: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "ok": self.ok, "detail": self.detail}


@dataclass
class SecurityChecklistResult:
    ok: bool
    items: list[ChecklistItemResult] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "items": [i.as_dict() for i in self.items],
            "first_party_exception": False,
        }


def _walk_secretish(obj: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k).lower()
            p = f"{path}.{key}" if path else key
            if any(frag in key for frag in _SECRET_KEY_FRAGMENTS) and v not in (
                None,
                "",
                [],
                {},
            ):
                hits.append(p)
            hits.extend(_walk_secretish(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_walk_secretish(v, f"{path}[{i}]"))
    return hits


def run_security_checklist(listing: MarketplaceListing) -> SecurityChecklistResult:
    """Same checklist for first-party and third-party listings."""
    items: list[ChecklistItemResult] = []

    items.append(
        ChecklistItemResult(
            id="listing_type_valid",
            ok=listing.listing_type in {"connector", "app", "prompt_pack", "playbook"},
            detail=listing.listing_type,
        )
    )
    items.append(
        ChecklistItemResult(
            id="version_present",
            ok=bool(listing.version and listing.version.count(".") == 2),
            detail=listing.version,
        )
    )
    items.append(
        ChecklistItemResult(
            id="slug_present",
            ok=bool(listing.slug),
            detail=listing.slug,
        )
    )

    if listing.listing_type == "connector":
        items.append(
            ChecklistItemResult(
                id="connector_key_bound",
                ok=bool(listing.connector_key.strip()),
                detail=listing.connector_key or "missing",
            )
        )
    else:
        items.append(
            ChecklistItemResult(
                id="connector_key_absent",
                ok=not listing.connector_key,
                detail=listing.connector_key or "ok",
            )
        )

    secret_hits = _walk_secretish(listing.manifest)
    items.append(
        ChecklistItemResult(
            id="no_secrets_in_manifest",
            ok=not secret_hits,
            detail=",".join(secret_hits) if secret_hits else "clean",
        )
    )

    # Explicit: first-party still runs checklist (no skip path).
    items.append(
        ChecklistItemResult(
            id="no_first_party_bypass",
            ok=True,
            detail=f"first_party={listing.first_party} still checked",
        )
    )

    ok = all(i.ok for i in items)
    return SecurityChecklistResult(ok=ok, items=items)
