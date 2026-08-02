"""STORY-13-02 — CAP-094 certification pipeline for MarketplaceListing.

Status machine: draft → pending_certification → certified | rejected
Connector path reuses Hub certify_source_connector / certify_named_connector.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.marketplace_listings.models import (
    MarketplaceListing,
    MarketplaceListingError,
)
from app.modules.marketplace_listings.security_checklist import (
    SecurityChecklistResult,
    run_security_checklist,
)
from app.modules.marketplace_listings.store import MemMarketplaceListingStore
from app.modules.marketplace_listings.trial_sandbox import (
    DEFAULT_TRIAL_SANDBOX,
    CertificationTrialSandbox,
)

# Allowed transitions for CAP-094 submit/run (publish/revoke are later stories).
_SUBMIT_FROM = frozenset({"draft", "rejected"})
_RUN_FROM = frozenset({"pending_certification", "rejected", "draft"})


@dataclass
class PipelineStageResult:
    stage: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "ok": self.ok, "detail": dict(self.detail)}


@dataclass
class CertificationPipelineReport:
    listing_id: str
    ok: bool
    status_before: str
    status_after: str
    stages: list[PipelineStageResult] = field(default_factory=list)
    ran_at: str = ""
    honesty: str = (
        "CI certification pipeline only; live HubSpot/Odoo sync and R-02 soak "
        "not claimed. Not Production GO."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "ok": self.ok,
            "status_before": self.status_before,
            "status_after": self.status_after,
            "stages": [s.as_dict() for s in self.stages],
            "ran_at": self.ran_at,
            "honesty": self.honesty,
        }


def submit_for_certification(
    store: MemMarketplaceListingStore,
    listing_id: str,
) -> MarketplaceListing:
    row = store.get(listing_id) or store.get_by_slug(listing_id)
    if row is None:
        raise MarketplaceListingError("marketplace listing not found")
    if row.status not in _SUBMIT_FROM:
        raise MarketplaceListingError(
            f"cannot submit from status={row.status}; expected one of {sorted(_SUBMIT_FROM)}"
        )
    return store.upsert(
        listing_id=row.id,
        slug=row.slug,
        name=row.name,
        listing_type=row.listing_type,
        version=row.version,
        status="pending_certification",
        description=row.description,
        publisher=row.publisher,
        first_party=row.first_party,
        connector_key=row.connector_key,
        tags=list(row.tags),
        manifest={**row.manifest, "pipeline": "STORY-13-02"},
    )


async def _run_conformance(listing: MarketplaceListing) -> PipelineStageResult:
    if listing.listing_type != "connector":
        return PipelineStageResult(
            stage="conformance",
            ok=True,
            detail={
                "skipped": True,
                "reason": "non-connector listing; SourceConnector suite N/A",
            },
        )
    key = listing.connector_key.strip().lower()
    if not key:
        return PipelineStageResult(
            stage="conformance",
            ok=False,
            detail={"error": "connector_key required"},
        )
    if key in {"broken", "fail", "reject-me"}:
        return PipelineStageResult(
            stage="conformance",
            ok=False,
            detail={
                "error": "intentional negative connector key",
                "connector_key": key,
            },
        )
    try:
        from app.modules.integration_hub.second_connector import certify_named_connector

        result = await certify_named_connector(key)
    except KeyError as exc:
        return PipelineStageResult(
            stage="conformance",
            ok=False,
            detail={"error": str(exc), "connector_key": key},
        )
    except AssertionError as exc:
        return PipelineStageResult(
            stage="conformance",
            ok=False,
            detail={"error": str(exc), "connector_key": key},
        )
    except Exception as exc:  # noqa: BLE001 — surface as reject, not 500 invent
        return PipelineStageResult(
            stage="conformance",
            ok=False,
            detail={"error": f"{type(exc).__name__}: {exc}", "connector_key": key},
        )
    return PipelineStageResult(
        stage="conformance",
        ok=bool(result.get("ok")),
        detail={
            "suite": "certify_source_connector",
            "via": "integrations/certify",
            "result": result,
        },
    )


def _run_security(
    listing: MarketplaceListing,
) -> tuple[PipelineStageResult, SecurityChecklistResult]:
    checklist = run_security_checklist(listing)
    return (
        PipelineStageResult(
            stage="security_checklist",
            ok=checklist.ok,
            detail=checklist.as_dict(),
        ),
        checklist,
    )


def _run_trial(
    listing: MarketplaceListing,
    sandbox: CertificationTrialSandbox,
    *,
    real_tenant_ids: list[str] | None,
) -> PipelineStageResult:
    detail = sandbox.run_trial(listing, real_tenant_ids=real_tenant_ids)
    return PipelineStageResult(
        stage="sandboxed_trial",
        ok=bool(detail.get("ok")),
        detail=detail,
    )


async def run_certification_pipeline(
    store: MemMarketplaceListingStore,
    listing_id: str,
    *,
    sandbox: CertificationTrialSandbox | None = None,
    real_tenant_ids: list[str] | None = None,
    auto_submit: bool = True,
) -> CertificationPipelineReport:
    """Run conformance + security + trial; set status certified or rejected."""
    box = sandbox or DEFAULT_TRIAL_SANDBOX
    row = store.get(listing_id) or store.get_by_slug(listing_id)
    if row is None:
        raise MarketplaceListingError("marketplace listing not found")

    status_before = row.status
    if auto_submit and row.status in _SUBMIT_FROM:
        row = submit_for_certification(store, row.id)
    elif row.status not in _RUN_FROM and row.status != "pending_certification":
        raise MarketplaceListingError(f"cannot certify from status={row.status}")

    stages: list[PipelineStageResult] = []
    conf = await _run_conformance(row)
    stages.append(conf)
    sec, _ = _run_security(row)
    stages.append(sec)
    trial = _run_trial(row, box, real_tenant_ids=real_tenant_ids)
    stages.append(trial)

    ok = all(s.ok for s in stages)
    status_after = "certified" if ok else "rejected"
    updated = store.upsert(
        listing_id=row.id,
        slug=row.slug,
        name=row.name,
        listing_type=row.listing_type,
        version=row.version,
        status=status_after,
        description=row.description,
        publisher=row.publisher,
        first_party=row.first_party,
        connector_key=row.connector_key,
        tags=list(row.tags),
        manifest={
            **row.manifest,
            "pipeline": "STORY-13-02",
            "last_certify_ok": ok,
            "last_certify_at": datetime.now(UTC).isoformat(),
        },
    )
    return CertificationPipelineReport(
        listing_id=updated.id,
        ok=ok,
        status_before=status_before,
        status_after=updated.status,
        stages=stages,
        ran_at=datetime.now(UTC).isoformat(),
    )
