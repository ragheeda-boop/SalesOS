from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.modules.revenue_execution.models import Opportunity, Task

STAGE_WEIGHTS = {"identified": 0.10, "qualifying": 0.25, "developing": 0.45, "proposing": 0.65, "negotiating": 0.80, "closing": 0.90}
STAGE_ORDER = ["identified", "qualifying", "developing", "proposing", "negotiating", "closing"]

class RevenueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_opportunity(self, tenant_id: str, company_id: str, title: str, estimated_value: float, confidence: float, buying_intent: float = 0.5, relationship_strength: float = 0.5, source_action_id: str = None):
        risk = "low" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "high"
        result = await self.db.execute(
            text("""
                INSERT INTO opportunities (tenant_id, company_id, title, estimated_value, confidence, win_probability, source, source_action_id, buying_intent, relationship_strength, risk_level, stage)
                VALUES (:tenant_id, :company_id, :title, :value, :confidence, 0.10, 'nba', :action_id, :buying_intent, :relationship, :risk, 'identified')
                RETURNING id, title, stage, estimated_value, confidence, source, risk_level, created_at, last_activity_at
            """),
            {"tenant_id": tenant_id, "company_id": company_id, "title": title, "value": estimated_value,
             "confidence": confidence, "action_id": source_action_id, "buying_intent": buying_intent,
             "relationship": relationship_strength, "risk": risk}
        )
        row = result.fetchone()
        await self.db.commit()
        return dict(row._mapping) if row else None

    async def update_stage(self, opportunity_id: str, stage: str, tenant_id: str):
        result = await self.db.execute(
            text("UPDATE opportunities SET stage = :stage, stage_changed_at = NOW(), last_activity_at = NOW() WHERE id = :id AND tenant_id = :tenant_id RETURNING id, title, stage, estimated_value, confidence"),
            {"stage": stage, "id": opportunity_id, "tenant_id": tenant_id}
        )
        await self.db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def create_task(self, tenant_id: str, title: str, priority: str = "medium", source: str = "manual", company_id: str = None, due_date: str = None):
        result = await self.db.execute(
            text("""
                INSERT INTO tasks (tenant_id, title, priority, source, company_id, due_date)
                VALUES (:tenant_id, :title, :priority, :source, :company_id, :due_date::date)
                RETURNING id, title, priority, source, completed, created_at
            """),
            {"tenant_id": tenant_id, "title": title, "priority": priority, "source": source, "company_id": company_id, "due_date": due_date}
        )
        await self.db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def complete_task(self, task_id: str, tenant_id: str):
        result = await self.db.execute(
            text("UPDATE tasks SET completed = true WHERE id = :id AND tenant_id = :tenant_id RETURNING id, title, completed"),
            {"id": task_id, "tenant_id": tenant_id}
        )
        await self.db.commit()
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def get_pipeline(self, tenant_id: str):
        result = await self.db.execute(
            text("""
                SELECT stage, COUNT(*) as deals, COALESCE(SUM(estimated_value), 0) as value
                FROM opportunities WHERE tenant_id = :tenant_id AND stage NOT IN ('won', 'lost')
                GROUP BY stage ORDER BY array_position(ARRAY['identified','qualifying','developing','proposing','negotiating','closing'], stage)
            """),
            {"tenant_id": tenant_id}
        )
        stages_data = result.fetchall()
        stages = [{"id": r.stage, "label": r.stage, "deals": r.deals, "value": float(r.value)} for r in stages_data]
        total_value = sum(s["value"] for s in stages)
        weighted_value = sum(s["value"] * STAGE_WEIGHTS.get(s["id"], 0) for s in stages)
        return {"total_deals": sum(s["deals"] for s in stages), "total_value": total_value, "weighted_value": weighted_value, "stages": stages}

    async def list_opportunities(self, tenant_id: str, stage: str = None, page: int = 1, limit: int = 20):
        where = "WHERE tenant_id = :tenant_id"
        params = {"tenant_id": tenant_id}
        if stage:
            where += " AND stage = :stage"
            params["stage"] = stage
        offset = (page - 1) * limit
        result = await self.db.execute(
            text(f"SELECT id, company_id, title, stage, estimated_value, confidence, win_probability, source, risk_level, created_at, last_activity_at FROM opportunities {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {**params, "limit": limit, "offset": offset}
        )
        rows = [dict(r._mapping) for r in result.fetchall()]
        count_result = await self.db.execute(text(f"SELECT COUNT(*) FROM opportunities {where}"), params)
        total = count_result.scalar()
        return {"opportunities": rows, "total": total, "page": page}

    async def list_tasks(self, tenant_id: str, priority: str = None):
        where = "WHERE tenant_id = :tenant_id"
        params = {"tenant_id": tenant_id}
        if priority:
            where += " AND priority = :priority"
            params["priority"] = priority
        result = await self.db.execute(
            text(f"SELECT id, title, priority, source, completed, created_at FROM tasks {where} ORDER BY created_at DESC"),
            params
        )
        return [dict(r._mapping) for r in result.fetchall()]
