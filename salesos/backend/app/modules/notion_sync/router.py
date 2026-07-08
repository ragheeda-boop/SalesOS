import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .schemas import SyncRequest, SyncResult, SyncStatus
from .service import NotionSyncService

router = APIRouter()


@router.post("/notion/sync", response_model=SyncResult, dependencies=[Depends(require_permission_dep("company", PermissionAction.IMPORT))])
async def trigger_sync(
    body: SyncRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    service = NotionSyncService(db=db, logger=getattr(request.app.state, "logger", None))

    sync_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    if body.entity_type == "company":
        result = await service.import_companies(
            database_id=body.source.database_id,
            token=body.source.token,
            tenant_id=tenant_id,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported entity_type: {body.entity_type}")

    status = SyncStatus(
        sync_id=sync_id,
        status="completed" if not result["errors"] else "completed_with_errors",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        entities_found=result["entities_found"],
        entities_imported=result["entities_imported"],
        entities_skipped=result["entities_skipped"],
        errors=result["errors"],
    )
    return SyncResult(
        status=status.status,
        message=f"Imported {result['entities_imported']} companies from Notion",
        details=status,
    )
