from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.common.schemas import PaginatedResponse
from app.dependencies import require_role_dep

from ..schemas import JobDetailResponse, JobResponse
from ._dependencies import AdminRepositories, get_admin_repos

router = APIRouter(
    tags=["Admin - Jobs"],
    dependencies=[Depends(require_role_dep("admin"))],
)


@router.get("/jobs", response_model=PaginatedResponse)
async def list_jobs(
    status: str | None = Query(None),
    job_type: str | None = Query(None),
    page_size: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, description="Keyset cursor for pagination"),
    repos: AdminRepositories = Depends(get_admin_repos),
):
    from sdk.pagination import encode_cursor

    jobs, total = await repos.jobs.list(
        status=status, job_type=job_type, page=1, page_size=page_size + 1
    )
    has_next = len(jobs) > page_size
    if has_next:
        jobs = jobs[:page_size]
    next_cursor = None
    if has_next and jobs:
        last = jobs[-1]
        next_cursor = encode_cursor(str(last.id), last.created_at)
    items = [
        JobResponse(
            id=j.id,
            type=j.type,
            status=j.status,
            progress=j.progress,
            tenant_id=j.tenant_id,
            created_by=j.created_by,
            payload=j.payload,
            result=j.result,
            error_message=j.error_message,
            retry_count=j.retry_count,
            max_retries=j.max_retries,
            scheduled_at=j.scheduled_at,
            started_at=j.started_at,
            completed_at=j.completed_at,
            created_at=j.created_at,
            updated_at=j.updated_at,
        )
        for j in jobs
    ]
    return PaginatedResponse(
        total=total,
        page=1,
        page_size=page_size,
        items=items,
        next_cursor=next_cursor,
        has_next=has_next,
    )


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str, repos: AdminRepositories = Depends(get_admin_repos)):
    job = await repos.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobDetailResponse(
        id=job.id,
        type=job.type,
        status=job.status,
        progress=job.progress,
        tenant_id=job.tenant_id,
        created_by=job.created_by,
        payload=job.payload,
        result=job.result,
        error_message=job.error_message,
        retry_count=job.retry_count,
        max_retries=job.max_retries,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
        logs=job.logs,
    )


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, repos: AdminRepositories = Depends(get_admin_repos)):
    job = await repos.jobs.retry(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not in failed state")
    return {"message": "Job queued for retry", "job_id": job_id}
