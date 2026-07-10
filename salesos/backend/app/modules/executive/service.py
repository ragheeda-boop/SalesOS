from datetime import datetime, timezone, timedelta

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.executive.schemas import (
    ExecutiveDashboard, RevenueKPI, TeamKPI, RiskKPI,
    PipelineHealth, RenewalKPI, GrowthKPI, HealthKPI,
)


class ExecutiveService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.now = datetime.now(timezone.utc)
        self.days_30 = self.now - timedelta(days=30)
        self.days_90 = self.now - timedelta(days=90)

    async def _fetch_one(self, sql: str, params: dict | None = None) -> dict:
        try:
            row = await self.db.execute(sa_text(sql), params or {})
            return dict(row.mappings().one())
        except Exception:
            return {}

    async def _fetch_all(self, sql: str, params: dict | None = None) -> list[dict]:
        try:
            rows = await self.db.execute(sa_text(sql), params or {})
            return [dict(r) for r in rows.mappings().all()]
        except Exception:
            return []

    async def get_revenue(self) -> RevenueKPI:
        r = await self._fetch_one(
            "SELECT COALESCE(SUM(value), 0) as total_pipeline, "
            "COALESCE(SUM(CASE WHEN status IN ('won','closed_won') THEN value ELSE 0 END), 0) as won_value "
            "FROM commercial_opportunities WHERE tenant_id = :tid",
            {"tid": self.tenant_id},
        )
        total = r.get("total_pipeline", 0.0)
        won = r.get("won_value", 0.0)
        prev = await self._fetch_one(
            "SELECT COALESCE(SUM(value), 0) as prev_value FROM commercial_opportunities "
            "WHERE tenant_id = :tid AND created_at < :d30",
            {"tid": self.tenant_id, "d30": self.days_30},
        )
        prev_val = prev.get("prev_value", 0.0) or 0.0
        growth_pct = round(((total - prev_val) / prev_val * 100), 1) if prev_val > 0 else 0.0
        return RevenueKPI(
            total_booked=won,
            total_pipeline=total,
            growth_percent=growth_pct,
        )

    async def get_team(self) -> TeamKPI:
        r = await self._fetch_one(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active "
            "FROM users WHERE tenant_id = :tid",
            {"tid": self.tenant_id},
        )
        return TeamKPI(
            total_employees=r.get("total", 0),
            active_employees=r.get("active", 0),
        )

    async def get_pipeline(self) -> tuple[PipelineHealth, float]:
        r = await self._fetch_one(
            "SELECT COUNT(*) as total, "
            "COALESCE(SUM(value), 0) as pipeline_value, "
            "COALESCE(SUM(CASE WHEN status IN ('won','closed_won') THEN 1 ELSE 0 END), 0) as won, "
            "COALESCE(SUM(CASE WHEN status IN ('lost','closed_lost') THEN 1 ELSE 0 END), 0) as lost, "
            "COALESCE(AVG(value), 0) as avg_val "
            "FROM commercial_opportunities WHERE tenant_id = :tid",
            {"tid": self.tenant_id},
        )
        total = r.get("total", 0)
        won = r.get("won", 0)
        lost = r.get("lost", 0)
        avg_val = r.get("avg_val", 0.0)
        pipeline_value = r.get("pipeline_value", 0.0)
        win_rate = won / (won + lost) if (won + lost) > 0 else 0.0

        by_stage = await self._fetch_all(
            "SELECT stage, COUNT(*) as cnt, COALESCE(SUM(value), 0) as val "
            "FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open' "
            "GROUP BY stage ORDER BY cnt DESC",
            {"tid": self.tenant_id},
        )

        return PipelineHealth(
            total_deals=total,
            total_value=pipeline_value,
            won_deals=won,
            lost_deals=lost,
            win_rate=round(win_rate, 2),
            avg_deal_size=round(avg_val, 2),
            by_stage=by_stage,
        ), win_rate

    async def get_risks(self) -> RiskKPI:
        stalled = await self._fetch_one(
            "SELECT COUNT(*) as cnt FROM commercial_opportunities "
            "WHERE tenant_id = :tid AND status = 'open' AND stage = 'prospecting'",
            {"tid": self.tenant_id},
        )
        pending_renewals = await self._fetch_one(
            "SELECT COUNT(*) as cnt FROM commercial_contracts "
            "WHERE tenant_id = :tid AND status = 'active' AND expiry_date <= :d90",
            {"tid": self.tenant_id, "d90": self.days_90.date()},
        )
        return RiskKPI(
            stalled_deals=stalled.get("cnt", 0),
            expiring_contracts=pending_renewals.get("cnt", 0),
        )

    async def get_renewals(self) -> RenewalKPI:
        r = await self._fetch_one(
            "SELECT "
            "SUM(CASE WHEN expiry_date <= :d30 THEN 1 ELSE 0 END) as due_30, "
            "SUM(CASE WHEN expiry_date <= :d90 AND expiry_date > :d30 THEN 1 ELSE 0 END) as due_90 "
            "FROM commercial_contracts WHERE tenant_id = :tid AND status = 'active'",
            {"tid": self.tenant_id, "d30": self.days_30.date(), "d90": self.days_90.date()},
        )
        return RenewalKPI(
            due_next_30_days=r.get("due_30") or 0,
            due_next_90_days=r.get("due_90") or 0,
        )

    async def get_growth(self) -> GrowthKPI:
        r = await self._fetch_one(
            "SELECT "
            "(SELECT COUNT(*) FROM companies WHERE tenant_id = :tid AND created_at >= :d30) as new_companies, "
            "(SELECT COUNT(*) FROM contacts_standalone WHERE tenant_id = :tid AND created_at >= :d30) as new_contacts, "
            "(SELECT COUNT(*) FROM commercial_opportunities WHERE tenant_id = :tid AND created_at >= :d30) as new_opps, "
            "(SELECT COUNT(*) FROM commercial_contracts WHERE tenant_id = :tid AND created_at >= :d30) as new_contracts",
            {"tid": self.tenant_id, "d30": self.days_30},
        )
        return GrowthKPI(
            new_companies_30d=r.get("new_companies", 0),
            new_contacts_30d=r.get("new_contacts", 0),
            new_opportunities_30d=r.get("new_opps", 0),
            new_contracts_30d=r.get("new_contracts", 0),
        )

    async def get_health(self) -> HealthKPI:
        completeness = await self._fetch_one(
            "SELECT "
            "COUNT(*) as total, "
            "SUM(CASE WHEN name_ar IS NOT NULL AND name_ar != '' THEN 1 ELSE 0 END) as has_name, "
            "SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) as has_email, "
            "SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone, "
            "SUM(CASE WHEN city IS NOT NULL THEN 1 ELSE 0 END) as has_city, "
            "SUM(CASE WHEN industry IS NOT NULL THEN 1 ELSE 0 END) as has_industry "
            "FROM companies WHERE tenant_id = :tid",
            {"tid": self.tenant_id},
        )
        total = completeness.get("total", 0) or 1
        filled = sum([
            completeness.get("has_name", 0) or 0,
            completeness.get("has_email", 0) or 0,
            completeness.get("has_phone", 0) or 0,
            completeness.get("has_city", 0) or 0,
            completeness.get("has_industry", 0) or 0,
        ])
        max_fill = total * 5
        data_completeness = round(filled / max_fill, 2) if max_fill > 0 else 0.0

        sync = await self._fetch_one(
            "SELECT COUNT(*) as cnt FROM entity_resolution_log "
            "WHERE tenant_id = :tid AND created_at >= :d1",
            {"tid": self.tenant_id, "d1": datetime.now(timezone.utc) - timedelta(days=1)},
        )
        has_recent_sync = sync.get("cnt", 0) > 0

        if data_completeness > 0.8 and has_recent_sync:
            overall = "good"
        elif data_completeness > 0.5:
            overall = "fair"
        else:
            overall = "needs_attention"

        return HealthKPI(
            overall_health=overall,
            data_completeness=data_completeness,
            sync_status="synced" if has_recent_sync else "pending",
            last_activity=self.now.isoformat(),
        )

    async def get_dashboard(self) -> ExecutiveDashboard:
        revenue = await self.get_revenue()
        team = await self.get_team()
        pipeline, win_rate = await self.get_pipeline()
        risks = await self.get_risks()
        renewals = await self.get_renewals()
        growth = await self.get_growth()
        health = await self.get_health()

        return ExecutiveDashboard(
            revenue=RevenueKPI(
                total_booked=revenue.total_booked,
                total_pipeline=revenue.total_pipeline,
                weighted_pipeline=revenue.total_pipeline * max(win_rate, 0.1),
                forecast=revenue.total_pipeline * max(win_rate, 0.1),
                growth_percent=revenue.growth_percent,
            ),
            team=TeamKPI(
                total_employees=team.total_employees,
                active_employees=team.active_employees,
                avg_win_rate=round(win_rate, 2),
            ),
            risk=RiskKPI(
                stalled_deals=risks.stalled_deals,
                expiring_contracts=renewals.due_next_30_days + renewals.due_next_90_days,
            ),
            pipeline=pipeline,
            renewals=renewals,
            growth=growth,
            health=health,
        )
