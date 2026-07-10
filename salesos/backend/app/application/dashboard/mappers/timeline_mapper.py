from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.dto.dashboard_dto import RecentActivityData, ActivityItem


class TimelineMapper:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def get_recent(self) -> RecentActivityData:
        from sqlalchemy import text as sa_text

        rows = await self.db.execute(
            sa_text("""
                SELECT ar.id, ar.action, ar.entity_type, ar.entity_id,
                       ar.target_type, ar.target_id, ar.metadata, ar.timestamp
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
            items.append(ActivityItem(
                id=r["id"],
                type=self._activity_type(r["action"]),
                title=meta.get("description") or r["action"],
                companyId=r["entity_id"],
                companyName=meta.get("name_ar"),
                timestamp=r["timestamp"].isoformat() if r["timestamp"] else "",
            ))

        return RecentActivityData(items=items, total=len(items))

    def _activity_type(self, action: str) -> str:
        action_lower = action.lower()
        if "signal" in action_lower:
            return "signal"
        if "decision" in action_lower:
            return "decision"
        if "update" in action_lower or "edit" in action_lower:
            return "update"
        return "note"
