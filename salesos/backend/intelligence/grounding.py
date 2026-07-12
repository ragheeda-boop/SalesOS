"""Data grounding layer for AI agents — retrieve-then-generate."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentContext:
    """Structured grounding context retrieved from data sources."""
    company_info: dict[str, Any] = field(default_factory=dict)
    contacts: list[dict[str, Any]] = field(default_factory=list)
    opportunities: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    signals: list[dict[str, Any]] = field(default_factory=list)
    recent_activity: list[dict[str, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([self.company_info, self.contacts, self.opportunities,
                        self.relationships, self.signals, self.recent_activity])

    def to_prompt_block(self) -> str:
        lines = ["--- بيانات مُسترجعة للسياق ---"]
        if self.company_info:
            ci = self.company_info
            parts = [f"الشركة: {ci.get('name_ar') or ci.get('name_en', '')}"]
            for k, v in ci.items():
                if v and k not in ('name_ar', 'name_en'):
                    parts.append(f"{k}: {v}")
            lines.append("معلومات الشركة: " + " | ".join(parts))
        if self.contacts:
            names = [c.get('name', '') for c in self.contacts[:5]]
            lines.append(f"جهات الاتصال ({len(self.contacts)}): {', '.join(names)}")
        if self.opportunities:
            total = sum(float(o.get('amount', 0) or 0) for o in self.opportunities)
            stages = [o.get('stage', '') for o in self.opportunities]
            lines.append(f"الفرص ({len(self.opportunities)}): القيمة الإجمالية {total:.0f} | المراحل: {', '.join(stages)}")
        if self.recent_activity:
            events = [a.get('description', '') for a in self.recent_activity[:5]]
            lines.append("النشاط الأخير: " + " | ".join(events))
        if self.signals:
            sigs = [s.get('title', '') for s in self.signals[:5]]
            lines.append("الإشارات: " + " | ".join(sigs))
        if self.relationships:
            rels = [r.get('target_name', r.get('target_id', '')) for r in self.relationships[:5]]
            lines.append("العلاقات: " + ", ".join(rels))
        return "\n".join(lines)


class GroundingService:
    """Retrieves actual data from PostgreSQL/Neo4j to ground AI agents."""

    def __init__(self, db_session_factory=None, neo4j_driver=None):
        self._db_session_factory = db_session_factory
        self._neo4j_driver = neo4j_driver

    async def get_context(self, company_id: str, agent_type: str = "general") -> AgentContext:
        ctx = AgentContext()
        if self._db_session_factory:
            ctx.company_info = await self._get_company_info(company_id)
            ctx.contacts = await self._get_contacts(company_id)
            ctx.opportunities = await self._get_opportunities(company_id)
            ctx.recent_activity = await self._get_recent_activity(company_id)
        if self._neo4j_driver:
            ctx.relationships = await self._get_graph_relationships(company_id)
        ctx.signals = await self._get_signals(company_id)
        return ctx

    async def _get_company_info(self, company_id: str) -> dict[str, Any]:
        try:
            from sqlalchemy import text
            async with self._db_session_factory() as session:
                row = await session.execute(
                    text("""
                        SELECT name_ar, name_en, cr_number, city, region, industry,
                               status, activity_description, employees_count, annual_revenue
                        FROM companies WHERE id::text = :cid
                    """),
                    {"cid": company_id},
                )
                data = row.mappings().first()
                return dict(data) if data else {}
        except Exception:
            return {}

    async def _get_contacts(self, company_id: str) -> list[dict[str, Any]]:
        try:
            from sqlalchemy import text
            async with self._db_session_factory() as session:
                rows = await session.execute(
                    text("""
                        SELECT id::text, name, email, phone, position, department, is_decision_maker
                        FROM contacts WHERE company_id::text = :cid
                        ORDER BY is_decision_maker DESC NULLS LAST
                    """),
                    {"cid": company_id},
                )
                return [dict(r) for r in rows.mappings().all()]
        except Exception:
            return []

    async def _get_opportunities(self, company_id: str) -> list[dict[str, Any]]:
        try:
            from sqlalchemy import text
            async with self._db_session_factory() as session:
                rows = await session.execute(
                    text("""
                        SELECT id::text, title, stage, amount, probability, expected_close_date
                        FROM opportunities WHERE company_id::text = :cid
                        ORDER BY amount DESC NULLS LAST
                    """),
                    {"cid": company_id},
                )
                return [dict(r) for r in rows.mappings().all()]
        except Exception:
            return []

    async def _get_graph_relationships(self, company_id: str) -> list[dict[str, Any]]:
        try:
            async with self._neo4j_driver.session() as session:
                result = await session.run(
                    """
                    MATCH (c:Company {id: $cid})-[r]-(related)
                    RETURN related.id AS target_id, related.name AS target_name,
                           labels(related) AS target_type, type(r) AS relationship_type,
                           r.strength AS strength
                    """,
                    cid=company_id,
                )
                data = await result.data()
                return [dict(record) for record in data]
        except Exception:
            return []

    async def _get_signals(self, company_id: str) -> list[dict[str, Any]]:
        try:
            from sqlalchemy import text
            async with self._db_session_factory() as session:
                rows = await session.execute(
                    text("""
                        SELECT id::text, signal_type, title, description, intensity, priority, detected_at
                        FROM buying_signals
                        WHERE company_id::text = :cid
                        ORDER BY detected_at DESC LIMIT 20
                    """),
                    {"cid": company_id},
                )
                return [dict(r) for r in rows.mappings().all()]
        except Exception:
            return []

    async def _get_recent_activity(self, company_id: str) -> list[dict[str, Any]]:
        try:
            from sqlalchemy import text
            async with self._db_session_factory() as session:
                rows = await session.execute(
                    text("""
                        SELECT id::text, event_type, description, occurred_at
                        FROM timeline_events
                        WHERE company_id::text = :cid
                        ORDER BY occurred_at DESC LIMIT 20
                    """),
                    {"cid": company_id},
                )
                return [dict(r) for r in rows.mappings().all()]
        except Exception:
            return []
