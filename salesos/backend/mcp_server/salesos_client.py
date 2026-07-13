"""SalesOS internal API client — wraps domain services for MCP tools."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import or_

from app.database import async_session
from app.modules.company.service import CompanyService
from app.modules.executive.service import ExecutiveService
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresOpportunityRepository,
)
from domains.commercial.opportunity.contracts.repository import OpportunityQuery
from domains.workflow import InMemoryWorkflowRepository, WorkflowEngine
from runtime.nba_engine import NBAEngine
from runtime.pipeline_analytics import PipelineAnalytics
from runtime.search_runtime import SearchRuntime, SearchStrategy

logger = logging.getLogger(__name__)


class SalesOSClient:
    """Wraps SalesOS domain services for use by MCP tools."""

    def __init__(self, tenant_id: str | None = None):
        self._tenant_id = tenant_id or "default"

    async def search_companies(self, query: str, limit: int = 10) -> list[dict]:
        async with async_session() as db:
            svc = CompanyService(db=db)
            companies, total = await svc.search_companies(
                tenant_id=self._tenant_id,
                query=query,
                page=1,
                page_size=limit,
            )
            return [
                {
                    "id": str(c.id),
                    "name_ar": c.name_ar,
                    "name_en": c.name_en,
                    "cr_number": c.cr_number,
                    "city": c.city,
                    "region": c.region,
                    "status": c.status,
                    "confidence_score": c.confidence_score,
                }
                for c in companies
            ]

    async def get_company(self, company_id: str) -> dict | None:
        async with async_session() as db:
            svc = CompanyService(db=db)
            try:
                company = await svc.get_company(company_id)
            except Exception:
                return None
            return {
                "id": str(company.id),
                "name_ar": company.name_ar,
                "name_en": company.name_en,
                "cr_number": company.cr_number,
                "city": company.city,
                "region": company.region,
                "status": company.status,
                "phone": company.phone,
                "email": company.email,
                "website": company.website,
                "activity_description": company.activity_description,
                "legal_form": company.legal_form,
                "employees_count": company.employees_count,
                "confidence_score": company.confidence_score,
                "created_at": str(company.created_at) if company.created_at else None,
                "updated_at": str(company.updated_at) if company.updated_at else None,
            }

    async def get_company_pipeline(self, company_id: str) -> dict:
        async with async_session() as db:
            opp_repo = PostgresOpportunityRepository(db)
            result = await opp_repo.query(
                OpportunityQuery(
                    tenant_id=self._tenant_id,
                    company_id=company_id,
                    page_size=50,
                )
            )
            return {
                "company_id": company_id,
                "total": result.total,
                "opportunities": [
                    {
                        "id": o.id,
                        "name": o.name,
                        "stage": o.stage,
                        "value": o.value,
                        "probability": o.probability,
                        "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                        "owner_id": o.owner_id,
                        "expected_close_date": str(o.expected_close_date) if o.expected_close_date else None,
                    }
                    for o in result.items
                ],
            }

    async def get_pipeline_summary(self) -> dict:
        async with async_session() as db:
            analytics = PipelineAnalytics(db, self._tenant_id)
            return await analytics.summary()

    async def get_opportunity(self, opportunity_id: str) -> dict | None:
        async with async_session() as db:
            opp_repo = PostgresOpportunityRepository(db)
            try:
                opp = await opp_repo.get_by_id(opportunity_id)
            except Exception:
                return None
            if not opp:
                return None
            return {
                "id": opp.id,
                "name": opp.name,
                "stage": opp.stage,
                "value": opp.value,
                "probability": opp.probability,
                "currency": opp.currency,
                "status": opp.status.value if hasattr(opp.status, "value") else str(opp.status),
                "company_id": opp.company_id,
                "owner_id": opp.owner_id,
                "description": opp.description,
                "expected_close_date": str(opp.expected_close_date) if opp.expected_close_date else None,
                "created_at": str(opp.created_at) if opp.created_at else None,
                "updated_at": str(opp.updated_at) if opp.updated_at else None,
            }

    async def evaluate_decision(self, company_id: str, context: str) -> dict:
        async with async_session() as session:
            nba = NBAEngine(
                session_factory=lambda: session,
                logger=logger,
            )
            result = await nba.recompute(company_id, self._tenant_id)
            if not result:
                return {"company_id": company_id, "action": "no_recommendation", "reason": "No data available"}
            return {
                "id": result.id,
                "opportunity_id": result.opportunity_id,
                "action": result.action,
                "reason": result.reason,
                "confidence": result.confidence,
                "confidence_label": result.confidence_label,
                "source": result.source,
                "alternatives": [{"action": a.action, "reason": a.reason, "confidence": a.confidence} for a in result.alternatives],
                "evidence": [{"type": e.type, "description": e.description, "source": e.source} for e in result.evidence],
                "risks": [{"type": r.type, "level": r.level, "description": r.description} for r in result.potential_risks],
            }

    async def get_decision_history(self, company_id: str, limit: int = 10) -> list[dict]:
        async with async_session() as session:
            from sqlalchemy import text
            rows = await session.execute(
                text("""
                    SELECT id, company_id, action, reason, confidence, created_at
                    FROM company_features
                    WHERE company_id = :cid AND tenant_id = :tid AND feature_name = 'nba'
                    ORDER BY computed_at DESC LIMIT :lim
                """),
                {"cid": company_id, "tid": self._tenant_id, "lim": limit},
            )
            return [
                {
                    "id": r["id"],
                    "company_id": r["company_id"],
                    "action": r["action"],
                    "reason": r["reason"],
                    "confidence": float(r["confidence"]),
                    "created_at": str(r["created_at"]) if r["created_at"] else None,
                }
                for r in rows.mappings().all()
            ]

    async def search(self, query: str, domain: str = "all") -> dict:
        async with async_session() as session:
            sr = SearchRuntime(
                session_factory=lambda: session,
                logger=logger,
            )
            strategy = SearchStrategy.HYBRID if domain == "all" else SearchStrategy(domain)
            result = await sr.search(
                query=query,
                tenant_id=self._tenant_id,
                strategy=strategy,
                limit=20,
            )
            return {
                "query": result.query,
                "strategy": result.strategy.value,
                "total": result.total,
                "took_ms": round(result.took_ms, 2),
                "items": [item.to_dict() for item in result.items],
            }

    async def search_employees(self, query: str, company_id: str | None = None) -> list[dict]:
        async with async_session() as db:
            from app.modules.identity.models import User

            stmt = __import__("sqlalchemy", fromlist=["select"]).select(User).where(
                User.tenant_id == self._tenant_id,
                or_(
                    User.full_name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                    User.role.ilike(f"%{query}%"),
                ),
            )
            if company_id:
                from app.modules.company.models import Company
                stmt = stmt.join(Company, Company.tenant_id == User.tenant_id).where(Company.id == company_id)
            result = await db.execute(stmt.limit(20))
            return [
                {
                    "id": str(u.id),
                    "full_name": u.full_name,
                    "full_name_ar": u.full_name_ar,
                    "email": u.email,
                    "role": u.role,
                    "phone": u.phone,
                    "is_active": u.is_active,
                }
                for u in result.scalars().all()
            ]

    async def get_revenue_analytics(self, timeframe: str = "monthly") -> dict:
        async with async_session() as db:
            svc = ExecutiveService(db, self._tenant_id)
            dashboard = await svc.get_dashboard()
            return {
                "revenue": {
                    "total_booked": dashboard.revenue.total_booked,
                    "total_pipeline": dashboard.revenue.total_pipeline,
                    "weighted_pipeline": dashboard.revenue.weighted_pipeline,
                    "forecast": dashboard.revenue.forecast,
                    "growth_percent": dashboard.revenue.growth_percent,
                },
                "pipeline": {
                    "total_deals": dashboard.pipeline.total_deals,
                    "total_value": dashboard.pipeline.total_value,
                    "won_deals": dashboard.pipeline.won_deals,
                    "lost_deals": dashboard.pipeline.lost_deals,
                    "win_rate": dashboard.pipeline.win_rate,
                    "avg_deal_size": dashboard.pipeline.avg_deal_size,
                    "by_stage": dashboard.pipeline.by_stage,
                },
                "team": {
                    "total_employees": dashboard.team.total_employees,
                    "active_employees": dashboard.team.active_employees,
                },
                "growth": {
                    "new_companies_30d": dashboard.growth.new_companies_30d,
                    "new_contacts_30d": dashboard.growth.new_contacts_30d,
                    "new_opportunities_30d": dashboard.growth.new_opportunities_30d,
                    "new_contracts_30d": dashboard.growth.new_contracts_30d,
                },
                "timeframe": timeframe,
            }

    async def get_market_intelligence(self, industry: str | None = None) -> dict:
        async with async_session() as db:
            from sqlalchemy import text

            industry_filter = ""
            params: dict[str, Any] = {"tid": self._tenant_id}
            if industry:
                industry_filter = " AND c.industry = :industry"
                params["industry"] = industry

            rows = await db.execute(
                text(f"""
                    SELECT c.industry, COUNT(*) as company_count,
                           COUNT(DISTINCT o.id) as opportunity_count,
                           COALESCE(SUM(o.value), 0) as total_pipeline_value
                    FROM companies c
                    LEFT JOIN commercial_opportunities o ON o.company_id::text = c.id::text AND o.tenant_id = :tid
                    WHERE c.tenant_id = :tid{industry_filter}
                    GROUP BY c.industry
                    ORDER BY total_pipeline_value DESC
                """),
                params,
            )
            industries = [
                {
                    "industry": r["industry"],
                    "company_count": r["company_count"],
                    "opportunity_count": r["opportunity_count"],
                    "total_pipeline_value": float(r["total_pipeline_value"]),
                }
                for r in rows.mappings().all()
            ]

            total_companies = sum(i["company_count"] for i in industries)
            total_pipeline = sum(i["total_pipeline_value"] for i in industries)

            return {
                "industries": industries,
                "total_industries": len(industries),
                "total_companies": total_companies,
                "total_pipeline_value": total_pipeline,
                "filter_industry": industry,
            }

    async def list_workflows(self, status: str | None = None) -> list[dict]:
        repo = InMemoryWorkflowRepository()
        workflows = await repo.list(self._tenant_id)
        result = []
        for w in workflows:
            if status and w.status != status:
                continue
            result.append({
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "trigger_type": w.trigger_type,
                "status": w.status,
                "steps_count": len(w.steps),
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None,
            })
        return result

    async def execute_workflow(self, workflow_id: str, context: dict) -> dict:
        repo = InMemoryWorkflowRepository()
        engine = WorkflowEngine(repo)
        wf = await repo.get(workflow_id, self._tenant_id)
        if not wf:
            return {"error": f"Workflow {workflow_id} not found"}
        if wf.status != "active":
            return {"error": f"Workflow is '{wf.status}', must be 'active'"}

        execution = await engine.execute(wf, context)
        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "error": execution.error,
            "steps": [
                {
                    "step_id": sr.step_id,
                    "step_type": sr.step_type,
                    "status": sr.status,
                    "result": sr.result,
                    "error": sr.error,
                }
                for sr in execution.step_results
            ],
        }

    async def get_kpi_metrics(self) -> dict:
        async with async_session() as db:
            svc = ExecutiveService(db, self._tenant_id)
            dashboard = await svc.get_dashboard()
            return {
                "revenue": {
                    "total_booked": dashboard.revenue.total_booked,
                    "total_pipeline": dashboard.revenue.total_pipeline,
                    "growth_percent": dashboard.revenue.growth_percent,
                },
                "pipeline": {
                    "total_deals": dashboard.pipeline.total_deals,
                    "win_rate": dashboard.pipeline.win_rate,
                },
                "team": {
                    "total_employees": dashboard.team.total_employees,
                },
                "health": {
                    "overall": dashboard.health.overall_health,
                    "data_completeness": dashboard.health.data_completeness,
                },
            }
