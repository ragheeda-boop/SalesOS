import contextlib
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company
from app.modules.contact.models import Contact
from app.modules.identity.models import User

from .schemas import (
    ActivityIntelligence,
    AICoachAction,
    CalendarIntelligence,
    EmailIntelligence,
    Employee360Response,
    EmployeeKPIs,
    EmployeePortfolio,
    EmployeePortfolioItem,
    EmployeeProfile,
    EmployeeSignals,
    EmployeeSignalSummary,
    EmployeeTimeline,
    PeerComparison,
    PerformanceInsights,
    RiskFlagItem,
    ScoreTrend,
    TimelineEvent,
)


def _to_employee_signals(signal_data: dict | None) -> EmployeeSignals:
    if not signal_data:
        return EmployeeSignals()
    summary = signal_data.get("summary")
    if isinstance(summary, EmployeeSignalSummary):
        signals_summary = summary
    elif isinstance(summary, dict):
        signals_summary = EmployeeSignalSummary(**summary)
    elif summary is not None:
        signals_summary = EmployeeSignalSummary(
            total_signals=int(getattr(summary, "total_signals", 0) or 0),
            by_source=dict(getattr(summary, "by_source", {}) or {}),
            by_type=dict(getattr(summary, "by_type", {}) or {}),
            recent_signals=list(getattr(summary, "recent_signals", []) or []),
        )
    else:
        signals_summary = EmployeeSignalSummary()
    score = signal_data.get("score")
    return EmployeeSignals(
        signals=signals_summary,
        score=score if isinstance(score, dict) else None,
    )


