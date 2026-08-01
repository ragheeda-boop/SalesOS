import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .schemas import ImportPreview, ImportResult
from .service import ExcelImportService

router = APIRouter()


@router.post(
    "/import/excel/preview",
    response_model=ImportPreview,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.IMPORT))],
)
async def preview_excel(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are supported")

    content = await file.read()
    service = ExcelImportService(db=db)
    result = await service.preview(content, file.filename)
    return ImportPreview(**result)


@router.post(
    "/import/excel/companies",
    response_model=ImportResult,
    dependencies=[Depends(require_permission_dep("company", PermissionAction.IMPORT))],
)
async def import_companies_from_excel(
    request: Request,
    file: UploadFile = File(...),
    column_mapping: str | None = Form(None, description="JSON string of column mapping"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    import json

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are supported")

    content = await file.read()

    mapping = json.loads(column_mapping) if column_mapping else None
    service = ExcelImportService(db=db, logger=getattr(request.app.state, "logger", None))
    result = await service.import_companies(
        content=content,
        filename=file.filename,
        tenant_id=tenant_id,
        column_mapping=mapping,
    )

    import_id = str(uuid.uuid4())
    now = datetime.now(UTC)
    return ImportResult(
        import_id=import_id,
        filename=file.filename,
        total_rows=result["total"],
        imported=result["imported"],
        skipped=result["skipped"],
        errors=result["errors"],
        started_at=now,
        completed_at=now,
        status="completed" if not result["errors"] else "completed_with_errors",
    )
