from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.dto.dashboard_dto import DecisionQueueData, DecisionItem


class ScoringMapper:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def get_decisions(self) -> DecisionQueueData:
        from sqlalchemy import text as sa_text

        rows = await self.db.execute(
            sa_text("""
                SELECT c.id, c.name_ar, cf.feature_name, cf.score
                FROM company_features cf
                JOIN companies c ON c.id::text = cf.company_id
                WHERE cf.tenant_id = :tid
                  AND cf.score >= 0.7
                ORDER BY cf.score DESC
                LIMIT 10
            """),
            {"tid": self.tenant_id},
        )
        items = []
        for r in rows.mappings().all():
            items.append(DecisionItem(
                id=f"dec_{r['feature_name']}_{r['id']}",
                companyId=r["id"],
                companyName=r["name_ar"] or "",
                type="opportunity",
                title=f"فرصة: {r['name_ar']} — {r['feature_name']}",
                priority="high" if r["score"] >= 0.85 else "medium",
                score=float(r["score"]),
            ))

        return DecisionQueueData(items=items, total=len(items))
