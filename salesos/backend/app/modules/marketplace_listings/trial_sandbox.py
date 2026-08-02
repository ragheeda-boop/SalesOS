"""STORY-13-02 — CAP-094 sandboxed trial (listing install isolation).

Intentionally separate from domains/marketplace/sandbox.py (plugin iframe/import
sandbox — NOT CAP-094). This module only proves trial-tenant install isolation
in-memory. Not Production GO.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.modules.marketplace_listings.models import MarketplaceListing


@dataclass
class TrialInstallRecord:
    trial_tenant_id: str
    listing_id: str
    listing_slug: str
    installed: bool = True


@dataclass
class CertificationTrialSandbox:
    """Isolated trial installs — must not appear under real tenant keys."""

    _installs: dict[str, list[TrialInstallRecord]] = field(default_factory=dict)

    def run_trial(
        self,
        listing: MarketplaceListing,
        *,
        real_tenant_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        real = [str(t) for t in (real_tenant_ids or []) if str(t).strip()]
        trial_id = f"trial-{listing.id}-{uuid.uuid4().hex[:8]}"
        if trial_id in real:
            return {
                "ok": False,
                "stage": "sandboxed_trial",
                "detail": "trial tenant id collided with real tenant",
                "trial_tenant_id": trial_id,
            }

        record = TrialInstallRecord(
            trial_tenant_id=trial_id,
            listing_id=listing.id,
            listing_slug=listing.slug,
        )
        self._installs.setdefault(trial_id, []).append(record)

        # Negative isolation: real tenants must not see this install.
        leaked = [
            tid
            for tid in real
            if any(r.listing_id == listing.id for r in self._installs.get(tid, []))
        ]
        if leaked:
            return {
                "ok": False,
                "stage": "sandboxed_trial",
                "detail": f"install leaked to real tenants: {leaked}",
                "trial_tenant_id": trial_id,
            }

        return {
            "ok": True,
            "stage": "sandboxed_trial",
            "trial_tenant_id": trial_id,
            "listing_id": listing.id,
            "real_tenants_checked": real,
            "side_effects_on_real_tenants": False,
            "sandbox_module": "marketplace_listings.trial_sandbox",
            "not_domains_marketplace_sandbox": True,
        }

    def installs_for(self, tenant_id: str) -> list[TrialInstallRecord]:
        return list(self._installs.get(str(tenant_id), []))


DEFAULT_TRIAL_SANDBOX = CertificationTrialSandbox()