class Employee360Service:
    def __init__(
        self,
        db: AsyncSession,
        activity_runtime: Any = None,
        logger: Any = None,
        signal_pipeline: Any = None,
        signal_repo: Any = None,
    ):
        self.db = db
        self.activity_runtime = activity_runtime
        self.logger = logger
        self.signal_pipeline = signal_pipeline
        self.signal_repo = signal_repo

    async def _recover_session(self) -> None:
        """Clear an aborted transaction so later reads in the same request can continue."""
        with contextlib.suppress(Exception):
            await self.db.rollback()

    async def get_360(self, user_id: str, tenant_id: str) -> Employee360Response:
        # Sequential DB work only — AsyncSession is not safe under asyncio.gather.
        # Concurrent use left the request transaction aborted; commit then raised
        # PendingRollbackError and the browser saw axios "Network Error".
        profile = await self._get_profile(user_id, tenant_id)
        portfolio = await self._get_portfolio(tenant_id, user_id)
        activity = await self._get_activity_intelligence(tenant_id, user_id)
        signal_data = await self._get_signals_data(user_id, tenant_id)

        kpis = self._compute_kpis(portfolio, activity)
        if signal_data:
            score_data = signal_data.get("score") or {}
            kpis.signal_volume_score = score_data.get("signal_volume_score", 0.0)
            kpis.diversity_score = score_data.get("diversity_score", 0.0)
            kpis.completion_rate = score_data.get("completion_rate", 0.0)
            kpis.signal_count = (signal_data.get("summary") or {}).get("total_signals", 0)

        timeline = await self._get_timeline(user_id, tenant_id)
        performance = await self._get_performance(user_id, tenant_id, signal_data)

        ai_coach = self._generate_coach_actions(portfolio, kpis, performance)

        # ── ADR-012 Activity Intelligence Integration (employee-scoped events) ──
        calendar_intelligence = CalendarIntelligence()
        email_intelligence = EmailIntelligence()
        try:
            from intelligence.activity_intelligence.readers.postgres_readers import (
                PostgresEmailReader,
                PostgresMeetingReader,
            )

            email_reader = PostgresEmailReader(self.db)
            meeting_reader = PostgresMeetingReader(self.db)

            sent = await email_reader.count_by_employee(user_id, tenant_id, direction="outbound")
            received = await email_reader.count_by_employee(user_id, tenant_id, direction="inbound")
            meeting_count = await meeting_reader.count_by_employee(user_id, tenant_id)
            meeting_hours = await meeting_reader.hours_by_employee(user_id, tenant_id)
            reply_rate = round(sent / max(1, received), 4)

            email_intelligence = EmailIntelligence(
                sent=sent,
                received=received,
                replies=int(reply_rate * 100),
                avg_response_hours=0,
                top_companies=[],
                top_contacts=[],
            )
            calendar_intelligence = CalendarIntelligence(
                today_count=0,
                week_count=meeting_count,
                month_count=meeting_count,
                total_hours=meeting_hours,
                avg_duration_minutes=0,
                unique_companies_met=0,
                upcoming=[],
            )
            kpis.response_rate = reply_rate
            kpis.follow_up_rate = min(1.0, max(0.0, reply_rate))
        except Exception as e:
            await self._recover_session()
            if self.logger:
                self.logger.warn("employee_360.adr012_failed", user_id=user_id, error=str(e))

        return Employee360Response(
            profile=profile,
            portfolio=portfolio,
            calendar_intelligence=calendar_intelligence,
            email_intelligence=email_intelligence,
            activity_intelligence=activity,
            kpis=kpis,
            ai_coach=ai_coach,
            signals=_to_employee_signals(signal_data),
            timeline=timeline,
            performance=performance,
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
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
            )
            .order_by(User.full_name)
            .limit(10)
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
            department=user.department,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            tenant_id=str(user.tenant_id),
            created_at=user.created_at,
            team=team[:10],
            manager=None,
        )

    async def _get_portfolio(self, tenant_id: str, user_id: str) -> EmployeePortfolio:
        companies = []
        contacts_list = []
        pipeline = []
        contracts: list[EmployeePortfolioItem] = []

        try:
            from domains.commercial.infrastructure.postgres_repositories import (
                PostgresOpportunityRepository,
            )
            from domains.commercial.opportunity.contracts.repository import OpportunityQuery

            opp_repo = PostgresOpportunityRepository(self.db)
            result = await opp_repo.query(
                OpportunityQuery(tenant_id=tenant_id, owner_id=user_id, page_size=100)
            )
            pipeline = [
                EmployeePortfolioItem(
                    id=o.id,
                    name=o.name,
                    type="opportunity",
                    value=o.value,
                    status=o.stage,
                    company_id=o.company_id,
                    company_name=getattr(o, "company_name", None)
                    or getattr(o, "account_name", None),
                )
                for o in result.items
            ]
        except Exception as e:
            await self._recover_session()
            if self.logger:
                self.logger.warn(
                    "employee_360.portfolio_opportunities_failed", user_id=user_id, error=str(e)
                )

        try:
            contact_result = await self.db.execute(
                select(Contact)
                .where(
                    Contact.tenant_id == uuid.UUID(tenant_id),
                )
                .limit(50)
            )
            contacts_list = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "company_id": str(c.company_id) if c.company_id else None,
                }
                for c in contact_result.scalars().all()
            ]
        except Exception as e:
            await self._recover_session()
            if self.logger:
                self.logger.warn("employee_360.portfolio_contacts_failed", error=str(e))

        try:
            company_result = await self.db.execute(
                select(Company)
                .where(
                    Company.tenant_id == uuid.UUID(tenant_id),
                )
                .limit(50)
            )
            companies = [
                {
                    "id": str(c.id),
                    "name_ar": c.name_ar,
                    "name_en": c.name_en,
                    "cr_number": c.cr_number,
                    "status": c.status,
                    "city": c.city,
                }
                for c in company_result.scalars().all()
            ]
        except Exception as e:
            await self._recover_session()
            if self.logger:
                self.logger.warn("employee_360.portfolio_companies_failed", error=str(e))

        total_revenue = sum(p.value for p in pipeline if p.status in ("closed_won", "won"))

        return EmployeePortfolio(
            companies=companies,
            contacts=contacts_list,
            pipeline=pipeline,
            revenue=total_revenue,
            contracts=contracts,
            projects=[],
        )

    async def _get_activity_intelligence(
        self, tenant_id: str, user_id: str
    ) -> ActivityIntelligence:
        if not self.activity_runtime:
            return ActivityIntelligence()

        try:
            items, total = await self.activity_runtime.get_by_actor(
                actor=user_id, tenant_id=tenant_id, limit=50
            )
        except Exception:
            await self._recover_session()
            return ActivityIntelligence()

        meetings = sum(1 for a in items if a.get("action", "").startswith("meeting"))
        emails = sum(1 for a in items if a.get("action", "").startswith("email"))
        calls = sum(1 for a in items if a.get("action", "").startswith("call"))
        tasks = sum(1 for a in items if a.get("action", "").startswith("task"))
        notes = sum(1 for a in items if a.get("action", "").startswith("note"))
        documents = sum(
            1
            for a in items
            if a.get("action", "").startswith("document") or a.get("action", "").startswith("file")
        )

        return ActivityIntelligence(
            meetings=meetings,
            emails=emails,
            calls=calls,
            tasks=tasks,
            notes=notes,
            documents=documents,
            total=total,
            recent=items[:20],
        )

    def _compute_kpis(
        self, portfolio: EmployeePortfolio, activity: ActivityIntelligence
    ) -> EmployeeKPIs:
        total_pipeline = sum(
            p.value
            for p in portfolio.pipeline
            if p.status not in ("closed_won", "closed_lost", "won", "lost")
        )
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

    async def _get_signals_data(self, user_id: str, tenant_id: str) -> dict | None:
        if not self.signal_repo:
            return None
        try:
            summary = await self.signal_repo.get_summary(user_id, tenant_id)
            score = await self.signal_repo.get_latest_score(user_id, tenant_id)
            return {
                "summary": summary,
                "score": score.__dict__ if score else None,
            }
        except Exception:
            await self._recover_session()
            return None

    async def _get_timeline(self, user_id: str, tenant_id: str) -> EmployeeTimeline:
        if not self.signal_repo:
            return EmployeeTimeline()
        try:
            items, total, _ = await self.signal_repo.get_by_employee(
                user_id,
                tenant_id,
                limit=10,
            )
            events = [
                TimelineEvent(
                    id=s.id,
                    signal_type=s.signal_type,
                    source=s.source,
                    metadata=s.metadata or {},
                    timestamp=s.timestamp,
                )
                for s in items
            ]
            return EmployeeTimeline(events=events, total=total)
        except Exception:
            await self._recover_session()
            return EmployeeTimeline()

    async def _get_performance(
        self,
        user_id: str,
        tenant_id: str,
        signal_data: dict | None,
    ) -> PerformanceInsights:
        if not self.signal_repo:
            return PerformanceInsights()
        try:
            from domains.employee.performance import EmployeePerformanceEngine

            engine = EmployeePerformanceEngine(repository=self.signal_repo)

            current_score = None
            if signal_data and signal_data.get("score"):
                from domains.employee.models import EmployeeScore

                score_dict = signal_data["score"]
                current_score = EmployeeScore(
                    id=score_dict.get("id", ""),
                    employee_id=score_dict.get("employee_id", user_id),
                    tenant_id=score_dict.get("tenant_id", tenant_id),
                    overall_score=score_dict.get("overall_score", 0.0),
                    signal_volume_score=score_dict.get("signal_volume_score", 0.0),
                    recency_score=score_dict.get("recency_score", 0.0),
                    diversity_score=score_dict.get("diversity_score", 0.0),
                    completion_rate=score_dict.get("completion_rate", 0.0),
                    confidence_interval_low=score_dict.get("confidence_interval_low", 0.0),
                    confidence_interval_high=score_dict.get("confidence_interval_high", 0.0),
                    signal_count=score_dict.get("signal_count", 0),
                )

            all_signals, _, _ = await self.signal_repo.get_by_employee(
                user_id,
                tenant_id,
                limit=500,
            )

            result = await engine.compute_performance(
                user_id,
                tenant_id,
                current_score,
                all_signals,
            )
            return PerformanceInsights(
                trend=ScoreTrend(**result.get("trend", {})),
                peer_comparison=PeerComparison(**result.get("peer_comparison", {})),
                risk_flags=[RiskFlagItem(**f) for f in result.get("risk_flags", [])],
            )
        except Exception:
            await self._recover_session()
            return PerformanceInsights()

    def _generate_coach_actions(
        self,
        portfolio: EmployeePortfolio,
        kpis: EmployeeKPIs,
        performance: PerformanceInsights | None = None,
    ) -> list[AICoachAction]:
        actions: list[AICoachAction] = []

        # ── Pipeline & Revenue ──
        if kpis.pipeline == 0 and kpis.revenue == 0:
            actions.append(
                AICoachAction(
                    type="pipeline_empty",
                    title="Build your pipeline",
                    description="You have no active deals. Start prospecting by identifying target companies in your territory.",  # noqa: E501
                    priority="high",
                )
            )
        elif kpis.pipeline > 0 and kpis.revenue == 0:
            actions.append(
                AICoachAction(
                    type="no_revenue",
                    title="Convert pipeline to revenue",
                    description=f"You have {kpis.pipeline:,.0f} SAR in pipeline but no closed revenue. Focus on advancing deals to close.",  # noqa: E501
                    priority="high",
                )
            )
        if 0 < kpis.win_rate < 0.3:
            actions.append(
                AICoachAction(
                    type="win_rate_low",
                    title="Improve win rate",
                    description="Your win rate is below 30%. Review deal qualification criteria and focus on high-probability opportunities.",  # noqa: E501
                    priority="medium",
                )
            )

        # ── Signal Quality ──
        if kpis.signal_count > 0 and kpis.diversity_score < 0.3:
            actions.append(
                AICoachAction(
                    type="low_signal_diversity",
                    title="Diversify your activity types",
                    description="Your signals are concentrated in few areas. Mix calls, emails, and meetings for better engagement.",  # noqa: E501
                    priority="medium",
                )
            )
        if kpis.signal_count < 10 and kpis.pipeline > 0:
            actions.append(
                AICoachAction(
                    type="low_activity",
                    title="Increase activity volume",
                    description=f"Only {kpis.signal_count} signals recorded. Aim for consistent daily activity to drive pipeline.",  # noqa: E501
                    priority="medium",
                )
            )
        if kpis.completion_rate < 0.3 and kpis.signal_count > 0:
            actions.append(
                AICoachAction(
                    type="low_completion",
                    title="Complete your tasks and workflows",
                    description=f"Task completion rate is {round(kpis.completion_rate * 100)}%. Complete outstanding items to maintain momentum.",  # noqa: E501
                    priority="medium",
                )
            )

        # ── Response & Follow-up ──
        if kpis.response_rate > 0 and kpis.response_rate < 0.5:
            actions.append(
                AICoachAction(
                    type="low_response_rate",
                    title="Respond faster to communications",
                    description=f"Response rate is {round(kpis.response_rate * 100)}%. Faster responses improve win rates and customer satisfaction.",  # noqa: E501
                    priority="medium",
                )
            )
        if kpis.follow_up_rate > 0 and kpis.follow_up_rate < 0.3:
            actions.append(
                AICoachAction(
                    type="low_follow_up",
                    title="Increase follow-up consistency",
                    description=f"Follow-up rate is {round(kpis.follow_up_rate * 100)}%. Consistent follow-ups are the top predictor of deal closure.",  # noqa: E501
                    priority="high",
                )
            )

        # ── Performance Risk Flags ──
        if performance:
            for flag in performance.risk_flags:
                if flag.flag == "declining_signals" and flag.severity == "high":
                    actions.append(
                        AICoachAction(
                            type="declining_signals",
                            title="Activity dropping sharply",
                            description=f"{flag.message}. Review your weekly plan and identify blockers.",  # noqa: E501
                            priority="high",
                        )
                    )
                elif flag.flag == "low_engagement" and flag.severity in ("high", "medium"):
                    actions.append(
                        AICoachAction(
                            type="low_engagement",
                            title="Increase customer engagement",
                            description=f"{flag.message}. Schedule outreach calls and meetings this week.",  # noqa: E501
                            priority="high" if flag.severity == "high" else "medium",
                        )
                    )
                elif flag.flag == "declining_score":
                    actions.append(
                        AICoachAction(
                            type="score_declining",
                            title="Performance score declining",
                            description=f"{flag.message}. Focus on consistent daily activity to reverse the trend.",  # noqa: E501
                            priority="high",
                        )
                    )

        # ── Productivity ──
        if kpis.productivity < 0.5 and kpis.activities > 0:
            actions.append(
                AICoachAction(
                    type="low_productivity",
                    title="Boost your daily productivity",
                    description=f"Productivity score is {round(kpis.productivity * 100)}%. Set daily activity targets and track your progress.",  # noqa: E501
                    priority="medium",
                )
            )
        if kpis.activities > 80:
            actions.append(
                AICoachAction(
                    type="high_performer",
                    title="Excellent activity levels",
                    description=f"You have {kpis.activities} activities this month. Keep up the great work and focus on quality over quantity.",  # noqa: E501
                    priority="low",
                )
            )

        # ── Fallback ──
        if not actions:
            actions.append(
                AICoachAction(
                    type="on_track",
                    title="You're on track",
                    description="Your activity, pipeline, and performance indicators are healthy. Keep maintaining your rhythm.",  # noqa: E501
                    priority="low",
                )
            )

        # ── Sort by priority ──
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda a: priority_order.get(a.priority, 2))
        return actions[:7]
