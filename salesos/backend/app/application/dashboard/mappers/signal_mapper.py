from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.dto.dashboard_dto import (
    IntelligenceFeedData, SignalItem, MarketPulseData, MarketTrend, CompanyMover,
)


class SignalMapper:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def get_feed(self) -> IntelligenceFeedData:
        from sqlalchemy import text as sa_text

        rows = await self.db.execute(
            sa_text("""
                SELECT ar.id, ar.action, ar.entity_type, ar.entity_id,
                       ar.target_type, ar.metadata, ar.timestamp, ar.actor
                FROM activity_records ar
                WHERE ar.tenant_id = :tid
                ORDER BY ar.timestamp DESC
                LIMIT 20
            """),
            {"tid": self.tenant_id},
        )
        items = []
        for r in rows.mappings().all():
            meta = r["metadata"] or {}
            items.append(SignalItem(
                id=r["id"],
                companyId=r["entity_id"],
                companyName=meta.get("name_ar") or r["actor"] or "",
                category=self._categorize(r["action"]),
                title=r["action"],
                summary=meta.get("description", ""),
                severity="medium",
                source=r["entity_type"] or "system",
                timestamp=r["timestamp"].isoformat() if r["timestamp"] else "",
                isUnseen=True,
            ))

        return IntelligenceFeedData(
            items=items,
            total=len(items),
            unseenCount=len(items),
        )

    async def get_market_pulse(self) -> MarketPulseData:
        from sqlalchemy import text as sa_text

        trends = []
        rows = await self.db.execute(
            sa_text("""
                SELECT cf.feature_name, AVG(cf.score) as avg_score,
                       COUNT(*) as company_count
                FROM company_features cf
                WHERE cf.tenant_id = :tid
                GROUP BY cf.feature_name
                ORDER BY avg_score DESC
                LIMIT 5
            """),
            {"tid": self.tenant_id},
        )
        for r in rows.mappings().all():
            avg = float(r["avg_score"])
            trends.append(MarketTrend(
                name=r["feature_name"],
                direction="up" if avg > 0.6 else "stable" if avg > 0.3 else "down",
                change=round(avg * 100, 1),
                description=f"{r['company_count']} شركة بمتوسط {avg:.0%}",
            ))

        movers = []
        top = await self.db.execute(
            sa_text("""
                SELECT c.id, c.name_ar, cf.feature_name, cf.score
                FROM company_features cf
                JOIN companies c ON c.id::text = cf.company_id
                WHERE cf.tenant_id = :tid
                ORDER BY cf.score DESC
                LIMIT 5
            """),
            {"tid": self.tenant_id},
        )
        for r in top.mappings().all():
            movers.append(CompanyMover(
                companyId=r["id"],
                companyName=r["name_ar"] or "",
                scoreChange=round(float(r["score"]) * 100, 1),
                reason=f"ارتفاع في {r['feature_name']}",
            ))

        return MarketPulseData(trends=trends, topMovers=movers)

    def _categorize(self, action: str) -> str:
        action_lower = action.lower()
        if any(w in action_lower for w in ("tender", "منافسة", "طرح")):
            return "tender"
        if any(w in action_lower for w in ("regulatory", "license", "ترخيص", "رخصة")):
            return "regulatory"
        if any(w in action_lower for w in ("competitor", "منافس")):
            return "competitor"
        if any(w in action_lower for w in ("revenue", "funding", "revenue", "تمويل")):
            return "financial"
        return "news"
