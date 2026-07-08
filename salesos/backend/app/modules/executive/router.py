from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session
from app.modules.executive.schemas import ExecutiveDashboard
from app.modules.executive.service import ExecutiveService

router = APIRouter()


@router.get("/executive/dashboard", response_model=ExecutiveDashboard)
async def executive_dashboard(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    service = ExecutiveService(db, tenant_id)
    return await service.get_dashboard()
