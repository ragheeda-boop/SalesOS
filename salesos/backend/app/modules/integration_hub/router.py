"""STORY-08-06 — Integration Hub HTTP (DOM-021) for Studio FE (STORY-08-07).

Connect / test / map / schedule / monitor / disconnect + conflict policy.
Mounted at /api/v1/integrations/* (alongside Communication Hub /google/*).
Does not invent secrets. Does not touch DEC-085. Not Production GO.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, verify_token
from app.modules.admin.services import FeatureFlagService
from app.modules.integration_hub.conflict_policy import ConflictResolutionPolicy
from app.modules.integration_hub.conflict_policy_service import (
    ConflictResolutionPolicyService,
)
from app.modules.integration_hub.connection_service import ExternalSystemConnectionService
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.field_mapping_service import FieldMappingConfigService
from app.modules.integration_hub.odoo_adapter import OdooAdapter
from app.modules.integration_hub.odoo_incremental_sync import (
    FLAG_ODOO_INTEGRATION,
    OdooIntegrationDisabledError,
    assert_odoo_integration_enabled,
)
from app.modules.integration_hub.schemas import (
    ConflictPolicyResponse,
    ConflictPolicyUpsert,
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestResponse,
    DisconnectResponse,
    MappingCreate,
    MappingResponse,
    ScheduleCreate,
    ScheduleResponse,
    SyncRunResponse,
    UnlinkedBadgeItemResponse,
    UnlinkedBadgeListResponse,
)
from app.modules.integration_hub.sync_run_service import SyncRunService
from app.modules.integration_hub.sync_schedule import schedule_connection_sync
from app.modules.integration_hub.unlinked_badge import collect_unlinked_badges_from_error_logs
from domains.workflow.postgres_repo import PostgresWorkflowRepository
from domains.workflow.service import WorkflowService, WorkflowValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integration Hub"])
_AUTH = [Depends(verify_token)]


def _tid(tenant_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(tenant_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid tenant_id") from exc


async def _require_odoo_integration_if_needed(
    db: AsyncSession,
    *,
    tenant_id: str,
    connector_key: str,
) -> None:
    """STORY-09-07: gate Odoo connector paths on feature_odoo_integration."""
    if (connector_key or "").strip().lower() != "odoo":
        return
    eval_result = await FeatureFlagService(db).is_enabled(FLAG_ODOO_INTEGRATION, str(tenant_id))
    try:
        assert_odoo_integration_enabled(eval_result)
    except OdooIntegrationDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/connections", response_model=list[ConnectionResponse], dependencies=_AUTH)
async def list_connections(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(100, ge=1, le=500),
) -> list[ConnectionResponse]:
    rows = await ExternalSystemConnectionService(db).list_for_tenant(
        tenant_id=_tid(tenant_id), limit=limit
    )
    return [ConnectionResponse.model_validate(r) for r in rows]


@router.post("/connections", response_model=ConnectionResponse, dependencies=_AUTH)
async def create_connection(
    body: ConnectionCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionResponse:
    await _require_odoo_integration_if_needed(
        db, tenant_id=tenant_id, connector_key=body.connector_key
    )
    try:
        row = await ExternalSystemConnectionService(db).create(
            tenant_id=_tid(tenant_id),
            connector_key=body.connector_key,
            name=body.name,
            credential_ref=body.credential_ref,
            connection_config=body.connection_config,
        )
        # Default conflict policy (feedback-loop exclusion baked in).
        await ConflictResolutionPolicyService(db).upsert(
            tenant_id=row.tenant_id,
            connection_id=row.id,
            rules=[],
            salesos_authored_fields=sorted(
                ConflictResolutionPolicy.default().salesos_authored_fields
            ),
            operational_fields=sorted(ConflictResolutionPolicy.default().operational_fields),
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConnectionResponse.model_validate(row)


@router.get(
    "/connections/{connection_id}",
    response_model=ConnectionResponse,
    dependencies=_AUTH,
)
async def get_connection(
    connection_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionResponse:
    row = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="connection not found")
    return ConnectionResponse.model_validate(row)


@router.post(
    "/connections/{connection_id}/test",
    response_model=ConnectionTestResponse,
    dependencies=_AUTH,
)
async def test_connection(
    connection_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ConnectionTestResponse:
    row = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="connection not found")
    await _require_odoo_integration_if_needed(
        db, tenant_id=tenant_id, connector_key=row.connector_key
    )
    # Dispatch by connector_key — live XML-RPC uses vault credential_ref only.
    if (row.connector_key or "").strip().lower() == "odoo":
        adapter: FakeSourceConnector | OdooAdapter = OdooAdapter()
    else:
        adapter = FakeSourceConnector()
    result = await adapter.test_connection(
        credential_ref=row.credential_ref,
        config=row.connection_config or {},
    )
    return ConnectionTestResponse(
        ok=result.ok,
        message=result.message,
        latency_ms=float(result.latency_ms or 0.0),
    )


@router.post(
    "/connections/{connection_id}/disconnect",
    response_model=DisconnectResponse,
    dependencies=_AUTH,
)
async def disconnect_connection(
    connection_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> DisconnectResponse:
    row = await ExternalSystemConnectionService(db).disconnect(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="connection not found")
    await db.commit()
    return DisconnectResponse(id=row.id, is_active=row.is_active, message="connection deactivated")


@router.post(
    "/connections/{connection_id}/mappings",
    response_model=MappingResponse,
    dependencies=_AUTH,
)
async def create_mapping(
    connection_id: uuid.UUID,
    body: MappingCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> MappingResponse:
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    try:
        row = await FieldMappingConfigService(db).create(
            tenant_id=_tid(tenant_id),
            connection_id=connection_id,
            model=body.model,
            mappings=body.mappings,
            baseline_fields=body.baseline_fields,
            version=body.version,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MappingResponse.model_validate(row)


@router.get(
    "/connections/{connection_id}/mappings/active",
    response_model=MappingResponse | None,
    dependencies=_AUTH,
)
async def get_active_mapping(
    connection_id: uuid.UUID,
    model: str = Query(..., min_length=1, max_length=128),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> MappingResponse | None:
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    row = await FieldMappingConfigService(db).get_active_for_connection_model(
        tenant_id=_tid(tenant_id),
        connection_id=connection_id,
        model=model,
    )
    if row is None:
        return None
    return MappingResponse.model_validate(row)


@router.get(
    "/connections/{connection_id}/conflict-policy",
    response_model=ConflictPolicyResponse,
    dependencies=_AUTH,
)
async def get_conflict_policy(
    connection_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ConflictPolicyResponse:
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    svc = ConflictResolutionPolicyService(db)
    row = await svc.get_for_connection(tenant_id=_tid(tenant_id), connection_id=connection_id)
    if row is None:
        row = await svc.upsert(
            tenant_id=_tid(tenant_id),
            connection_id=connection_id,
            rules=[],
        )
        await db.commit()
    return ConflictPolicyResponse.model_validate(row)


@router.put(
    "/connections/{connection_id}/conflict-policy",
    response_model=ConflictPolicyResponse,
    dependencies=_AUTH,
)
async def put_conflict_policy(
    connection_id: uuid.UUID,
    body: ConflictPolicyUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ConflictPolicyResponse:
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    try:
        row = await ConflictResolutionPolicyService(db).upsert(
            tenant_id=_tid(tenant_id),
            connection_id=connection_id,
            rules=[r.model_dump() for r in body.rules],
            salesos_authored_fields=body.salesos_authored_fields,
            operational_fields=body.operational_fields,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConflictPolicyResponse.model_validate(row)


@router.post(
    "/connections/{connection_id}/schedule",
    response_model=ScheduleResponse,
    dependencies=_AUTH,
)
async def schedule_sync(
    connection_id: uuid.UUID,
    body: ScheduleCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
) -> ScheduleResponse:
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    if not conn.is_active:
        raise HTTPException(status_code=400, detail="connection is disconnected")
    await _require_odoo_integration_if_needed(
        db, tenant_id=tenant_id, connector_key=conn.connector_key
    )
    wf = WorkflowService(repository=PostgresWorkflowRepository(session=db))
    try:
        job = await schedule_connection_sync(
            wf,
            tenant_id=str(tenant_id),
            connection_id=connection_id,
            model=body.model,
            schedule=body.schedule,
            job_type=body.job_type,
            name=body.name,
        )
        await db.commit()
    except (ValueError, WorkflowValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScheduleResponse(
        job_id=job.id,
        connection_id=connection_id,
        model=body.model,
        schedule=body.schedule,
        job_type=body.job_type,
        next_run_at=job.next_run_at,
    )


@router.get(
    "/connections/{connection_id}/sync-runs",
    response_model=list[SyncRunResponse],
    dependencies=_AUTH,
)
async def list_sync_runs(
    connection_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200),
) -> list[SyncRunResponse]:
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    rows = await SyncRunService(db).list_for_connection(
        tenant_id=_tid(tenant_id),
        connection_id=connection_id,
        limit=limit,
    )
    return [SyncRunResponse.model_validate(r) for r in rows]


@router.get(
    "/connections/{connection_id}/unlinked-badges",
    response_model=UnlinkedBadgeListResponse,
    dependencies=_AUTH,
)
async def list_unlinked_badges(
    connection_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(100, ge=1, le=500),
    sync_run_limit: int = Query(50, ge=1, le=200),
) -> UnlinkedBadgeListResponse:
    """STORY-09-01 residual — list unlinked cr_number badges for Studio Monitor.

    Sources SyncRun.error_log entries with kind=unlinked_badge (never silent skip).
    """
    conn = await ExternalSystemConnectionService(db).get_for_tenant(
        connection_id, tenant_id=_tid(tenant_id)
    )
    if conn is None:
        raise HTTPException(status_code=404, detail="connection not found")
    runs = await SyncRunService(db).list_for_connection(
        tenant_id=_tid(tenant_id),
        connection_id=connection_id,
        limit=sync_run_limit,
    )
    items = collect_unlinked_badges_from_error_logs(runs, limit=limit)
    return UnlinkedBadgeListResponse(
        connection_id=connection_id,
        count=len(items),
        items=[UnlinkedBadgeItemResponse.model_validate(i.as_dict()) for i in items],
    )


@router.get("/certify/meta", dependencies=_AUTH)
async def certify_meta() -> dict:
    """STORY-11-10 — second-connector certification surface (R-02)."""
    from app.modules.integration_hub.second_connector import (
        SECOND_CONNECTOR_KEY,
        SECOND_CONNECTOR_TARGET,
    )

    return {
        "suite": "certify_source_connector",
        "certifiable": ["fake", "odoo", "hubspot"],
        "second_connector_key": SECOND_CONNECTOR_KEY,
        "second_connector_target": SECOND_CONNECTOR_TARGET,
        "honesty": (
            "Identical suite to Fake/Odoo. HubSpot adapter is in-memory CI; "
            "live HubSpot API / production pilot sync not claimed. "
            "Chief Architect SAP-vs-HubSpot formal decision may still refine target."
        ),
    }


@router.post("/certify/{connector_key}", dependencies=_AUTH)
async def certify_connector(connector_key: str) -> dict:
    """STORY-11-10 — run SourceConnector certification suite for a named adapter."""
    from app.modules.integration_hub.second_connector import certify_named_connector

    try:
        return await certify_named_connector(connector_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AssertionError as exc:
        raise HTTPException(status_code=400, detail=f"certification failed: {exc}") from exc
