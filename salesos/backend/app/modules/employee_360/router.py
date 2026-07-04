from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session

from .schemas import Employee360Response
from .service import Employee360Service

router = APIRouter()


@router.get("/employees/me/360", response_model=Employee360Response)
async def my_employee_360(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    service = Employee360Service(db=db, activity_runtime=activity_runtime)
    return await service.get_360(user_id, tenant_id)


@router.get("/employees/{employee_id}/360", response_model=Employee360Response)
async def employee_360(
    employee_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    service = Employee360Service(db=db, activity_runtime=activity_runtime)
    return await service.get_360(employee_id, tenant_id)
