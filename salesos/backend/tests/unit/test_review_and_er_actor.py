"""Client-supplied reviewer, tenant, and actor fields are ignored."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.modules.entity_resolution.er_router import merge_entities, resolve_conflict, run_matching
from app.modules.entity_resolution.er_schemas import (
    MergeRequest,
    ResolveConflictRequest,
    RunMatchingRequest,
)
from app.modules.master_data.phase7.review_router import record_disposition
from app.modules.master_data.phase7.schemas import ReviewEvidence, ReviewQueueDisposition


def _row(first=None, mapping=None):
    result = MagicMock()
    result.first.return_value = first
    result.mappings.return_value.first.return_value = mapping
    return result


@pytest.mark.asyncio
async def test_review_disposition_stores_jwt_subject_not_body_reviewer() -> None:
    service = SimpleNamespace(record_disposition=AsyncMock(return_value={"id": "1"}))
    body = ReviewQueueDisposition(
        disposition="REVIEW",
        reviewer="spoofed-name",
        evidence=ReviewEvidence(reason="checked the row"),
    )

    await record_disposition(
        queue_type="P1_CANDIDATE",
        subject_key="company-1",
        body=body,
        service=service,
        user_id="user-from-jwt",
    )

    service.record_disposition.assert_awaited_once()
    assert service.record_disposition.await_args.kwargs["reviewer"] == "user-from-jwt"


@pytest.mark.asyncio
async def test_review_disposition_rejects_missing_user() -> None:
    service = SimpleNamespace(record_disposition=AsyncMock())
    body = ReviewQueueDisposition(
        disposition="REVIEW",
        evidence=ReviewEvidence(reason="checked the row"),
    )

    with pytest.raises(HTTPException) as exc:
        await record_disposition(
            queue_type="P1_CANDIDATE",
            subject_key="company-1",
            body=body,
            service=service,
            user_id="",
        )

    assert exc.value.status_code == 401
    service.record_disposition.assert_not_called()


@pytest.mark.asyncio
async def test_matching_run_uses_session_tenant() -> None:
    pipeline = AsyncMock(
        return_value=SimpleNamespace(
            total_candidates=0,
            matches_found=0,
            auto_merge=0,
            review=0,
            separate=0,
            vetoed=0,
            errors=0,
            duration_seconds=0.0,
        )
    )
    with patch("app.modules.entity_resolution.er_router.run_matching_pipeline", pipeline):
        await run_matching(
            body=RunMatchingRequest(tenant_id="other-tenant"),
            db=object(),
            tenant_id="session-tenant",
        )

    assert pipeline.await_args.kwargs["tenant_id"] == "session-tenant"


@pytest.mark.asyncio
async def test_conflict_resolution_stores_jwt_actor() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_row(mapping={"value_a": "alpha"}))

    await resolve_conflict(
        conflict_id="conflict-1",
        body=ResolveConflictRequest(resolution="use_a", resolved_by="spoofed"),
        db=db,
        user_id="user-from-jwt",
    )

    update = db.execute.await_args_list[-1].args[1]
    assert update["by"] == "user-from-jwt"


@pytest.mark.asyncio
async def test_manual_merge_stores_jwt_actor() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_row(first=("id",)))

    await merge_entities(
        body=MergeRequest(
            target_entity_id="target-1",
            source_entity_id="source-1",
            performed_by="spoofed",
        ),
        db=db,
        user_id="user-from-jwt",
    )

    actors = [call.args[1].get("by") for call in db.execute.await_args_list if len(call.args) > 1]
    assert "user-from-jwt" in actors
    assert "spoofed" not in actors
