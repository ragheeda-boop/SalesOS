from datetime import date

from sqlalchemy import case, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.revenue_execution.models import Opportunity, Task

STAGE_WEIGHTS = {
    "identified": 0.10,
    "qualifying": 0.25,
    "developing": 0.45,
    "proposing": 0.65,
    "negotiating": 0.80,
    "closing": 0.90,
}
STAGE_ORDER = ["identified", "qualifying", "developing", "proposing", "negotiating", "closing"]


def _stage_sort_key():
    return case(
        *((Opportunity.stage == stage, index) for index, stage in enumerate(STAGE_ORDER)),
        else_=len(STAGE_ORDER),
    )


class RevenueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_opportunity(
        self,
        tenant_id: str,
        company_id: str,
        title: str,
        estimated_value: float,
        confidence: float,
        buying_intent: float = 0.5,
        relationship_strength: float = 0.5,
        source_action_id: str | None = None,
    ):
        risk = "low" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "high"
        stmt = (
            insert(Opportunity)
            .values(
                tenant_id=tenant_id,
                company_id=company_id,
                title=title,
                estimated_value=estimated_value,
                confidence=confidence,
                win_probability=0.10,
                source="nba",
                source_action_id=source_action_id,
                buying_intent=buying_intent,
                relationship_strength=relationship_strength,
                risk_level=risk,
                stage="identified",
            )
            .returning(
                Opportunity.id,
                Opportunity.title,
                Opportunity.stage,
                Opportunity.estimated_value,
                Opportunity.confidence,
                Opportunity.source,
                Opportunity.risk_level,
                Opportunity.created_at,
                Opportunity.last_activity_at,
            )
        )
        result = await self.db.execute(stmt)
        row = result.fetchone()
        await self.db.commit()
        return dict(row._mapping) if row else None

    async def update_stage(self, opportunity_id: str, stage: str, tenant_id: str):
        stmt = (
            update(Opportunity)
            .where(Opportunity.id == opportunity_id, Opportunity.tenant_id == tenant_id)
            .values(stage=stage, stage_changed_at=func.now(), last_activity_at=func.now())
            .returning(
                Opportunity.id,
                Opportunity.title,
                Opportunity.stage,
                Opportunity.estimated_value,
                Opportunity.confidence,
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def create_task(
        self,
        tenant_id: str,
        title: str,
        priority: str = "medium",
        source: str = "manual",
        company_id: str | None = None,
        due_date: str | None = None,
    ):
        parsed_due: date | None = None
        if due_date is not None:
            parsed_due = date.fromisoformat(due_date) if isinstance(due_date, str) else due_date

        stmt = (
            insert(Task)
            .values(
                tenant_id=tenant_id,
                title=title,
                priority=priority,
                source=source,
                company_id=company_id,
                due_date=parsed_due,
            )
            .returning(
                Task.id,
                Task.title,
                Task.priority,
                Task.source,
                Task.completed,
                Task.created_at,
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def complete_task(self, task_id: str, tenant_id: str):
        stmt = (
            update(Task)
            .where(Task.id == task_id, Task.tenant_id == tenant_id)
            .values(completed=True)
            .returning(Task.id, Task.title, Task.completed)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def get_pipeline(self, tenant_id: str):
        stage_order = _stage_sort_key()
        stmt = (
            select(
                Opportunity.stage,
                func.count().label("deals"),
                func.coalesce(func.sum(Opportunity.estimated_value), 0).label("value"),
            )
            .where(
                Opportunity.tenant_id == tenant_id,
                Opportunity.stage.notin_(["won", "lost"]),
            )
            .group_by(Opportunity.stage)
            .order_by(stage_order)
        )
        result = await self.db.execute(stmt)
        stages_data = result.fetchall()
        stages = [
            {"id": r.stage, "label": r.stage, "deals": r.deals, "value": float(r.value)}
            for r in stages_data
        ]
        total_value = sum(s["value"] for s in stages)
        weighted_value = sum(s["value"] * STAGE_WEIGHTS.get(s["id"], 0) for s in stages)
        return {
            "total_deals": sum(s["deals"] for s in stages),
            "total_value": total_value,
            "weighted_value": weighted_value,
            "stages": stages,
        }

    async def list_opportunities(
        self, tenant_id: str, stage: str | None = None, page: int = 1, limit: int = 20
    ):
        filters = [Opportunity.tenant_id == tenant_id]
        if stage:
            filters.append(Opportunity.stage == stage)
        offset = (page - 1) * limit
        list_stmt = (
            select(
                Opportunity.id,
                Opportunity.company_id,
                Opportunity.title,
                Opportunity.stage,
                Opportunity.estimated_value,
                Opportunity.confidence,
                Opportunity.win_probability,
                Opportunity.source,
                Opportunity.risk_level,
                Opportunity.created_at,
                Opportunity.last_activity_at,
            )
            .where(*filters)
            .order_by(Opportunity.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(list_stmt)
        rows = [dict(r._mapping) for r in result.fetchall()]
        count_stmt = select(func.count()).select_from(Opportunity).where(*filters)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()
        return {"opportunities": rows, "total": total, "page": page}

    async def list_tasks(self, tenant_id: str, priority: str | None = None):
        filters = [Task.tenant_id == tenant_id]
        if priority:
            filters.append(Task.priority == priority)
        stmt = (
            select(
                Task.id,
                Task.title,
                Task.priority,
                Task.source,
                Task.company_id,
                Task.completed,
                Task.created_at,
            )
            .where(*filters)
            .order_by(Task.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return [dict(r._mapping) for r in result.fetchall()]
