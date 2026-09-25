"""Entity Resolution API — Matching, Conflicts, Quality, Merge.

New REST endpoints for the evidence-first ER pipeline built on Phase 0-2
master data infrastructure. Mounts alongside the existing entity_resolution
router (which remains untouched for backward compatibility).

Endpoints:
  POST /er/run         — Run matching pipeline
  GET  /er/matches     — List match results
  GET  /er/conflicts   — List field conflicts
  POST /er/conflicts/{id}/resolve — Resolve a conflict
  GET  /er/provenance/{entity_id} — Field provenance
  GET  /er/quality/{entity_id}    — Quality score
  POST /er/quality/{entity_id}/score — Compute quality score
  POST /er/merge       — Merge two entities
  POST /er/unmerge     — Unmerge (rollback)
  GET  /er/merge-history — Merge history
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .er_schemas import (
    RunMatchingRequest,
    RunMatchingResponse,
    MatchResultItem,
    ConflictItem,
    ResolveConflictRequest,
    FieldProvenanceItem,
    QualityScoreResponse,
    MergeRequest,
    UnmergeRequest,
    MergeHistoryItem,
)
from .matching_pipeline import run_matching_pipeline
from .field_provenance import FieldProvenanceService
from .quality_scorer import QualityScorer

router = APIRouter(tags=["Entity Resolution"])


# ── Matching Pipeline ────────────────────────────────────────────────────────


@router.post(
    "/er/run",
    response_model=RunMatchingResponse,
    status_code=201,
    summary="Run matching pipeline",
    description="Run the entity resolution matching pipeline. Finds candidate pairs via deterministic blocking, evaluates them using evidence-first policy, and persists match/conflict results.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.CREATE))],
)
async def run_matching(
    body: RunMatchingRequest,
    db: AsyncSession = Depends(get_db_session),
):
    result = await run_matching_pipeline(
        session=db,
        tenant_id=body.tenant_id,
        source_file_id=body.source_file_id,
        max_candidates=body.max_candidates,
    )
    return RunMatchingResponse(
        total_candidates=result.total_candidates,
        matches_found=result.matches_found,
        auto_merge=result.auto_merge,
        review=result.review,
        separate=result.separate,
        vetoed=result.vetoed,
        errors=result.errors,
        duration_seconds=result.duration_seconds,
    )


# ── Match Results ────────────────────────────────────────────────────────────


@router.get(
    "/matches",
    summary="List match results",
    description="List entity match results with optional status filter and pagination.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.READ))],
)
@router.get(
    "/er/matches",
    summary="List match results",
    description="List entity match results with optional status filter and pagination.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.READ))],
)
async def list_matches(
    status: str | None = Query(None, description="Filter by match_status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """List entity match results."""
    offset = (page - 1) * page_size

    where = "WHERE 1=1"
    params: dict = {"limit": page_size, "offset": offset}

    if status:
        where += " AND match_status = :status"
        params["status"] = status

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM md_entity_matches {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        text(f"SELECT * FROM md_entity_matches {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    items = [dict(r) for r in result.mappings().all()]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
        "has_next": offset + page_size < total,
    }


# ── Conflicts ────────────────────────────────────────────────────────────────


@router.get(
    "/er/conflicts",
    summary="List entity conflicts",
    description="List field-level entity conflicts with optional resolution status and entity filters.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.READ))],
)
async def list_conflicts(
    resolution: str | None = Query(None, description="Filter by resolution status"),
    entity_id: str | None = Query(None, description="Filter by global_entity_id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """List entity conflicts."""
    offset = (page - 1) * page_size
    where = "WHERE 1=1"
    params: dict = {"limit": page_size, "offset": offset}

    if resolution:
        where += " AND resolution = :resolution"
        params["resolution"] = resolution
    if entity_id:
        where += " AND global_entity_id = :entity_id"
        params["entity_id"] = entity_id

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM md_entity_conflicts {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        text(f"SELECT * FROM md_entity_conflicts {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    items = [dict(r) for r in result.mappings().all()]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
        "has_next": offset + page_size < total,
    }


@router.post(
    "/er/conflicts/{conflict_id}/resolve",
    summary="Resolve a conflict",
    description="Resolve a field-level conflict by selecting use_a, use_b, custom value, or dismiss.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.UPDATE))],
)
async def resolve_conflict(
    conflict_id: str = Path(...),
    body: ResolveConflictRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    """Resolve a field-level conflict."""
    import uuid
    from datetime import UTC, datetime

    now = datetime.now(UTC)

    if body.resolution == "use_a":
        # Get value_a from the conflict and set as resolved
        result = await db.execute(
            text("SELECT value_a FROM md_entity_conflicts WHERE id = :id"),
            {"id": conflict_id},
        )
        row = result.mappings().first()
        if not row:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Conflict not found")
        resolved_value = row["value_a"]
    elif body.resolution == "use_b":
        result = await db.execute(
            text("SELECT value_b FROM md_entity_conflicts WHERE id = :id"),
            {"id": conflict_id},
        )
        row = result.mappings().first()
        if not row:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Conflict not found")
        resolved_value = row["value_b"]
    elif body.resolution == "custom":
        resolved_value = body.resolved_value
    elif body.resolution == "dismiss":
        resolved_value = None
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Invalid resolution: {body.resolution}")

    await db.execute(
        text(
            "UPDATE md_entity_conflicts SET resolution = 'resolved', "
            "resolved_value = :value, resolved_by = :by, resolved_at = :now "
            "WHERE id = :id"
        ),
        {"id": conflict_id, "value": resolved_value, "by": body.resolved_by, "now": now},
    )

    return {"message": f"Conflict {conflict_id} resolved", "resolution": body.resolution}


# ── Field Provenance ─────────────────────────────────────────────────────────


@router.get(
    "/er/provenance/{entity_id}",
    summary="Get field provenance",
    description="Get field provenance history for a global entity, optionally filtered by field name.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.READ))],
)
async def get_provenance(
    entity_id: str = Path(...),
    field: str | None = Query(None, description="Filter by field_name"),
    db: AsyncSession = Depends(get_db_session),
):
    """Get field provenance history for a global entity."""
    svc = FieldProvenanceService(db)
    provenance = await svc.get_field_provenance(entity_id, field)
    return {"entity_id": entity_id, "provenance": provenance}


# ── Quality Scores ───────────────────────────────────────────────────────────


@router.get(
    "/er/quality/{entity_id}",
    response_model=QualityScoreResponse | None,
    summary="Get quality score",
    description="Get the latest quality score for a global entity.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.READ))],
)
async def get_quality_score(
    entity_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the latest quality score for a global entity."""
    scorer = QualityScorer(db)
    score = await scorer.get_latest_score(entity_id)
    return score


