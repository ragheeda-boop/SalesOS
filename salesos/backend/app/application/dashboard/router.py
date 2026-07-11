from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from sdk.permissions import PermissionAction
from app.application.dashboard.dto.dashboard_dto import DashboardDTO
from app.application.dashboard.aggregators.dashboard_aggregator import DashboardAggregator
from app.application.dashboard.queries.dashboard_query_handler import DashboardQueryHandler
from app.application.dashboard.queries.get_dashboard_query import DashboardQuery

router = APIRouter()


@router.get("/dashboard", response_model=DashboardDTO)
async def get_dashboard(
    query: DashboardQuery = Depends(),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _: None = Depends(require_permission_dep("executive", PermissionAction.READ)),
):
    aggregator = DashboardAggregator(db, tenant_id)
    handler = DashboardQueryHandler(aggregator)
    return await handler.handle(query)
