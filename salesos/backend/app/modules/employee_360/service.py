from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import User
from app.modules.company.models import Company
from app.modules.contact.models import Contact

from .schemas import (
    AICoachAction,
    ActivityIntelligence,
    CalendarIntelligence,
    EmailIntelligence,
    EmployeeKPIs,
    EmployeePortfolio,
    EmployeePortfolioItem,
    EmployeeProfile,
    Employee360Response,
)


class Employee360Service:
    def __init__(self, db: AsyncSession, activity_runtime: Any = None, logger: Any = None):
        self.db = db
        self.activity_runtime = activity_runtime
        self.logger = logger

    async def get_360(self, user_id: str, tenant_id: str) -> Employee360Response:
        profile = await self._get_profile(user_id, tenant_id)
        portfolio = await self._get_portfolio(tenant_id, user_id)
        activity = await self._get_activity_intelligence(tenant_id, user_id)
        kpis = self._compute_kpis(portfolio, activity)

        ai_coach = self._generate_coach_actions(portfolio, kpis)

        return Employee360Response(
            profile=profile,
            portfolio=portfolio,
            calendar_intelligence=CalendarIntelligence(),
            email_intelligence=EmailIntelligence(),
            activity_intelligence=activity,
            kpis=kpis,
            ai_coach=ai_coach,
        )

    async def _get_profile(self, user_id: str, tenant_id: str) -> EmployeeProfile:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            from app.common.exceptions import NotFoundError
            raise NotFoundError("User", user_id)

        # Get team members (same tenant)
        team_result = await self.db.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.is_active == True,
            ).order_by(User.full_name).limit(50)
        )
        team = [
            {"id": str(u.id), "full_name": u.full_name, "email": u.email, "role": u.role}
            for u in team_result.scalars().all()
            if str(u.id) != user_id
        ]

        return EmployeeProfile(
            id=str(user.id),
            full_name=user.full_name,
            full_name_ar=user.full_name_ar,
            email=user.email,
            role=user.role,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            tenant_id=str(user.tenant_id),
            created_at=user.created_at,
            team=team[:10],
            manager=None,
        )

    async def _get_portfolio(self, tenant_id: str, user_id: str) -> EmployeePortfolio:
        import uuid

        companies = []
        contacts_list = []
        pipeline = []
        contracts = []

        try:
            from domains.commercial.opportunity.contracts.repository import OpportunityQuery
            from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository

            opp_repo = PostgresOpportunityRepository(self.db)
            result = await opp_repo.query(
                OpportunityQuery(tenant_id=tenant_id, owner_id=user_id, page_size=100)
            )
            pipeline = [
                EmployeePortfolioItem(
                    id=o.id, name=o.name, type="opportunity",
                    value=o.value, status=o.stage,
                    company_id=o.company_id,
                )
                for o in result.items
            ]
        except Exception:
            pass

        try:
            contact_result = await self.db.execute(
                select(Contact).where(
                    Contact.tenant_id == uuid.UUID(tenant_id),
                ).limit(50)
            )
            contacts_list = [
                {"id": str(c.id), "name": c.name, "email": c.email,
                 "phone": c.phone, "company_id": str(c.company_id) if c.company_id else None}
                for c in contact_result.scalars().all()
            ]
        except Exception:
            pass

        try:
            company_result = await self.db.execute(
                select(Company).where(
                    Company.tenant_id == uuid.UUID(tenant_id),
                ).limit(50)
            )
            companies = [
                {"id": str(c.id), "name_ar": c.name_ar, "name_en": c.name_en,
                 "cr_number": c.cr_number, "status": c.status, "city": c.city}
                for c in company_result.scalars().all()
            ]
        except Exception:
            pass

        total_revenue = sum(p.value for p in pipeline if p.status in ("closed_won", "won"))

        return EmployeePortfolio(
            companies=companies,
            contacts=contacts_list,
            pipeline=pipeline,
            revenue=total_revenue,
            contracts=contracts,
            projects=[],
        )

    async def _get_activity_intelligence(self, tenant_id: str, user_id: str) -> ActivityIntelligence:
        if not self.activity_runtime:
            return ActivityIntelligence()

        try:
            items, total = await self.activity_runtime.get_by_actor(
                actor=user_id, tenant_id=tenant_id, limit=50
            )
        except Exception:
            return ActivityIntelligence()

        meetings = sum(1 for a in items if a.get("action", "").startswith("meeting"))
        emails = sum(1 for a in items if a.get("action", "").startswith("email"))
        calls = sum(1 for a in items if a.get("action", "").startswith("call"))
        tasks = sum(1 for a in items if a.get("action", "").startswith("task"))

        return ActivityIntelligence(
            meetings=meetings,
            emails=emails,
            calls=calls,
            tasks=tasks,
            total=total,
            recent=items[:20],
        )

    def _compute_kpis(self, portfolio: EmployeePortfolio, activity: ActivityIntelligence) -> EmployeeKPIs:
        total_pipeline = sum(p.value for p in portfolio.pipeline if p.status not in ("closed_won", "closed_lost", "won", "lost"))
        won_deals = [p for p in portfolio.pipeline if p.status in ("closed_won", "won")]
        lost_deals = [p for p in portfolio.pipeline if p.status in ("closed_lost", "lost")]
        total_deals = len(won_deals) + len(lost_deals)
        win_rate = len(won_deals) / total_deals if total_deals > 0 else 0.0

        return EmployeeKPIs(
            revenue=portfolio.revenue,
            pipeline=total_pipeline,
            win_rate=round(win_rate, 2),
            activities=activity.total,
            productivity=round(activity.total / 30.0, 2) if activity.total > 0 else 0.0,
        )

    def _generate_coach_actions(self, portfolio: EmployeePortfolio, kpis: EmployeeKPIs) -> list[AICoachAction]:
        actions = []
        if kpis.pipeline == 0 and kpis.revenue == 0:
            actions.append(AICoachAction(
                type="pipeline_empty", title="Build your pipeline",
                description="You have no active deals. Start prospecting.",
                priority="high",
            ))
        if kpis.win_rate < 0.3 and kpis.win_rate > 0:
            actions.append(AICoachAction(
                type="win_rate_low", title="Improve win rate",
                description="Your win rate is below 30%. Review your sales process.",
                priority="medium",
            ))
        if not actions:
            actions.append(AICoachAction(
                type="on_track", title="You're on track",
                description="Keep following up with your pipeline.",
                priority="low",
            ))
        return actions