@router.post(
    "/er/quality/{entity_id}/score",
    response_model=QualityScoreResponse,
    status_code=201,
    summary="Compute quality score",
    description="Compute and persist a fresh quality score for a global entity.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.CREATE))],
)
async def compute_quality_score(
    entity_id: str = Path(...),
    entity_type: str = Query("company", pattern="^(company|person)$"),
    db: AsyncSession = Depends(get_db_session),
):
    """Compute and persist a fresh quality score."""
    scorer = QualityScorer(db)
    score = await scorer.score_entity(entity_id, entity_type)
    return score


# ── Merge / Unmerge ──────────────────────────────────────────────────────────


@router.post(
    "/er/merge",
    status_code=201,
    summary="Merge two entities",
    description="Merge a source entity into a target entity. Transfers source_row provenance, updates source rows to point to target, and records merge history.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.CREATE))],
)
async def merge_entities(
    body: MergeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    """Merge a source entity into a target entity.

    Transfers source_row provenance, updates source rows to point to target,
    and records merge history.
    """
    import uuid
    from datetime import UTC, datetime

    now = datetime.now(UTC)

    # Verify both entities exist
    target = await db.execute(
        text("SELECT id FROM md_global_companies WHERE id = :id"),
        {"id": body.target_entity_id},
    )
    if not target.first():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Target entity {body.target_entity_id} not found")

    source = await db.execute(
        text("SELECT id FROM md_global_companies WHERE id = :id"),
        {"id": body.source_entity_id},
    )
    if not source.first():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Source entity {body.source_entity_id} not found")

    # Transfer source rows to target
    await db.execute(
        text(
            "UPDATE md_source_rows SET global_entity_id = :target_id "
            "WHERE global_entity_id = :source_id"
        ),
        {"target_id": body.target_entity_id, "source_id": body.source_entity_id},
    )

    # Transfer field provenance
    await db.execute(
        text(
            "UPDATE md_field_provenance SET global_entity_id = :target_id "
            "WHERE global_entity_id = :source_id"
        ),
        {"target_id": body.target_entity_id, "source_id": body.source_entity_id},
    )

    # Update target source_count
    await db.execute(
        text(
            "UPDATE md_global_companies SET source_count = source_count + 1, updated_at = :now "
            "WHERE id = :id"
        ),
        {"id": body.target_entity_id, "now": now},
    )

    # Soft-delete source entity
    await db.execute(
        text(
            "UPDATE md_global_companies SET status = 'merged', deleted_at = :now, updated_at = :now "
            "WHERE id = :id"
        ),
        {"id": body.source_entity_id, "now": now},
    )

    # Record merge history
    history_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO md_entity_merge_history "
            "(id, operation, target_entity_id, source_entity_ids, match_score, "
            "match_method, performed_by, performed_at, rollback_available, details) "
            "VALUES (:id, 'merge', :target, CAST(:sources AS jsonb), NULL, 'manual', :by, :now, "
            "true, CAST(:details AS jsonb))"
        ),
        {
            "id": history_id,
            "target": body.target_entity_id,
            "sources": json.dumps([body.source_entity_id]),
            "by": body.performed_by,
            "now": now,
            "details": json.dumps({"reason": "manual_merge"}),
        },
    )

    return {
        "message": "Entities merged",
        "merge_history_id": history_id,
        "target_entity_id": body.target_entity_id,
        "source_entity_id": body.source_entity_id,
    }


