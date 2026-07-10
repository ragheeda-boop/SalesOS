from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.dto.dashboard_dto import AIBriefData


class AIMapper:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def get_brief(self) -> AIBriefData:
        from sqlalchemy import text as sa_text

        row = await self.db.execute(
            sa_text("""
                SELECT
                    (SELECT COUNT(*) FROM companies WHERE tenant_id = :tid) as total_companies,
                    (SELECT COUNT(*) FROM companies WHERE tenant_id = :tid AND created_at >= :d30) as new_companies,
                    (SELECT COUNT(*) FROM commercial_opportunities WHERE tenant_id = :tid) as total_deals,
                    (SELECT COUNT(*) FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open') as active_deals,
                    (SELECT COALESCE(SUM(value), 0) FROM commercial_opportunities WHERE tenant_id = :tid AND status = 'open') as pipeline
            """),
            {"tid": self.tenant_id, "d30": datetime.now(timezone.utc) - timedelta(days=30)},
        )
        r = dict(row.mappings().one())

        tc = r.get("total_companies", 0)
        nc = r.get("new_companies", 0)
        td = r.get("total_deals", 0)
        ad = r.get("active_deals", 0)
        pv = float(r.get("pipeline", 0.0))

        highlights = []
        if nc > 0:
            highlights.append(f"تمت إضافة {nc} شركة جديدة خلال الـ 30 يوماً الماضية")
        if ad > 0:
            highlights.append(f"{ad} صفقة نشطة بقيمة إجمالية {pv:,.0f}")
        if tc > 0:
            highlights.append(f"إجمالي {tc} شركة في قاعدة البيانات")

        summary = f"نظرة عامة: {tc} شركة، {td} صفقة (منها {ad} نشطة). "
        if pv > 0:
            summary += f"قيمة الصفقات النشطة: {pv:,.0f}. "
        if nc > 0:
            summary += f"نمو: {nc} شركة جديدة في آخر 30 يوم."

        return AIBriefData(
            summary=summary,
            highlights=highlights,
            generatedAt=datetime.now(timezone.utc).isoformat(),
        )
