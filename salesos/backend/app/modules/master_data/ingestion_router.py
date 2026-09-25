"""Ingestion Pipeline REST endpoints — Phase 2.

Handles file upload, hash dedup, source row insertion, and entity creation.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .ingestion import IngestionPipeline

router = APIRouter(tags=["Master Data Ingestion"])


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class IngestFileRequest(BaseModel):
    """JSON body for file ingestion (rows provided as JSON array)."""
    source_system: str = Field(..., min_length=1, max_length=100)
    rows: list[dict[str, Any]]
    dedup_key_fields: list[str] | None = None


class IngestFileResponse(BaseModel):
    status: str
    file_id: str | None = None
    filename: str | None = None
    file_hash: str | None = None
    rows_inserted: int = 0
    duplicate_groups: int = 0
    entities_created: int = 0
    legacy_mappings_created: int = 0
    errors: list[dict] = []
    duration_seconds: float = 0.0
    message: str | None = None
    existing_file_id: str | None = None


class FileHashCheckResponse(BaseModel):
    exists: bool
    file_id: str | None = None
    filename: str | None = None
    status: str | None = None


class DuplicateGroupResponse(BaseModel):
    group_index: int
    row_indices: list[int]
    count: int


class DetectDuplicatesRequest(BaseModel):
    rows: list[dict[str, Any]]
    key_fields: list[str]


class DetectDuplicatesResponse(BaseModel):
    total_rows: int
    duplicate_groups: list[DuplicateGroupResponse]
    unique_rows: int
    duplicate_rows: int


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


def get_pipeline(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant_id),
) -> IngestionPipeline:
    return IngestionPipeline(session=db, tenant_id=tenant_id)


@router.post(
    "/ingest",
    response_model=IngestFileResponse,
    status_code=201,
    summary="Ingest rows into master data pipeline",
    description="Ingest a file's rows into the master data pipeline. Flow: hash check, register file, insert rows, detect duplicates, create global entities, create legacy mappings. Returns duplicate status if file hash already exists.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.CREATE))],
)
async def ingest_file(
    body: IngestFileRequest,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Ingest a file's rows into the master data pipeline.

    Flow: hash check → register file → insert rows → detect duplicates →
    create global entities → create legacy mappings.

    Returns duplicate status if file hash already exists.
    """
    # Compute a synthetic hash from the rows data for dedup
    import json
    rows_bytes = json.dumps(body.rows, sort_keys=True, default=str).encode("utf-8")
    file_hash = IngestionPipeline.compute_file_hash(rows_bytes)

    # Check for duplicate
    existing = await pipeline.check_file_hash(file_hash)
    if existing:
        return IngestFileResponse(
            status="duplicate",
            file_id=existing["id"],
            filename=existing["filename"],
            message=f"File already ingested as {existing['filename']}",
        )

    result = await pipeline.ingest_file(
        original_filename=f"ingest_{body.source_system}_{len(body.rows)}_rows.json",
        file_data=rows_bytes,
        source_system=body.source_system,
        source_entity_type="company",
        rows=body.rows,
        dedup_key_fields=body.dedup_key_fields,
    )
    return IngestFileResponse(**result)


@router.post(
    "/check-hash/{file_hash}",
    response_model=FileHashCheckResponse,
    summary="Check file hash for duplicates",
    description="Check if a file hash already exists in the system (dedup check before ingestion).",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def check_file_hash(
    file_hash: str,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Check if a file hash already exists (dedup check)."""
    existing = await pipeline.check_file_hash(file_hash)
    if existing:
        return FileHashCheckResponse(
            exists=True,
            file_id=existing["id"],
            filename=existing["original_filename"],
            status=existing["status"],
        )
    return FileHashCheckResponse(exists=False)


@router.post(
    "/detect-duplicates",
    response_model=DetectDuplicatesResponse,
    summary="Detect duplicate rows",
    description="Detect duplicate groups within a set of rows based on key fields. Read-only analysis — does not persist anything.",
    dependencies=[Depends(require_permission_dep("master-data", PermissionAction.READ))],
)
async def detect_duplicates(
    body: DetectDuplicatesRequest,
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Detect duplicate groups within a set of rows based on key fields.

    This is a read-only analysis endpoint — does not persist anything.
    """
    groups = pipeline.detect_duplicates(body.rows, body.key_fields)

    dup_groups = []
    unique_count = 0
    dup_count = 0
    for idx, group in enumerate(groups):
        if len(group) > 1:
            dup_groups.append(
                DuplicateGroupResponse(
                    group_index=idx,
                    row_indices=group,
                    count=len(group),
                )
            )
            dup_count += len(group)
        else:
            unique_count += 1

    return DetectDuplicatesResponse(
        total_rows=len(body.rows),
        duplicate_groups=dup_groups,
        unique_rows=unique_count,
        duplicate_rows=dup_count,
    )
