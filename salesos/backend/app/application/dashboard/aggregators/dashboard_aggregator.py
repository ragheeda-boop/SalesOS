import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.dto.dashboard_dto import (
    DashboardDTO, MissionCenterData, DecisionQueueData, IntelligenceFeedData,
    AIBriefData, MarketPulseData, RecentActivityData,
)
from app.application.dashboard.aggregators.source_reader import SourceReader
from app.application.dashboard.mappers.company_mapper import CompanyMapper
from app.application.dashboard.mappers.signal_mapper import SignalMapper
from app.application.dashboard.mappers.timeline_mapper import TimelineMapper
from app.application.dashboard.mappers.scoring_mapper import ScoringMapper
from app.application.dashboard.mappers.ai_mapper import AIMapper
from app.application.dashboard.queries.get_dashboard_query import DashboardQuery


class DashboardAggregator:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._company_mapper = CompanyMapper(db, tenant_id)
        self._signal_mapper = SignalMapper(db, tenant_id)
        self._timeline_mapper = TimelineMapper(db, tenant_id)
        self._scoring_mapper = ScoringMapper(db, tenant_id)
        self._ai_mapper = AIMapper(db, tenant_id)

    async def aggregate(self, query: DashboardQuery) -> DashboardDTO:
        requested = query.fields
        sources = {}

        tasks = {}

        if requested is None or "mission-center" in requested:
            reader = SourceReader("mission-center", "Mission Center", timeout=0.5)
            tasks["missionCenter"] = reader.read(self._company_mapper.get_stats)

        if requested is None or "decision-queue" in requested:
            reader = SourceReader("decision-queue", "Decision Queue", timeout=0.5)
            tasks["decisionQueue"] = reader.read(self._scoring_mapper.get_decisions)

        if requested is None or "intelligence-feed" in requested:
            reader = SourceReader("intelligence-feed", "Intelligence Feed", timeout=0.5)
            tasks["intelligenceFeed"] = reader.read(self._signal_mapper.get_feed)

        if requested is None or "ai-brief" in requested:
            reader = SourceReader("ai-brief", "AI Brief", timeout=1.0)
            tasks["aiBrief"] = reader.read(self._ai_mapper.get_brief)

        if requested is None or "market-pulse" in requested:
            reader = SourceReader("market-pulse", "Market Pulse", timeout=0.5)
            tasks["marketPulse"] = reader.read(self._signal_mapper.get_market_pulse)

        if requested is None or "recent-activity" in requested:
            reader = SourceReader("recent-activity", "Recent Activity", timeout=0.5)
            tasks["recentActivity"] = reader.read(self._timeline_mapper.get_recent)

        results = {}
        if tasks:
            done = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for key, result in zip(tasks.keys(), done):
                if isinstance(result, Exception):
                    from app.application.dashboard.dto.widget_state import WidgetStatus
                    from app.application.dashboard.dto.widget_contract import DashboardWidget, WidgetAction
                    results[key] = DashboardWidget(
                        id=key, title=key.replace("-", " ").title(),
                        status=WidgetStatus.error, data=None,
                        actions=[WidgetAction(id=f"{key}.refresh", label="Retry", type="refresh")],
                    )
                else:
                    results[key] = result

        return DashboardDTO(
            generatedAt=datetime.now(timezone.utc),
            period=query.period,
            totalTracked=0,
            missionCenter=results.get("missionCenter"),
            decisionQueue=results.get("decisionQueue"),
            intelligenceFeed=results.get("intelligenceFeed"),
            aiBrief=results.get("aiBrief"),
            marketPulse=results.get("marketPulse"),
            recentActivity=results.get("recentActivity"),
        )
