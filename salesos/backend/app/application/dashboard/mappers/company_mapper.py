from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.dto.dashboard_dto import MissionCenterData


class CompanyMapper:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def get_stats(self) -> MissionCenterData:
        from sqlalchemy import text as sa_text

        row = await self.db.execute(
            sa_text(
                "SELECT "
                "(SELECT COUNT(*) FROM companies WHERE tenant_id = :tid) as companies, "
                "(SELECT COUNT(*) FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open') as deals, "
                "(SELECT COALESCE(SUM(value), 0) FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open') as pipeline, "
                "(SELECT COUNT(*) FROM activity_records WHERE tenant_id = :tid AND timestamp >= :today) as signals, "
                "(SELECT COUNT(*) FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open' AND stage = 'prospecting') as pending"
            ),
            {"tid": self.tenant_id, "today": datetime.now(timezone.utc) - timedelta(days=1)},
        )
        r = dict(row.mappings().one())

        return MissionCenterData(
            companiesTracked=r.get("companies", 0),
            activeDeals=r.get("deals", 0),
            pipelineValue=float(r.get("pipeline", 0.0)),
            signalsToday=r.get("signals", 0),
            decisionsPending=r.get("pending", 0),
        )
