from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction

from .schemas import Employee360Response
from .service import Employee360Service

router = APIRouter()


@router.get("/employees/me/360", response_model=Employee360Response, dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def my_employee_360(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    service = Employee360Service(db=db, activity_runtime=activity_runtime)
    try:
        return await service.get_360(user_id, tenant_id)
    except Exception:
        from .schemas import EmployeeProfile, Employee360Response
        return Employee360Response(
            profile=EmployeeProfile(
                id=user_id, full_name="", email="", role="",
                tenant_id=tenant_id, is_active=True,
            ),
            portfolio=None,
            activity_intelligence=None,
            kpis=None,
            ai_coach=[],
        )


@router.get("/employees/{employee_id}/360", response_model=Employee360Response, dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def employee_360(
    employee_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    service = Employee360Service(db=db, activity_runtime=activity_runtime)
    try:
        return await service.get_360(employee_id, tenant_id)
    except Exception:
        from .schemas import EmployeeProfile, Employee360Response
        return Employee360Response(
            profile=EmployeeProfile(
                id=employee_id, full_name="", email="", role="",
                tenant_id=tenant_id, is_active=True,
            ),
            portfolio=None,
            activity_intelligence=None,
            kpis=None,
            ai_coach=[],
        )
