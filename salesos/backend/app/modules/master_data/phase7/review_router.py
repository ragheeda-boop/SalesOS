"""Phase 7-A — Review Queue REST endpoints.

READ-ONLY exports + record-only disposition capture. Hard limits apply:
writes ONLY to md_review_queue_state in salesos_test. No Phase 6 write,
no merge, no CR promotion, no production, no Apollo/external API.

HOTFIX (this revision): removed the duplicated `/review-queue` path segment.
This router is mounted in `app/boot/routers.py` with
`prefix="/api/v1/master-data/review-queue"`; every route below is declared
relative to that mount point only (e.g. "/p3", not "/review-queue/p3").
Previously each route ALSO started with "/review-queue/...", producing a
live path of `/api/v1/master-data/review-queue/review-queue/p3` that never
matched the frontend's calls to `/api/v1/master-data/review-queue/p3`.
No business logic changed: every handler below calls the exact same
`ReviewQueueService` methods as before, unchanged in `review_queue.py`.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.config import settings
from app.dependencies import require_permission_dep
from sdk.permissions import PermissionAction

from .review_queue import ReviewQueueService
from .schemas import ReviewQueueDisposition, ReviewQueueDispositionResponse

router = APIRouter(tags=["Master Data Review Queue"])
_REVIEW_READ_PERMISSION = Depends(
    require_permission_dep("master-data-review", PermissionAction.READ)
)
_REVIEW_UPDATE_PERMISSION = Depends(
    require_permission_dep("master-data-review", PermissionAction.UPDATE)
)


def get_service() -> ReviewQueueService:
    environment = (settings.env or "").strip().lower()
    if environment not in {"local", "dev", "development", "test", "testing"}:
        raise HTTPException(
            status_code=503,
            detail="Master Data review endpoints are disabled outside local/test environments",
        )
    # The review service binds to its OWN salesos_test session
    # (review_async_session) to reach the Phase 6 + Phase 7-A md_* tables.
    # The app request session (get_db_session) is on the app DB, which does
    # NOT contain the review tables. Auth/tenancy already resolved via
    # require_permission_dep (app DB); the review data is read/written from
    # salesos_test.
    return ReviewQueueService()


# ═══════════════════════════════════════════════════════════════════════════════
# Read-only exports
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/p3",
    summary="List P3 review pairs",
    description="List P3 fuzzy candidate pairs for human review, with optional status filter and pagination.",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def list_p3_pairs(
    status: str | None = Query(None),
    batch: str | None = Query(None, description="priority | remainder | omit for all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    service: ReviewQueueService = Depends(get_service),
):
    items, total = await service.list_p3_pairs(
        status=status, batch=batch, offset=(page - 1) * page_size, limit=page_size
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get(
    "/p3/count",
    summary="Get P3 pair count",
    description="Get the total count of P3 fuzzy candidate pairs in the review queue.",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def get_p3_count(service: ReviewQueueService = Depends(get_service)):
    count = await service.get_p3_count()
    return {"queue_type": "P3_PAIR", "count": count}


@router.get(
    "/short-cr",
    summary="List suspicious short-CR accounts",
    description="List accounts with suspicious short CR numbers (potential real short CRs vs. artifacts).",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def list_short_cr(service: ReviewQueueService = Depends(get_service)):
    items = await service.list_short_cr()
    return {"total": len(items), "items": items}


@router.get(
    "/triage",
    summary="List triage candidates",
    description="List P1/P2/P3 triage candidates for human review, with optional type filter and pagination.",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def list_triage(
    candidate_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    service: ReviewQueueService = Depends(get_service),
):
    items, total = await service.list_triage_candidates(
        candidate_type=candidate_type, offset=(page - 1) * page_size, limit=page_size
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get(
    "/triage/counts",
    summary="Get triage candidate counts",
    description="Get counts of triage candidates broken down by priority level (P1, P2, P3).",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def get_triage_counts(service: ReviewQueueService = Depends(get_service)):
    counts = await service.get_triage_counts()
    return {"counts": counts}


@router.get(
    "/sales-usability/summary",
    summary="Sales-usability summary under PO decisions A2/A3",
    description=(
        "How many Phase 6 SALES_READY / SALES_READY_WITH_REVIEW accounts may actually be "
        "treated as sales-usable given the open human-review gates, and why the rest may not."
    ),
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def sales_usability_summary(service: ReviewQueueService = Depends(get_service)):
    return await service.get_sales_usability_summary()


@router.get(
    "/sales-usability/accounts",
    summary="List accounts with their sales-usability blockers",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def sales_usability_accounts(
    usable: bool | None = Query(None),
    blocker: str | None = Query(None, max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: ReviewQueueService = Depends(get_service),
):
    items, total = await service.list_sales_usability(
        usable=usable, blocker=blocker, offset=(page - 1) * page_size, limit=page_size
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ═══════════════════════════════════════════════════════════════════════════════
# Read-only FULL exports (no pagination cap) — same service methods, same
# queries, just called with a bound above the known population size instead
# of the UI page size. No new SQL, no new write path, no business-logic change.
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/export/p3",
    summary="Export all P3 pairs",
    description="Full read-only export of all P3 fuzzy candidate pairs (population fixed at ~2,661).",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def export_p3_pairs(service: ReviewQueueService = Depends(get_service)):
    """Full read-only export of all P3 pairs (population is fixed at 2,661)."""
    items, total = await service.list_p3_pairs(offset=0, limit=3000)
    return {"total": total, "items": items}


@router.get(
    "/export/short-cr",
    summary="Export short-CR accounts",
    description="Full read-only export of the 36 suspicious short-CR accounts.",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def export_short_cr(service: ReviewQueueService = Depends(get_service)):
    """Full read-only export of the 36 suspicious short-CR accounts."""
    items = await service.list_short_cr()
    return {"total": len(items), "items": items}


@router.get(
    "/export/triage",
    summary="Export all triage candidates",
    description="Full read-only export of all P1/P2/P3-account triage candidates (~54,185 records).",
    dependencies=[_REVIEW_READ_PERMISSION],
)
async def export_triage(service: ReviewQueueService = Depends(get_service)):
    """Full read-only export of all P1/P2/P3-account triage candidates (54,185)."""
    items, total = await service.list_triage_candidates(offset=0, limit=60000)
    return {"total": total, "items": items}


# ═══════════════════════════════════════════════════════════════════════════════
# Record-only disposition capture (P3, Short-CR, TRIAGE, P1 candidates, P2
# sample strata, and v0.7 MA-unresolved contacts)
# sample-stratum acceptance). Every write remains confined to
# md_review_queue_state; no Master Data side effect is attached.
# ═══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/{queue_type}/{subject_key}/disposition",
    response_model=ReviewQueueDispositionResponse,
    summary="Record a review disposition",
    description="Capture a review disposition (record-only; no merge, CR, or classification side effects). Canonical global_company_id is resolved from the subject and only asserted when it maps to a real Global Company; structured evidence lands in evidence_ref.",
    dependencies=[_REVIEW_UPDATE_PERMISSION],
)
async def record_disposition(
    queue_type: str = Path(...),
    subject_key: str = Path(...),
    body: ReviewQueueDisposition = ...,
    service: ReviewQueueService = Depends(get_service),
):
    """Capture a review disposition (record-only; no merge/CR/classification side effect)."""
    result = await service.record_disposition(
        queue_type=queue_type,
        subject_key=subject_key,
        disposition=body.disposition,
        reviewer=body.reviewer,
        notes=body.notes,
        evidence=body.evidence,
    )
    return result
