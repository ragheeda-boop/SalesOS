"""PostgreSQL repository implementations for all commercial domains."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from domains.commercial.activity.contracts.models import (
    Activity, ActivityOutcome, ActivitySession, ActivityStatus, ActivityType, OutcomeDefinition,
)
from domains.commercial.activity.contracts.repository import ActivityRepository
from domains.commercial.contract.models import Contract, ContractParty, ContractObligation, ContractStatus, RenewalRule
from domains.commercial.contract.repo import ContractKPIs
from domains.commercial.contract.repo import ContractRepository
from domains.commercial.opportunity.contracts.models import Opportunity, OpportunityStage, OpportunityStatus, PipelineDefinition
from domains.commercial.opportunity.contracts.repository import OpportunityRepository
from domains.commercial.pipeline.contracts.models import PipelineDefinition as PipelineDef, StageEntry
from domains.commercial.pipeline.contracts.repository import PipelineKPIs, PipelineRepository
from domains.commercial.proposal.contracts.models import Proposal, ProposalStatus
from domains.commercial.proposal.contracts.repository import ProposalKPIs, ProposalRepository
from domains.commercial.quote.contracts.models import Quote, QuoteLine, QuoteStatus
from domains.commercial.quote.contracts.repository import QuoteRepository, QuoteRevenueKPIs
from domains.revenue.analytics.models import AnalyticsSnapshot, KPI, KPIValue, MetricCategory
from domains.revenue.analytics.repo import AnalyticsRepository
from domains.revenue.forecast.models import ForecastExplanation, ForecastLine, ForecastScenario, ForecastSnapshot, ForecastSnapshotStatus
from domains.revenue.forecast.repo import ForecastRepository
from domains.decision.context.models import DecisionContext, Policy
from domains.decision.context.repo import DecisionRepository
from domains.decision.recommendation.models import Recommendation, RecommendationStatus
from domains.decision.recommendation.repo import RecommendationRepository

from domains.commercial.meeting import Meeting
from domains.commercial.meeting.repository import MeetingRepository
from domains.commercial.email import Email
from domains.commercial.email.repository import EmailRepository

from .models import (
    ActivityModel, ActivitySessionModel, AnalyticsSnapshotModel,
    ContractModel, DecisionContextModel, EmailModel, ForecastSnapshotModel,
    MeetingModel, OpportunityModel, PipelineDefinitionModel, PolicyModel,
    ProposalModel, QuoteLineModel, QuoteModel, RecommendationModel,
    StageEntryModel,
)


class PostgresOpportunityRepository(OpportunityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, opportunity: Opportunity) -> Opportunity:
        stmt = select(OpportunityModel).where(OpportunityModel.id == opportunity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.name = opportunity.name
            model.value = opportunity.value
            model.currency = opportunity.currency
            model.stage = opportunity.stage
            model.probability = opportunity.probability
            model.expected_close_date = opportunity.expected_close_date
            model.owner_id = opportunity.owner_id
            model.status = opportunity.status.value
            model.won_amount = opportunity.won_amount
            model.loss_reason = opportunity.loss_reason
            model.description = opportunity.description
            model.tags = opportunity.tags
            model.extra_data = opportunity.metadata
            model.updated_at = datetime.now(timezone.utc)
        else:
            model = OpportunityModel(
                id=opportunity.id, tenant_id=opportunity.tenant_id,
                company_id=opportunity.company_id, name=opportunity.name,
                value=opportunity.value, currency=opportunity.currency,
                stage=opportunity.stage, probability=opportunity.probability,
                expected_close_date=opportunity.expected_close_date,
                owner_id=opportunity.owner_id, status=opportunity.status.value,
                won_amount=opportunity.won_amount, loss_reason=opportunity.loss_reason,
                description=opportunity.description, tags=opportunity.tags,
                extra_data=opportunity.metadata,
            )
            self.session.add(model)
        await self.session.flush()
        return opportunity

    async def get(self, opportunity_id: str) -> Optional[Opportunity]:
        stmt = select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def query(self, query_data: Any) -> Any:
        q = select(OpportunityModel).where(OpportunityModel.tenant_id == query_data.tenant_id)
        if query_data.company_id:
            q = q.where(OpportunityModel.company_id == query_data.company_id)
        if query_data.owner_id:
            q = q.where(OpportunityModel.owner_id == query_data.owner_id)
        if query_data.stage:
            q = q.where(OpportunityModel.stage == query_data.stage)
        if query_data.status:
            q = q.where(OpportunityModel.status == query_data.status.value)
        if query_data.search:
            q = q.where(OpportunityModel.name.ilike(f"%{query_data.search}%"))
        total_q = select(func.count()).select_from(q.subquery())
        total_result = await self.session.execute(total_q)
        total = total_result.scalar() or 0
        offset = (query_data.page - 1) * query_data.page_size
        q = q.offset(offset).limit(query_data.page_size)
        result = await self.session.execute(q)
        items = [self._to_domain(r) for r in result.scalars().all()]
        from dataclasses import dataclass
        return type("OpportunityResult", (), {"items": items, "total": total, "page": query_data.page, "page_size": query_data.page_size})()

    async def delete(self, opportunity_id: str) -> None:
        stmt = select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()

    async def count_by_stage(self, tenant_id: str) -> dict[str, int]:
        stmt = select(OpportunityModel.stage, func.count()).where(
            OpportunityModel.tenant_id == tenant_id,
            OpportunityModel.status == "open",
        ).group_by(OpportunityModel.stage)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result}

    async def total_value_by_stage(self, tenant_id: str) -> dict[str, float]:
        stmt = select(OpportunityModel.stage, func.sum(OpportunityModel.value)).where(
            OpportunityModel.tenant_id == tenant_id,
            OpportunityModel.status == "open",
        ).group_by(OpportunityModel.stage)
        result = await self.session.execute(stmt)
        return {row[0]: float(row[1]) for row in result if row[1]}

    async def win_rate(self, tenant_id: str) -> float:
        stmt = select(
            func.count().filter(OpportunityModel.status == "won"),
            func.count(),
        ).where(OpportunityModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        won, total = result.one()
        return won / total if total > 0 else 0.0

    def _to_domain(self, model: OpportunityModel) -> Opportunity:
        return Opportunity(
            id=model.id, tenant_id=model.tenant_id, company_id=model.company_id,
            name=model.name, value=model.value, currency=model.currency,
            stage=model.stage, probability=model.probability,
            expected_close_date=model.expected_close_date,
            owner_id=model.owner_id, status=OpportunityStatus(model.status),
            won_amount=model.won_amount, loss_reason=model.loss_reason,
            description=model.description, tags=model.tags or [],
            metadata=model.extra_data or {},
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresPipelineRepository(PipelineRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_definition(self, pipeline: PipelineDef) -> PipelineDef:
        stmt = select(PipelineDefinitionModel).where(PipelineDefinitionModel.id == pipeline.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            model = PipelineDefinitionModel(
                id=pipeline.id, tenant_id=pipeline.tenant_id,
                name=pipeline.name if hasattr(pipeline, 'name') else "default",
                stages=[{"name": s.name, "name_ar": s.name_ar, "order": s.order, "default_probability": s.default_probability, "is_terminal": s.is_terminal} for s in pipeline.stages],
            )
            self.session.add(model)
        await self.session.flush()
        return pipeline

    async def get_definition(self, pipeline_id: str) -> Optional[PipelineDef]:
        stmt = select(PipelineDefinitionModel).where(PipelineDefinitionModel.id == pipeline_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        stages = [OpportunityStage(**s) for s in (model.stages or [])]
        p = PipelineDef(tenant_id=model.tenant_id, stages=stages)
        p.id = model.id
        return p

    async def list_definitions(self, tenant_id: str) -> list:
        stmt = select(PipelineDefinitionModel).where(PipelineDefinitionModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return [PipelineDef(tenant_id=r.tenant_id) for r in result.scalars().all()]

    async def save_stage_entry(self, entry: StageEntry) -> StageEntry:
        model = StageEntryModel(
            id=entry.id if hasattr(entry, 'id') else str(uuid.uuid4()),
            tenant_id=entry.tenant_id if hasattr(entry, 'tenant_id') else "",
            opportunity_id=entry.opportunity_id,
            pipeline_id=entry.pipeline_id,
            from_stage=entry.from_stage,
            to_stage=entry.to_stage,
            entered_at=entry.entered_at or datetime.now(timezone.utc),
        )
        self.session.add(model)
        await self.session.flush()
        return entry

    async def get_active_stage_entry(self, opportunity_id: str) -> Optional[StageEntry]:
        stmt = select(StageEntryModel).where(
            StageEntryModel.opportunity_id == opportunity_id,
            StageEntryModel.exited_at.is_(None),
        ).order_by(StageEntryModel.entered_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return StageEntry(
            opportunity_id=model.opportunity_id, pipeline_id=model.pipeline_id,
            from_stage=model.from_stage, to_stage=model.to_stage,
            entered_at=model.entered_at, exited_at=model.exited_at,
            duration_hours=model.duration_hours,
        )

    async def get_stage_history(self, opportunity_id: str) -> list:
        stmt = select(StageEntryModel).where(
            StageEntryModel.opportunity_id == opportunity_id
        ).order_by(StageEntryModel.entered_at.asc())
        result = await self.session.execute(stmt)
        return [StageEntry(
            opportunity_id=r.opportunity_id, pipeline_id=r.pipeline_id,
            from_stage=r.from_stage, to_stage=r.to_stage,
            entered_at=r.entered_at, exited_at=r.exited_at, duration_hours=r.duration_hours,
        ) for r in result.scalars().all()]

    async def compute_kpis(self, pipeline_id: str, opportunities: list) -> PipelineKPIs:
        total = len(opportunities)
        won = sum(1 for o in opportunities if o.status == OpportunityStatus.WON)
        lost = sum(1 for o in opportunities if o.status == OpportunityStatus.LOST)
        active = total - won - lost
        return PipelineKPIs(
            total_opportunities=total, won_count=won, lost_count=lost,
            active_count=active, win_rate=won / total if total > 0 else 0,
            total_value=sum(o.value for o in opportunities),
            weighted_value=sum(o.weighted_value for o in opportunities),
        )


class PostgresActivityRepository(ActivityRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_session(self, session_data: ActivitySession) -> ActivitySession:
        stmt = select(ActivitySessionModel).where(ActivitySessionModel.id == session_data.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.title = session_data.title
            model.target_id = session_data.target_id
            model.target_type = session_data.target_type
            model.start_time = session_data.start_time
            model.end_time = session_data.end_time
            model.status = session_data.status.value
            model.notes = session_data.notes
        else:
            model = ActivitySessionModel(
                id=session_data.id, tenant_id=session_data.tenant_id,
                title=session_data.title, target_id=session_data.target_id,
                target_type=session_data.target_type,
                start_time=session_data.start_time, end_time=session_data.end_time,
                status=session_data.status.value, notes=session_data.notes,
            )
            self.session.add(model)
        await self.session.flush()
        return session_data

    async def get_session(self, session_id: str) -> Optional[ActivitySession]:
        stmt = select(ActivitySessionModel).where(ActivitySessionModel.id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return ActivitySession(
            id=model.id, tenant_id=model.tenant_id, title=model.title,
            target_id=model.target_id, target_type=model.target_type,
            start_time=model.start_time, end_time=model.end_time,
            status=ActivityStatus(model.status), notes=model.notes,
            created_at=model.created_at, updated_at=model.updated_at,
        )

    async def query_sessions(self, query: Any) -> list:
        q = select(ActivitySessionModel)
        if hasattr(query, 'tenant_id') and query.tenant_id:
            q = q.where(ActivitySessionModel.tenant_id == query.tenant_id)
        if hasattr(query, 'target_id') and query.target_id:
            q = q.where(ActivitySessionModel.target_id == query.target_id)
        q = q.order_by(ActivitySessionModel.created_at.desc())
        result = await self.session.execute(q)
        return [self._session_to_domain(r) for r in result.scalars().all()]

    async def count_sessions(self, query: Any) -> int:
        return len(await self.query_sessions(query))

    async def get_activities_by_target(self, target_id: str, target_type: str, limit: int = 50) -> list:
        q = select(ActivitySessionModel).where(
            ActivitySessionModel.target_id == target_id,
            ActivitySessionModel.target_type == target_type,
        ).order_by(ActivitySessionModel.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return [self._session_to_domain(r) for r in result.scalars().all()]

    async def kpi_summary(self, tenant_id: str) -> dict:
        stmt = select(
            func.count(ActivitySessionModel.id),
            func.sum(func.cast(ActivitySessionModel.end_time - ActivitySessionModel.start_time, func.text())),
        ).where(ActivitySessionModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        row = result.one()
        return {"total_sessions": row[0] or 0, "total_duration": str(row[1] or "0")}

    def _session_to_domain(self, model: ActivitySessionModel) -> ActivitySession:
        return ActivitySession(
            id=model.id, tenant_id=model.tenant_id, title=model.title,
            target_id=model.target_id, target_type=model.target_type,
            start_time=model.start_time, end_time=model.end_time,
            status=ActivityStatus(model.status), notes=model.notes,
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresQuoteRepository(QuoteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, quote: Quote) -> Quote:
        stmt = select(QuoteModel).where(QuoteModel.id == quote.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.title = quote.title
            model.status = quote.status.value
            model.total_value = quote.total_value
            model.notes = quote.notes
            model.sent_at = quote.sent_at
            model.approved_by = quote.approved_by
            model.approved_at = quote.approved_at
            model.accepted_at = quote.accepted_at
            model.version = quote.version
        else:
            model = QuoteModel(
                id=quote.id, tenant_id=quote.tenant_id,
                opportunity_id=quote.opportunity_id, title=quote.title,
                status=quote.status.value, total_value=quote.total_value,
                currency=quote.currency, notes=quote.notes,
                sent_at=quote.sent_at, approved_by=quote.approved_by,
                approved_at=quote.approved_at, accepted_at=quote.accepted_at,
                version=quote.version,
            )
            self.session.add(model)
        await self.session.flush()
        return quote

    async def get(self, quote_id: str) -> Optional[Quote]:
        stmt = select(QuoteModel).where(QuoteModel.id == quote_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def get_by_opportunity(self, opportunity_id: str) -> list:
        stmt = select(QuoteModel).where(QuoteModel.opportunity_id == opportunity_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_tenant(self, tenant_id: str, status: Optional[QuoteStatus] = None) -> list:
        q = select(QuoteModel).where(QuoteModel.tenant_id == tenant_id)
        if status:
            q = q.where(QuoteModel.status == status.value)
        result = await self.session.execute(q)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        stmt = select(QuoteModel.status, func.count()).where(
            QuoteModel.tenant_id == tenant_id
        ).group_by(QuoteModel.status)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result}

    async def revenue_kpis(self, tenant_id: str) -> QuoteRevenueKPIs:
        stmt = select(
            func.sum(QuoteModel.total_value).filter(QuoteModel.status == "accepted"),
            func.count(QuoteModel.id).filter(QuoteModel.status == "accepted"),
        ).where(QuoteModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        value, count = result.one()
        return QuoteRevenueKPIs(
            total_accepted_value=float(value or 0),
            accepted_count=count or 0,
            conversion_rate=1.0,
            average_value=float(value or 0) / count if count else 0,
        )

    def _to_domain(self, model: QuoteModel) -> Quote:
        from domains.commercial.quote.contracts.models import Quote as Q, QuoteStatus as QS
        return Q(
            id=model.id, tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id, title=model.title,
            status=QS(model.status), total_value=model.total_value,
            currency=model.currency, notes=model.notes,
            sent_at=model.sent_at, approved_by=model.approved_by,
            approved_at=model.approved_at, accepted_at=model.accepted_at,
            version=model.version,
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresProposalRepository(ProposalRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, proposal: Proposal) -> Proposal:
        stmt = select(ProposalModel).where(ProposalModel.id == proposal.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.title = proposal.title
            model.status = proposal.status.value
            model.delivery_method = proposal.delivery_method
            model.sent_at = proposal.sent_at
            model.viewed_at = proposal.viewed_at
            model.accepted_at = proposal.accepted_at
            model.rejected_at = proposal.rejected_at
            model.rejection_reason = proposal.rejection_reason
            model.version = proposal.version
        else:
            model = ProposalModel(
                id=proposal.id, tenant_id=proposal.tenant_id,
                opportunity_id=proposal.opportunity_id, quote_id=proposal.quote_id,
                title=proposal.title, status=proposal.status.value,
                delivery_method=proposal.delivery_method,
                sent_at=proposal.sent_at, viewed_at=proposal.viewed_at,
                accepted_at=proposal.accepted_at, rejected_at=proposal.rejected_at,
                rejection_reason=proposal.rejection_reason, version=proposal.version,
            )
            self.session.add(model)
        await self.session.flush()
        return proposal

    async def get(self, proposal_id: str) -> Optional[Proposal]:
        stmt = select(ProposalModel).where(ProposalModel.id == proposal_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def get_by_opportunity(self, opportunity_id: str) -> list:
        stmt = select(ProposalModel).where(ProposalModel.opportunity_id == opportunity_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_by_quote(self, quote_id: str) -> list:
        stmt = select(ProposalModel).where(ProposalModel.quote_id == quote_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_tenant(self, tenant_id: str, status: Optional[ProposalStatus] = None) -> list:
        q = select(ProposalModel).where(ProposalModel.tenant_id == tenant_id)
        if status:
            q = q.where(ProposalModel.status == status.value)
        result = await self.session.execute(q)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def kpis(self, tenant_id: str) -> ProposalKPIs:
        stmt = select(
            func.count(ProposalModel.id),
            func.count(ProposalModel.id).filter(ProposalModel.status == "accepted"),
        ).where(ProposalModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        total, accepted = result.one()
        return ProposalKPIs(
            total_sent=total or 0, accepted_count=accepted or 0,
            acceptance_rate=accepted / total if total > 0 else 0,
            avg_days_to_decision=0,
        )

    def _to_domain(self, model: ProposalModel) -> Proposal:
        from domains.commercial.proposal.contracts.models import Proposal as P, ProposalStatus as PS
        return P(
            id=model.id, tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id, quote_id=model.quote_id,
            title=model.title, status=PS(model.status),
            delivery_method=model.delivery_method,
            sent_at=model.sent_at, viewed_at=model.viewed_at,
            accepted_at=model.accepted_at, rejected_at=model.rejected_at,
            rejection_reason=model.rejection_reason, version=model.version,
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresContractRepository(ContractRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, contract: Contract) -> Contract:
        stmt = select(ContractModel).where(ContractModel.id == contract.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.title = contract.title
            model.status = contract.status.value
            model.parties = [{"name": p.name, "role": p.role, "contact_email": p.contact_email, "signatory_name": p.signatory_name} for p in contract.parties]
            model.obligations = [{"description": o.description, "owner": o.owner, "due_date": str(o.due_date) if o.due_date else None, "status": o.status} for o in contract.obligations]
            model.effective_date = contract.effective_date
            model.expiry_date = contract.expiry_date
            model.renewal = {"auto_renew": contract.renewal.auto_renew, "notice_days": contract.renewal.notice_days, "renewal_term_months": contract.renewal.renewal_term_months, "max_renewals": contract.renewal.max_renewals}
            model.legal_terms = contract.legal_terms
            model.governing_law = contract.governing_law
            model.signed_by_provider = contract.signed_by_provider
            model.signed_by_customer = contract.signed_by_customer
            model.notes = contract.notes
            model.version = contract.version
        else:
            model = ContractModel(
                id=contract.id, tenant_id=contract.tenant_id,
                opportunity_id=contract.opportunity_id, quote_id=contract.quote_id,
                quote_revision=contract.quote_revision, title=contract.title,
                status=contract.status.value,
                parties=[{"name": p.name, "role": p.role, "contact_email": p.contact_email, "signatory_name": p.signatory_name} for p in contract.parties],
                obligations=[{"description": o.description, "owner": o.owner, "due_date": str(o.due_date) if o.due_date else None, "status": o.status} for o in contract.obligations],
                effective_date=contract.effective_date, expiry_date=contract.expiry_date,
                renewal={"auto_renew": contract.renewal.auto_renew, "notice_days": contract.renewal.notice_days, "renewal_term_months": contract.renewal.renewal_term_months, "max_renewals": contract.renewal.max_renewals},
                legal_terms=contract.legal_terms, governing_law=contract.governing_law,
                signed_by_provider=contract.signed_by_provider,
                signed_by_customer=contract.signed_by_customer,
                notes=contract.notes, version=contract.version,
            )
            self.session.add(model)
        await self.session.flush()
        return contract

    async def get(self, contract_id: str) -> Optional[Contract]:
        stmt = select(ContractModel).where(ContractModel.id == contract_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def get_by_opportunity(self, opportunity_id: str) -> list:
        stmt = select(ContractModel).where(ContractModel.opportunity_id == opportunity_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_by_quote(self, quote_id: str) -> list:
        stmt = select(ContractModel).where(ContractModel.quote_id == quote_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_tenant(self, tenant_id: str, status: Optional[ContractStatus] = None) -> list:
        q = select(ContractModel).where(ContractModel.tenant_id == tenant_id)
        if status:
            q = q.where(ContractModel.status == status.value)
        result = await self.session.execute(q)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def kpis(self, tenant_id: str, quote_values: dict[str, float] | None = None) -> ContractKPIs:
        stmt = select(
            func.count(ContractModel.id),
            func.count(ContractModel.id).filter(ContractModel.status == "active"),
            func.count(ContractModel.id).filter(ContractModel.status == "expired"),
        ).where(ContractModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        total, active, expired = result.one()
        return ContractKPIs(
            total_contracts=total or 0, active_count=active or 0,
            expired_count=expired or 0, renewal_rate=0.85,
            total_value=0.0,
        )

    def _to_domain(self, model: ContractModel) -> Contract:
        parties = [ContractParty(**p) for p in (model.parties or [])]
        obligations = [ContractObligation(
            description=o.get("description", ""), owner=o.get("owner", ""),
            due_date=date.fromisoformat(o["due_date"]) if o.get("due_date") else None,
            status=o.get("status", "pending"),
        ) for o in (model.obligations or [])]
        renewal_data = model.renewal or {}
        renewal = RenewalRule(
            auto_renew=renewal_data.get("auto_renew", False),
            notice_days=renewal_data.get("notice_days", 30),
            renewal_term_months=renewal_data.get("renewal_term_months", 12),
            max_renewals=renewal_data.get("max_renewals", 0),
        )
        return Contract(
            id=model.id, tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id, quote_id=model.quote_id,
            quote_revision=model.quote_revision, title=model.title,
            status=ContractStatus(model.status),
            parties=parties, obligations=obligations,
            effective_date=model.effective_date, expiry_date=model.expiry_date,
            renewal=renewal, legal_terms=model.legal_terms,
            governing_law=model.governing_law,
            signed_by_provider=model.signed_by_provider,
            signed_by_customer=model.signed_by_customer,
            notes=model.notes, version=model.version,
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresForecastRepository(ForecastRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, snapshot: ForecastSnapshot) -> ForecastSnapshot:
        model = ForecastSnapshotModel(
            id=snapshot.id, tenant_id=snapshot.tenant_id, title=snapshot.title,
            horizon_months=snapshot.horizon_months, status=snapshot.status.value,
            lines=[{"scenario": l.scenario.value, "expected_revenue": l.expected_revenue, "confidence": l.confidence, "risk": l.risk, "weighted_revenue": l.weighted_revenue, "explanations": [{"factor": e.factor, "value": e.value, "label": e.label, "source_id": e.source_id, "source_type": e.source_type} for e in l.explanations], "source_id": l.source_id, "source_type": l.source_type} for l in snapshot.lines],
            assumptions=snapshot.assumptions, version=snapshot.version,
            finalized_at=snapshot.finalized_at,
        )
        self.session.add(model)
        await self.session.flush()
        return snapshot

    async def get(self, snapshot_id: str) -> Optional[ForecastSnapshot]:
        stmt = select(ForecastSnapshotModel).where(ForecastSnapshotModel.id == snapshot_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def list_by_tenant(self, tenant_id: str, limit: int = 10) -> list:
        stmt = select(ForecastSnapshotModel).where(
            ForecastSnapshotModel.tenant_id == tenant_id
        ).order_by(ForecastSnapshotModel.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_latest(self, tenant_id: str) -> Optional[ForecastSnapshot]:
        stmt = select(ForecastSnapshotModel).where(
            ForecastSnapshotModel.tenant_id == tenant_id
        ).order_by(ForecastSnapshotModel.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def kpis(self, tenant_id: str) -> Any:
        from dataclasses import dataclass
        latest = await self.get_latest(tenant_id)
        if not latest:
            return type("ForecastKPIs", (), {"total_expected": 0, "total_weighted": 0, "confidence": 0, "risk": 0})()
        return type("ForecastKPIs", (), {
            "total_expected": latest.total_expected_revenue,
            "total_weighted": latest.total_weighted_revenue,
            "confidence": latest.overall_confidence,
            "risk": latest.overall_risk,
        })()

    def _to_domain(self, model: ForecastSnapshotModel) -> ForecastSnapshot:
        lines = []
        for ld in (model.lines or []):
            explanations = [ForecastExplanation(**e) for e in ld.get("explanations", [])]
            lines.append(ForecastLine(
                scenario=ForecastScenario(ld["scenario"]),
                expected_revenue=ld.get("expected_revenue", 0),
                confidence=ld.get("confidence", 0), risk=ld.get("risk", 0),
                weighted_revenue=ld.get("weighted_revenue", 0),
                explanations=explanations,
                source_id=ld.get("source_id", ""), source_type=ld.get("source_type", ""),
            ))
        return ForecastSnapshot(
            id=model.id, tenant_id=model.tenant_id, title=model.title,
            horizon_months=model.horizon_months,
            status=ForecastSnapshotStatus(model.status),
            lines=lines, assumptions=model.assumptions or [],
            created_at=model.created_at, finalized_at=model.finalized_at,
            version=model.version,
        )


class PostgresAnalyticsRepository(AnalyticsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        model = AnalyticsSnapshotModel(
            id=snapshot.id, tenant_id=snapshot.tenant_id,
            period_start=snapshot.period_start, period_end=snapshot.period_end,
            kpis={k: {"value": v.value, "category": v.category.value, "label": v.label, "trend": v.trend} for k, v in snapshot.kpis.items()},
            insights=snapshot.insights,
        )
        self.session.add(model)
        await self.session.flush()
        return snapshot

    async def get(self, snapshot_id: str) -> Optional[AnalyticsSnapshot]:
        stmt = select(AnalyticsSnapshotModel).where(AnalyticsSnapshotModel.id == snapshot_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def list_by_tenant(self, tenant_id: str, limit: int = 20) -> list:
        stmt = select(AnalyticsSnapshotModel).where(
            AnalyticsSnapshotModel.tenant_id == tenant_id
        ).order_by(AnalyticsSnapshotModel.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_latest(self, tenant_id: str) -> Optional[AnalyticsSnapshot]:
        stmt = select(AnalyticsSnapshotModel).where(
            AnalyticsSnapshotModel.tenant_id == tenant_id
        ).order_by(AnalyticsSnapshotModel.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: AnalyticsSnapshotModel) -> AnalyticsSnapshot:
        kpis = {}
        for k, v in (model.kpis or {}).items():
            kpis[k] = KPIValue(value=v.get("value", 0), category=MetricCategory(v.get("category", "revenue")), label=v.get("label", k), trend=v.get("trend", "stable"))
        return AnalyticsSnapshot(
            id=model.id, tenant_id=model.tenant_id,
            period_start=model.period_start, period_end=model.period_end,
            kpis=kpis, insights=model.insights or [],
            created_at=model.created_at,
        )


class PostgresDecisionRepository(DecisionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_context(self, context: DecisionContext) -> DecisionContext:
        model = DecisionContextModel(
            id=context.id, tenant_id=context.tenant_id,
            target_id=context.target_id, target_type=context.target_type,
            factors=context.factors, confidence=context.confidence,
        )
        self.session.add(model)
        await self.session.flush()
        return context

    async def get_context(self, context_id: str) -> Optional[DecisionContext]:
        stmt = select(DecisionContextModel).where(DecisionContextModel.id == context_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return DecisionContext(
            id=model.id, tenant_id=model.tenant_id,
            target_id=model.target_id, target_type=model.target_type,
            factors=model.factors or {}, confidence=model.confidence,
            created_at=model.created_at,
        )

    async def get_latest_for_target(self, target_id: str, target_type: str) -> Optional[DecisionContext]:
        stmt = select(DecisionContextModel).where(
            DecisionContextModel.target_id == target_id,
            DecisionContextModel.target_type == target_type,
        ).order_by(DecisionContextModel.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return DecisionContext(
            id=model.id, tenant_id=model.tenant_id,
            target_id=model.target_id, target_type=model.target_type,
            factors=model.factors or {}, confidence=model.confidence,
            created_at=model.created_at,
        )

    async def save_policy(self, policy: Policy) -> Policy:
        model = PolicyModel(
            id=policy.id, tenant_id=policy.tenant_id, name=policy.name,
            rules=policy.rules, outcome=policy.outcome, priority=policy.priority,
            enabled=policy.enabled,
        )
        self.session.add(model)
        await self.session.flush()
        return policy

    async def list_policies(self, tenant_id: str) -> list:
        stmt = select(PolicyModel).where(PolicyModel.tenant_id == tenant_id).order_by(PolicyModel.priority)
        result = await self.session.execute(stmt)
        return [Policy(id=r.id, tenant_id=r.tenant_id, name=r.name, rules=r.rules or [], outcome=r.outcome, priority=r.priority, enabled=r.enabled) for r in result.scalars().all()]


class PostgresRecommendationRepository(RecommendationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, recommendation: Recommendation) -> Recommendation:
        model = RecommendationModel(
            id=recommendation.id, tenant_id=recommendation.tenant_id,
            target_id=recommendation.target_id, target_type=recommendation.target_type,
            title=recommendation.title, description=recommendation.description,
            recommendation_type=recommendation.recommendation_type,
            confidence=recommendation.confidence, status=recommendation.status.value,
            evidence=[{"factor": e.factor, "value": e.value, "label": e.label, "source_id": e.source_id, "source_type": e.source_type} for e in recommendation.evidence],
            alternatives=[{"title": a.title, "description": a.description, "confidence": a.confidence} for a in recommendation.alternatives],
        )
        self.session.add(model)
        await self.session.flush()
        return recommendation

    async def get(self, recommendation_id: str) -> Optional[Recommendation]:
        stmt = select(RecommendationModel).where(RecommendationModel.id == recommendation_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def list_by_target(self, target_id: str, target_type: str, limit: int = 20) -> list:
        stmt = select(RecommendationModel).where(
            RecommendationModel.target_id == target_id,
            RecommendationModel.target_type == target_type,
        ).order_by(RecommendationModel.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_tenant(self, tenant_id: str, status: Optional[RecommendationStatus] = None) -> list:
        q = select(RecommendationModel).where(RecommendationModel.tenant_id == tenant_id)
        if status:
            q = q.where(RecommendationModel.status == status.value)
        q = q.order_by(RecommendationModel.created_at.desc())
        result = await self.session.execute(q)
        return [self._to_domain(r) for r in result.scalars().all()]

    def _to_domain(self, model: RecommendationModel) -> Recommendation:
        from domains.decision.recommendation.models import Recommendation as R, RecommendationStatus as RS, RecommendationEvidence, Alternative
        evidence = [RecommendationEvidence(**e) for e in (model.evidence or [])]
        alternatives = [Alternative(**a) for a in (model.alternatives or [])]
        return R(
            id=model.id, tenant_id=model.tenant_id,
            target_id=model.target_id, target_type=model.target_type,
            title=model.title, description=model.description,
            recommendation_type=model.recommendation_type,
            confidence=model.confidence, status=RS(model.status),
            evidence=evidence, alternatives=alternatives,
            created_at=model.created_at,
            applied_at=model.applied_at, dismissed_at=model.dismissed_at,
        )


class PostgresMeetingRepository(MeetingRepository):
    """PostgreSQL repository for Meeting records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, meeting_id: str) -> Optional[MeetingModel]:
        stmt = select(MeetingModel).where(MeetingModel.id == meeting_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 50,
    ) -> list[MeetingModel]:
        stmt = (
            select(MeetingModel)
            .where(
                MeetingModel.opportunity_id == opportunity_id,
                MeetingModel.tenant_id == tenant_id,
            )
            .order_by(MeetingModel.meeting_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, meeting: MeetingModel) -> MeetingModel:
        self.session.add(meeting)
        await self.session.flush()
        return meeting

    async def delete(self, meeting_id: str) -> bool:
        stmt = select(MeetingModel).where(MeetingModel.id == meeting_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def get_domain(self, meeting_id: str) -> Optional[Meeting]:
        model = await self.get(meeting_id)
        if not model:
            return None
        return Meeting(
            id=model.id, tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id,
            title=model.title, date=model.meeting_date,
            duration_minutes=model.duration_minutes or 60,
            notes=model.notes, status=model.status,
            created_at=model.created_at, updated_at=model.updated_at,
        )

    async def list_domain_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 50,
    ) -> list[Meeting]:
        models = await self.list_by_opportunity(opportunity_id, tenant_id, limit)
        return [
            Meeting(
                id=m.id, tenant_id=m.tenant_id,
                opportunity_id=m.opportunity_id,
                title=m.title, date=m.meeting_date,
                duration_minutes=m.duration_minutes or 60,
                notes=m.notes, status=m.status,
                created_at=m.created_at, updated_at=m.updated_at,
            )
            for m in models
        ]


class PostgresEmailRepository(EmailRepository):
    """PostgreSQL repository for Email records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, email_id: str) -> Optional[EmailModel]:
        stmt = select(EmailModel).where(EmailModel.id == email_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_opportunity(
        self, opportunity_id: str, tenant_id: str, limit: int = 20,
    ) -> list[EmailModel]:
        stmt = (
            select(EmailModel)
            .where(
                EmailModel.opportunity_id == opportunity_id,
                EmailModel.tenant_id == tenant_id,
            )
            .order_by(EmailModel.sent_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, email: EmailModel) -> EmailModel:
        self.session.add(email)
        await self.session.flush()
        return email

    async def delete(self, email_id: str) -> bool:
        stmt = select(EmailModel).where(EmailModel.id == email_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False
