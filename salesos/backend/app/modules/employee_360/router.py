from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.dependencies import get_current_tenant_id, get_current_user_id, get_db_session, require_permission_dep
from domains.employee.audit import EmployeeAuditLogger
from domains.employee.postgres_repo import PostgresEmployeeSignalRepository
from sdk.permissions import PermissionAction

from .schemas import (
    ActivityIntelligence, Employee360Response, EmployeeKPIs, EmployeePortfolio,
    EmployeeProfile,
)
from .service import Employee360Service

router = APIRouter()


def _get_signal_repo(db: AsyncSession) -> PostgresEmployeeSignalRepository | None:
    try:
        return PostgresEmployeeSignalRepository(db)
    except Exception:
        return None


@router.get("/employees/me/360", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def my_employee_360(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    signal_repo = _get_signal_repo(db)
    service = Employee360Service(db=db, activity_runtime=activity_runtime, signal_repo=signal_repo)
    try:
        result = await service.get_360(user_id, tenant_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Employee {user_id} not found")
    except Exception as e:
        import traceback as tb_module
        full_tb = tb_module.format_exc()
        print(f"360 CRASH: {full_tb}", flush=True)
        if logger := getattr(request.app.state, "logger", None):
            logger.error("employee_360.get_my_360_failed", user_id=user_id, error=str(e), traceback=full_tb[:1000])
        raise HTTPException(status_code=500, detail=f"Failed to load employee 360 data: {type(e).__name__}: {str(e)[:150]}")
    try:
        audit = EmployeeAuditLogger(db)
        await audit.log_view(user_id, user_id, tenant_id)
    except Exception:
        pass
    return result


@router.get("/employees/{employee_id}/360", dependencies=[Depends(require_permission_dep("employee", PermissionAction.READ))])
async def employee_360(
    employee_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    activity_runtime = getattr(request.app.state, "activity_runtime", None)
    signal_repo = _get_signal_repo(db)
    service = Employee360Service(db=db, activity_runtime=activity_runtime, signal_repo=signal_repo)
    try:
        result = await service.get_360(employee_id, tenant_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    except Exception as e:
        if logger := getattr(request.app.state, "logger", None):
            logger.error("employee_360.get_360_failed", employee_id=employee_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load employee 360 data")
    try:
        audit = EmployeeAuditLogger(db)
        await audit.log_view(employee_id, user_id, tenant_id)
    except Exception:
        pass
    return result
