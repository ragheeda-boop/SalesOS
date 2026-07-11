from app.application.dashboard.dto.dashboard_dto import DashboardDTO
from app.application.dashboard.aggregators.dashboard_aggregator import DashboardAggregator
from app.application.dashboard.queries.get_dashboard_query import DashboardQuery


class DashboardQueryHandler:
    def __init__(self, aggregator: DashboardAggregator):
        self._aggregator = aggregator

    async def handle(self, query: DashboardQuery) -> DashboardDTO:
        return await self._aggregator.aggregate(query)