@router.post(
    "/er/unmerge",
    status_code=201,
    summary="Unmerge entities",
    description="Unmerge (rollback) a previous merge operation, restoring the source entity.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.CREATE))],
)
async def unmerge_entities(
    body: UnmergeRequest = ...,
    db: AsyncSession = Depends(get_db_session),
):
    """Unmerge (rollback) a previous merge operation."""
    import uuid
    from datetime import UTC, datetime

    now = datetime.now(UTC)

    # Fetch merge history
    result = await db.execute(
        text("SELECT * FROM md_entity_merge_history WHERE id = :id AND operation = 'merge'"),
        {"id": body.merge_history_id},
    )
    history = result.mappings().first()
    if not history:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Merge history not found")

    history = dict(history)
    target_id = history["target_entity_id"]
    source_ids = history["source_entity_ids"]

    if not source_ids:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No source entities recorded in merge")

    source_id = source_ids[0]  # First source entity

    # Restore source entity
    await db.execute(
        text(
            "UPDATE md_global_companies SET status = 'active', deleted_at = NULL, updated_at = :now "
            "WHERE id = :id"
        ),
        {"id": source_id, "now": now},
    )

    # Transfer source rows back
    await db.execute(
        text(
            "UPDATE md_source_rows SET global_entity_id = :source_id "
            "WHERE global_entity_id = :target_id AND source_id IN "
            "(SELECT source_id FROM md_source_rows WHERE global_entity_id = :target_id "
            "  AND id::text IN (SELECT source_a_id FROM md_entity_matches WHERE global_entity_id = :target_id))"
        ),
        {"source_id": source_id, "target_id": target_id},
    )

    # Record unmerge
    unmerge_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO md_entity_merge_history "
            "(id, operation, target_entity_id, source_entity_ids, performed_by, "
            "performed_at, rollback_available, details) "
            "VALUES (:id, 'unmerge', :target, CAST(:sources AS jsonb), :by, :now, false, "
            "CAST(:details AS jsonb))"
        ),
        {
            "id": unmerge_id,
            "target": target_id,
            "sources": json.dumps([source_id]),
            "by": body.performed_by,
            "now": now,
            "details": json.dumps({"rollback_of": body.merge_history_id}),
        },
    )

    # Mark original merge as no longer rollbackable
    await db.execute(
        text(
            "UPDATE md_entity_merge_history SET rollback_available = false "
            "WHERE id = :id"
        ),
        {"id": body.merge_history_id},
    )

    return {
        "message": "Merge rolled back",
        "unmerge_history_id": unmerge_id,
        "restored_entity_id": source_id,
    }


# ── Merge History ────────────────────────────────────────────────────────────


@router.get(
    "/er/merge-history",
    summary="List merge history",
    description="List merge/unmerge history, optionally filtered by target entity.",
    dependencies=[Depends(require_permission_dep("entity-resolution", PermissionAction.READ))],
)
async def list_merge_history(
    entity_id: str | None = Query(None, description="Filter by target_entity_id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """List merge/unmerge history."""
    offset = (page - 1) * page_size
    where = "WHERE 1=1"
    params: dict = {"limit": page_size, "offset": offset}

    if entity_id:
        where += " AND target_entity_id = :entity_id"
        params["entity_id"] = entity_id

    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM md_entity_merge_history {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        text(f"SELECT * FROM md_entity_merge_history {where} ORDER BY performed_at DESC LIMIT :limit OFFSET :offset"),
        params,
    )
    items = [dict(r) for r in result.mappings().all()]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
        "has_next": offset + page_size < total,
    }
