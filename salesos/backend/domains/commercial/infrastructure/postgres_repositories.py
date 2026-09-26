"""PostgreSQL repository implementations for all commercial domains."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, cast, delete, func, or_, select, text
from sqlalchemy.dialects.postgresql import JSONB
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
from domains.commercial.pipeline.contracts.models import (
    PipelineDefinition as PipelineDef,
    StageDefinition,
    StageEntry,
)
from domains.commercial.pipeline.contracts.repository import PipelineKPIs, PipelineRepository
from domains.commercial.proposal.contracts.models import Proposal, ProposalStatus
from domains.commercial.proposal.contracts.repository import ProposalKPIs, ProposalRepository
from domains.commercial.quote.contracts.models import ApprovalState, Quote, QuoteLine, QuoteStatus
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

from domains.commercial.opportunity.contracts.opportunity_contact_repository import (
    OpportunityContact,
    OpportunityContactQuery,
    OpportunityContactRepository,
    OpportunityContactResult,
)

from .models import (
    ActivityModel, ActivitySessionModel, AnalyticsSnapshotModel,
    ContractModel, DecisionContextModel, EmailModel, ForecastSnapshotModel,
    MeetingModel, OpportunityContactModel, OpportunityModel,
    PipelineDefinitionModel, PolicyModel, ProposalModel, QuoteLineModel,
    QuoteModel, QuotaModel, QuotaSnapshotModel, RecommendationModel, ReviewModel, StageEntryModel,
    TerritoryModel,
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
            from sqlalchemy import delete as sa_delete
            await self.session.execute(
                sa_delete(OpportunityContactModel).where(
                    OpportunityContactModel.opportunity_id == opportunity_id
                )
            )
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
        stages = [StageDefinition(**s) for s in (model.stages or [])]
        return PipelineDef(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            # The legacy table stores one display name; keep the Arabic name
            # valid until the schema gains a dedicated name_ar column.
            name_ar=model.name,
            stages=stages,
        )

    async def list_definitions(self, tenant_id: str) -> list:
        stmt = select(PipelineDefinitionModel).where(PipelineDefinitionModel.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return [
            PipelineDef(
                id=r.id,
                tenant_id=r.tenant_id,
                name=r.name,
                name_ar=r.name,
                stages=[StageDefinition(**s) for s in (r.stages or [])],
            )
            for r in result.scalars().all()
        ]

    @staticmethod
    def _duration_hours(entry: StageEntry) -> float | None:
        if not entry.exited_at:
            return None
        return (entry.exited_at - entry.entered_at).total_seconds() / 3600

    async def save_stage_entry(self, entry: StageEntry) -> StageEntry:
        """Upsert by id: `enter_stage()` saves the same `prev` entry object
        twice (once to close it, once already persisted when re-entered),
        so a plain INSERT would violate the primary key on the second call.
        """
        existing = await self.session.get(StageEntryModel, entry.id)
        if existing is not None:
            existing.exited_at = entry.exited_at
            existing.duration_hours = self._duration_hours(entry)
        else:
            model = StageEntryModel(
                id=entry.id or str(uuid.uuid4()),
                tenant_id=entry.tenant_id,
                opportunity_id=entry.opportunity_id,
                pipeline_id=entry.pipeline_id,
                from_stage=entry.from_stage,
                to_stage=entry.stage_name,
                entered_at=entry.entered_at or datetime.now(timezone.utc),
                exited_at=entry.exited_at,
                duration_hours=self._duration_hours(entry),
            )
            self.session.add(model)
        await self.session.flush()
        return entry

    @staticmethod
    def _to_contract(model: StageEntryModel) -> StageEntry:
        return StageEntry(
            id=model.id, opportunity_id=model.opportunity_id, pipeline_id=model.pipeline_id,
            stage_name=model.to_stage, from_stage=model.from_stage, tenant_id=model.tenant_id,
            entered_at=model.entered_at, exited_at=model.exited_at,
        )

    async def get_active_stage_entry(self, opportunity_id: str) -> Optional[StageEntry]:
        stmt = select(StageEntryModel).where(
            StageEntryModel.opportunity_id == opportunity_id,
            StageEntryModel.exited_at.is_(None),
        ).order_by(StageEntryModel.entered_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_contract(model)

    async def get_stage_history(self, opportunity_id: str) -> list:
        stmt = select(StageEntryModel).where(
            StageEntryModel.opportunity_id == opportunity_id
        ).order_by(StageEntryModel.entered_at.asc())
        result = await self.session.execute(stmt)
        return [self._to_contract(r) for r in result.scalars().all()]

    async def compute_kpis(self, pipeline_id: str, opportunities: list) -> PipelineKPIs:
        """Compute the same KPI contract as the in-memory repository.

        The PostgreSQL adapter previously constructed an older, incompatible
        ``PipelineKPIs`` shape (``won_count``, ``total_value`` …).  Keep the
        persistence adapter contract-aligned so API reads work for both empty
        and populated pipelines.
        """
        pipeline = await self.get_definition(pipeline_id)
        if not pipeline:
            return PipelineKPIs(pipeline_id=pipeline_id)

        total = len(opportunities)
        pipeline_value = sum(getattr(o, "value", 0) for o in opportunities)
        weighted = sum(
            getattr(o, "weighted_value", None)
            if getattr(o, "weighted_value", None) is not None
            else getattr(o, "value", 0) * getattr(o, "probability", 0)
            for o in opportunities
        )

        def _status_value(opportunity: object) -> str:
            status = getattr(opportunity, "status", None)
            return getattr(status, "value", status) or ""

        won = sum(1 for o in opportunities if _status_value(o) == "won")
        lost = sum(1 for o in opportunities if _status_value(o) == "lost")
        closed = won + lost

        stage_counts: dict[str, int] = {}
        stage_values: dict[str, float] = {}
        for opportunity in opportunities:
            stage = getattr(opportunity, "stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            stage_values[stage] = stage_values.get(stage, 0.0) + getattr(opportunity, "value", 0)

        return PipelineKPIs(
            pipeline_id=pipeline_id,
            total_opportunities=total,
            pipeline_value=pipeline_value,
            weighted_pipeline=weighted,
            stage_counts=stage_counts,
            stage_values=stage_values,
            win_rate=round(won / closed, 2) if closed else 0.0,
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
        from sqlalchemy import func as sa_func
        q = select(sa_func.count(ActivitySessionModel.id))
        if hasattr(query, 'tenant_id') and query.tenant_id:
            q = q.where(ActivitySessionModel.tenant_id == query.tenant_id)
        if hasattr(query, 'target_id') and query.target_id:
            q = q.where(ActivitySessionModel.target_id == query.target_id)
        result = await self.session.execute(q)
        return result.scalar() or 0

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
        model = await self.session.get(QuoteModel, quote.id)
        if model:
            if model.status != quote.status.value:
                if quote.status == QuoteStatus.SENT and not model.sent_at:
                    model.sent_at = quote.updated_at
                if quote.status == QuoteStatus.ACCEPTED and not model.accepted_at:
                    model.accepted_at = quote.updated_at
            model.title = quote.title
            model.status = quote.status.value
            model.total_value = quote.grand_total
            model.notes = quote.notes
            model.approved_by = quote.approval.approved_by
            model.approved_at = quote.approval.approved_at
            model.version = quote.version
        else:
            model = QuoteModel(
                id=quote.id, tenant_id=quote.tenant_id,
                opportunity_id=quote.opportunity_id, title=quote.title,
                status=quote.status.value, total_value=quote.grand_total,
                currency=quote.currency, notes=quote.notes,
                sent_at=quote.updated_at if quote.status == QuoteStatus.SENT else None,
                approved_by=quote.approval.approved_by,
                approved_at=quote.approval.approved_at,
                accepted_at=quote.updated_at if quote.status == QuoteStatus.ACCEPTED else None,
                version=quote.version,
            )
            self.session.add(model)
        await self.session.flush()
        await self._sync_lines(quote)
        return quote

    async def _sync_lines(self, quote: Quote) -> None:
        """Persist `quote.lines` into `commercial_quote_lines`.

        The model only has description/quantity/unit_price/total columns —
        no discount_percent/tax_percent/description_ar/product_code/notes —
        so those per-line fields do not round-trip through this schema (a
        pre-existing persistence-schema limitation, not introduced here;
        see report 120 for the sibling gap on StageEntry.exit_reason).
        """
        existing_ids = {
            row[0] for row in (
                await self.session.execute(
                    select(QuoteLineModel.id).where(QuoteLineModel.quote_id == quote.id)
                )
            ).all()
        }
        current_ids = {line.id for line in quote.lines}
        stale_ids = existing_ids - current_ids
        if stale_ids:
            await self.session.execute(
                delete(QuoteLineModel).where(QuoteLineModel.id.in_(stale_ids))
            )
        for line in quote.lines:
            line_model = await self.session.get(QuoteLineModel, line.id)
            if line_model:
                line_model.description = line.description
                line_model.quantity = line.quantity
                line_model.unit_price = line.unit_price
                line_model.total = line.grand_total
            else:
                self.session.add(QuoteLineModel(
                    id=line.id, quote_id=quote.id, description=line.description,
                    quantity=line.quantity, unit_price=line.unit_price,
                    total=line.grand_total,
                ))
        await self.session.flush()

    async def get(self, quote_id: str) -> Optional[Quote]:
        stmt = select(QuoteModel).where(QuoteModel.id == quote_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return await self._to_domain(model)

    async def get_by_opportunity(self, opportunity_id: str) -> list:
        stmt = select(QuoteModel).where(QuoteModel.opportunity_id == opportunity_id)
        result = await self.session.execute(stmt)
        return [await self._to_domain(r) for r in result.scalars().all()]

    async def list_by_tenant(self, tenant_id: str, status: Optional[QuoteStatus] = None) -> list:
        q = select(QuoteModel).where(QuoteModel.tenant_id == tenant_id)
        if status:
            q = q.where(QuoteModel.status == status.value)
        result = await self.session.execute(q)
        return [await self._to_domain(r) for r in result.scalars().all()]

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        stmt = select(QuoteModel.status, func.count()).where(
            QuoteModel.tenant_id == tenant_id
        ).group_by(QuoteModel.status)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result}

    async def revenue_kpis(self, tenant_id: str) -> QuoteRevenueKPIs:
        """Mirrors the in-memory reference's formulas (engine/in_memory_repo.py)
        so both repository implementations stay contract-aligned."""
        quotes = await self.list_by_tenant(tenant_id)
        total = len(quotes)
        accepted = sum(1 for q in quotes if q.status == QuoteStatus.ACCEPTED)
        rejected = sum(1 for q in quotes if q.status == QuoteStatus.REJECTED)
        expired = sum(1 for q in quotes if q.status == QuoteStatus.EXPIRED)
        submitted_for_approval = sum(1 for q in quotes if q.approval.is_approved)
        approved = sum(1 for q in quotes if q.status == QuoteStatus.APPROVED)
        total_value = sum(q.grand_total for q in quotes)
        total_discount = sum(q.total_discount for q in quotes)
        open_value = sum(q.grand_total for q in quotes if q.status == QuoteStatus.DRAFT)
        return QuoteRevenueKPIs(
            total_quote_value=total_value,
            total_discount_amount=total_discount,
            average_discount_percent=round(sum(q.discount_percent for q in quotes) / total, 2) if total > 0 else 0.0,
            approval_rate=round(approved / submitted_for_approval, 2) if submitted_for_approval > 0 else 0.0,
            acceptance_rate=round(accepted / (accepted + rejected), 2) if (accepted + rejected) > 0 else 0.0,
            quote_to_win_conversion=round(accepted / total, 2) if total > 0 else 0.0,
            open_pipeline_value=open_value,
            total_quotes=total,
            accepted_quotes=accepted,
            rejected_quotes=rejected,
            expired_quotes=expired,
        )

    async def _to_domain(self, model: QuoteModel) -> Quote:
        lines_result = await self.session.execute(
            select(QuoteLineModel).where(QuoteLineModel.quote_id == model.id)
        )
        lines = [
            QuoteLine(
                id=r.id, description=r.description,
                quantity=int(r.quantity), unit_price=r.unit_price,
            )
            for r in lines_result.scalars().all()
        ]
        return Quote(
            id=model.id, tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id, title=model.title,
            status=QuoteStatus(model.status), lines=lines,
            approval=ApprovalState(approved_by=model.approved_by, approved_at=model.approved_at),
            currency=model.currency, notes=model.notes,
            version=model.version,
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresProposalRepository(ProposalRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, proposal: Proposal) -> Proposal:
        """`sections` (the proposal's actual content) has no schema home at
        all -- ProposalModel has no sections/content column of any kind --
        so update_section()'s mutations do not round-trip. A pre-existing
        gap, not introduced here; would need a new table/column + migration
        to close (see report 122).
        """
        stmt = select(ProposalModel).where(ProposalModel.id == proposal.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            if model.status != proposal.status.value:
                if proposal.status == ProposalStatus.DELIVERED and not model.sent_at:
                    model.sent_at = proposal.updated_at
                if proposal.status == ProposalStatus.REJECTED and not model.rejected_at:
                    model.rejected_at = proposal.updated_at
            model.title = proposal.title
            model.status = proposal.status.value
            model.delivery_method = proposal.delivery_method
            model.viewed_at = proposal.viewed_at
            model.accepted_at = proposal.accepted_at
            model.rejection_reason = proposal.rejection_reason
            model.version = proposal.version
        else:
            model = ProposalModel(
                id=proposal.id, tenant_id=proposal.tenant_id,
                opportunity_id=proposal.opportunity_id, quote_id=proposal.quote_id,
                title=proposal.title, status=proposal.status.value,
                delivery_method=proposal.delivery_method,
                sent_at=proposal.updated_at if proposal.status == ProposalStatus.DELIVERED else None,
                viewed_at=proposal.viewed_at,
                accepted_at=proposal.accepted_at,
                rejected_at=proposal.updated_at if proposal.status == ProposalStatus.REJECTED else None,
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
        """Mirrors the in-memory reference's formulas (engine/in_memory_repo.py)."""
        proposals = await self.list_by_tenant(tenant_id)
        total = len(proposals)
        delivered = sum(1 for p in proposals if p.is_delivered)
        accepted = sum(1 for p in proposals if p.status == ProposalStatus.ACCEPTED)
        cycle_hours = 0.0
        cycle_count = 0
        for p in proposals:
            if p.accepted_at and p.created_at:
                cycle_hours += (p.accepted_at - p.created_at).total_seconds() / 3600
                cycle_count += 1
        return ProposalKPIs(
            total_proposals=total,
            delivery_rate=round(delivered / total, 2) if total > 0 else 0.0,
            acceptance_rate=round(accepted / delivered, 2) if delivered > 0 else 0.0,
            average_cycle_hours=round(cycle_hours / cycle_count, 1) if cycle_count > 0 else 0.0,
            proposal_to_win_conversion=round(accepted / total, 2) if total > 0 else 0.0,
        )

    def _to_domain(self, model: ProposalModel) -> Proposal:
        return Proposal(
            id=model.id, tenant_id=model.tenant_id,
            opportunity_id=model.opportunity_id, quote_id=model.quote_id,
            title=model.title, status=ProposalStatus(model.status),
            delivery_method=model.delivery_method,
            viewed_at=model.viewed_at, accepted_at=model.accepted_at,
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
        """Mirrors the in-memory reference's formulas (contract/in_memory_repo.py).

        The previous implementation hardcoded `renewal_rate=0.85` and
        `total_contract_value=0.0` (both fake placeholders, ignoring the
        real `quote_values` argument entirely), never set `signed_rate`
        at all (silently always 0.0), and computed `expiring_soon` as the
        count of already-`expired` contracts rather than signed contracts
        whose `expiry_date` falls within the next 90 days. Unreached from
        any live router endpoint today (only a domain-level unit test
        calls `ContractService.kpis()`), fixed for contract alignment
        with the in-memory repository while this class was already being
        reviewed (report 123).
        """
        contracts = await self.list_by_tenant(tenant_id)
        total = len(contracts)
        active = sum(1 for c in contracts if c.status == ContractStatus.ACTIVE)
        signed = sum(1 for c in contracts if c.is_signed)
        renewed = sum(1 for c in contracts if c.status == ContractStatus.RENEWED)
        expiring_soon = sum(
            1 for c in contracts
            if c.is_signed and c.expiry_date and c.expiry_date <= date.today() + timedelta(days=90)
        )
        total_value = 0.0
        if quote_values:
            for c in contracts:
                total_value += quote_values.get(c.quote_id, 0.0)
        return ContractKPIs(
            total_contracts=total,
            active_contracts=active,
            signed_rate=round(signed / total, 2) if total > 0 else 0.0,
            renewal_rate=round(renewed / signed, 2) if signed > 0 else 0.0,
            expiring_soon=expiring_soon,
            total_contract_value=total_value,
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
        # ``AnalyticsSnapshot`` is the revenue analytics contract and stores
        # measured KPI values as a list.  The older commercial table keeps a
        # JSON object, so serialize the complete value record by KPI id rather
        # than reading the obsolete ``snapshot.kpis``/``insights`` fields.
        kpis = {
            value.kpi_id: {
                "value": value.value,
                "previous_value": value.previous_value,
                "change": value.change,
                "change_percent": value.change_percent,
                "dimension": value.dimension,
                "note": value.note,
            }
            for value in snapshot.values
        }
        model = AnalyticsSnapshotModel(
            id=snapshot.id, tenant_id=snapshot.tenant_id,
            period_start=snapshot.period_start.date(), period_end=snapshot.period_end.date(),
            kpis=kpis, insights=[],
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
        values = []
        for k, v in (model.kpis or {}).items():
            values.append(KPIValue(
                kpi_id=k,
                value=v.get("value", 0),
                previous_value=v.get("previous_value", 0),
                change=v.get("change", 0),
                change_percent=v.get("change_percent", 0),
                dimension=v.get("dimension", ""),
                note=v.get("note", ""),
            ))
        return AnalyticsSnapshot(
            id=model.id, tenant_id=model.tenant_id,
            period_start=datetime.combine(model.period_start, datetime.min.time(), tzinfo=timezone.utc),
            period_end=datetime.combine(model.period_end, datetime.min.time(), tzinfo=timezone.utc),
            values=values, generated_at=model.created_at,
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

    async def save_contexts(self, contexts: list[DecisionContext]) -> list[DecisionContext]:
        for ctx in contexts:
            model = DecisionContextModel(
                id=ctx.id, tenant_id=ctx.tenant_id,
                target_id=ctx.target_id, target_type=ctx.target_type,
                factors=ctx.factors, confidence=ctx.confidence,
            )
            self.session.add(model)
        await self.session.flush()
        return contexts

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


class PostgresOpportunityContactRepository(OpportunityContactRepository):
    """ADR-030: PostgreSQL implementation of OpportunityContactRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, oc: OpportunityContact) -> OpportunityContact:
        model = OpportunityContactModel(
            id=str(oc.id),
            tenant_id=str(oc.tenant_id),
            opportunity_id=oc.opportunity_id,
            contact_id=str(oc.contact_id),
            role=oc.role,
            is_primary=oc.is_primary,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get(self, oc_id: uuid.UUID) -> OpportunityContact | None:
        stmt = select(OpportunityContactModel).where(OpportunityContactModel.id == str(oc_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_opportunity(
        self, opportunity_id: str, tenant_id: str,
    ) -> list[OpportunityContact]:
        stmt = (
            select(OpportunityContactModel)
            .where(
                OpportunityContactModel.opportunity_id == opportunity_id,
                OpportunityContactModel.tenant_id == str(tenant_id),
            )
            .order_by(OpportunityContactModel.is_primary.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_contact(
        self, contact_id: uuid.UUID, tenant_id: str,
    ) -> list[OpportunityContact]:
        stmt = (
            select(OpportunityContactModel)
            .where(
                OpportunityContactModel.contact_id == str(contact_id),
                OpportunityContactModel.tenant_id == str(tenant_id),
            )
            .order_by(OpportunityContactModel.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def query(self, query: OpportunityContactQuery) -> OpportunityContactResult:
        conditions = [OpportunityContactModel.tenant_id == str(query.tenant_id)]
        if query.opportunity_id:
            conditions.append(OpportunityContactModel.opportunity_id == query.opportunity_id)
        if query.contact_id:
            conditions.append(OpportunityContactModel.contact_id == query.contact_id)

        count_stmt = select(func.count()).select_from(OpportunityContactModel).where(and_(*conditions))
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            select(OpportunityContactModel)
            .where(and_(*conditions))
            .order_by(OpportunityContactModel.is_primary.desc(), OpportunityContactModel.created_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        result = await self.session.execute(stmt)
        items = [self._to_domain(m) for m in result.scalars().all()]

        return OpportunityContactResult(items=items, total=total, page=query.page, page_size=query.page_size)

    async def delete(self, oc_id: uuid.UUID) -> bool:
        stmt = select(OpportunityContactModel).where(OpportunityContactModel.id == str(oc_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def delete_by_opportunity(self, opportunity_id: str) -> int:
        from sqlalchemy import delete as sa_delete
        result = await self.session.execute(
            sa_delete(OpportunityContactModel).where(
                OpportunityContactModel.opportunity_id == opportunity_id
            )
        )
        await self.session.flush()
        return result.rowcount

    def _to_domain(self, model: OpportunityContactModel) -> OpportunityContact:
        return OpportunityContact(
            id=uuid.UUID(str(model.id)),
            tenant_id=uuid.UUID(str(model.tenant_id)),
            opportunity_id=model.opportunity_id,
            contact_id=uuid.UUID(str(model.contact_id)),
            role=model.role,
            is_primary=model.is_primary,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


# ── P1-8: Review Repository ──

from domains.commercial.review.contracts.models import Review, ReviewDecision, ReviewStatus, ReviewType
from domains.commercial.review.contracts.repository import ReviewRepository


class PostgresReviewRepository(ReviewRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, review: Review) -> Review:
        stmt = select(ReviewModel).where(ReviewModel.id == review.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.review_type = review.review_type.value
            model.target_id = review.target_id
            model.target_type = review.target_type
            model.status = review.status.value
            model.assigned_to = review.assigned_to
            model.requested_by = review.requested_by
            model.decisions = [{"decision": d.decision, "decided_by": d.decided_by,
                               "decided_at": d.decided_at.isoformat(), "comments": d.comments}
                              for d in review.decisions]
            model.extra_metadata = review.metadata
            model.updated_at = datetime.now(timezone.utc)
        else:
            model = ReviewModel(
                id=review.id, tenant_id=review.tenant_id,
                review_type=review.review_type.value,
                target_id=review.target_id, target_type=review.target_type,
                status=review.status.value, assigned_to=review.assigned_to,
                requested_by=review.requested_by,
                decisions=[{"decision": d.decision, "decided_by": d.decided_by,
                            "decided_at": d.decided_at.isoformat(), "comments": d.comments}
                           for d in review.decisions],
                extra_metadata=review.metadata,
            )
            self.session.add(model)
        await self.session.flush()
        return review

    async def get(self, review_id: str) -> Review | None:
        stmt = select(ReviewModel).where(ReviewModel.id == review_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain(model)

    async def list_by_tenant(self, tenant_id: str, target_type: str | None = None) -> list[Review]:
        stmt = select(ReviewModel).where(ReviewModel.tenant_id == tenant_id)
        if target_type:
            stmt = stmt.where(ReviewModel.target_type == target_type)
        stmt = stmt.order_by(ReviewModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_pending(self, tenant_id: str, assigned_to: str | None = None) -> list[Review]:
        stmt = select(ReviewModel).where(
            ReviewModel.tenant_id == tenant_id,
            ReviewModel.status == "pending",
        )
        if assigned_to:
            stmt = stmt.where(ReviewModel.assigned_to == assigned_to)
        stmt = stmt.order_by(ReviewModel.created_at.asc())
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        stmt = select(ReviewModel.status, func.count()).where(
            ReviewModel.tenant_id == tenant_id
        ).group_by(ReviewModel.status)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    def _to_domain(self, model: ReviewModel) -> Review:
        decisions = []
        for d in (model.decisions or []):
            decisions.append(ReviewDecision(
                decision=d.get("decision", ""),
                decided_by=d.get("decided_by", ""),
                decided_at=datetime.fromisoformat(d["decided_at"]) if d.get("decided_at") else datetime.now(timezone.utc),
                comments=d.get("comments", ""),
            ))
        return Review(
            id=model.id, tenant_id=model.tenant_id,
            review_type=ReviewType(model.review_type),
            target_id=model.target_id, target_type=model.target_type,
            status=ReviewStatus(model.status),
            assigned_to=model.assigned_to or "",
            requested_by=model.requested_by or "",
            decisions=decisions,
            metadata=model.extra_metadata or {},
            created_at=model.created_at, updated_at=model.updated_at,
        )


# ── P1-6: Quota + Territory Postgres Repositories ──

from domains.revenue.quota.models import Quota, QuotaPeriod, QuotaSnapshot, QuotaStatus, TeamAggregate
from domains.revenue.quota.repo import QuotaRepository

from domains.revenue.territory.models import Territory
from domains.revenue.territory.repo import TerritoryRepository


class PostgresQuotaRepository(QuotaRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, quota: Quota) -> Quota:
        stmt = select(QuotaModel).where(QuotaModel.id == quota.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.rep_id = quota.rep_id
            model.rep_name = quota.rep_name
            model.period = quota.period.value
            model.target_amount = quota.target_amount
            model.attained_amount = quota.attained_amount
            model.start_date = quota.start_date
            model.end_date = quota.end_date
            model.status = quota.status.value
            model.extra_metadata = quota.metadata
            model.updated_at = datetime.now(timezone.utc)
        else:
            model = QuotaModel(
                id=quota.id, tenant_id=quota.tenant_id,
                rep_id=quota.rep_id, rep_name=quota.rep_name,
                period=quota.period.value,
                target_amount=quota.target_amount,
                attained_amount=quota.attained_amount,
                start_date=quota.start_date, end_date=quota.end_date,
                status=quota.status.value,
                extra_metadata=quota.metadata,
            )
            self.session.add(model)
        await self.session.flush()
        return quota

    async def get(self, quota_id: str) -> Quota | None:
        stmt = select(QuotaModel).where(QuotaModel.id == quota_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def delete(self, quota_id: str) -> bool:
        from sqlalchemy import delete as sa_delete
        result = await self.session.execute(
            sa_delete(QuotaModel).where(QuotaModel.id == quota_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def list_by_tenant(
        self, tenant_id: str, rep_id: str | None = None,
        period: str | None = None, status: str | None = None,
        limit: int = 50,
    ) -> list[Quota]:
        stmt = select(QuotaModel).where(QuotaModel.tenant_id == tenant_id)
        if rep_id:
            stmt = stmt.where(QuotaModel.rep_id == rep_id)
        if period:
            stmt = stmt.where(QuotaModel.period == period)
        if status:
            stmt = stmt.where(QuotaModel.status == status)
        stmt = stmt.order_by(QuotaModel.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_rep(self, tenant_id: str, rep_id: str) -> list[Quota]:
        return await self.list_by_tenant(tenant_id, rep_id=rep_id)

    async def get_active_quota(self, tenant_id: str, rep_id: str) -> Quota | None:
        stmt = select(QuotaModel).where(
            QuotaModel.tenant_id == tenant_id,
            QuotaModel.rep_id == rep_id,
            QuotaModel.status == "active",
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save_snapshot(self, snapshot: QuotaSnapshot) -> QuotaSnapshot:
        existing = await self.session.execute(
            select(QuotaSnapshotModel).where(QuotaSnapshotModel.id == snapshot.id)
        )
        model = existing.scalar_one_or_none()
        if model:
            return self._snapshot_to_domain(model)

        model = QuotaSnapshotModel(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            period_label=snapshot.period_label,
            quotas=[self._quota_to_snapshot_json(quota) for quota in snapshot.quotas],
            team=self._team_to_snapshot_json(snapshot.team),
            total_target=snapshot.total_target,
            total_attained=snapshot.total_attained,
            overall_attainment=snapshot.overall_attainment,
            created_at=snapshot.created_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._snapshot_to_domain(model)

    async def list_snapshots(self, tenant_id: str, limit: int = 10) -> list[QuotaSnapshot]:
        stmt = (
            select(QuotaSnapshotModel)
            .where(QuotaSnapshotModel.tenant_id == tenant_id)
            .order_by(QuotaSnapshotModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._snapshot_to_domain(model) for model in result.scalars().all()]

    def _to_domain(self, model: QuotaModel) -> Quota:
        return Quota(
            id=model.id, tenant_id=model.tenant_id,
            rep_id=model.rep_id, rep_name=model.rep_name or "",
            period=QuotaPeriod(model.period),
            target_amount=float(model.target_amount),
            attained_amount=float(model.attained_amount),
            start_date=model.start_date, end_date=model.end_date,
            status=QuotaStatus(model.status),
            metadata=model.extra_metadata or {},
            created_at=model.created_at, updated_at=model.updated_at,
        )

    @staticmethod
    def _quota_to_snapshot_json(quota: Quota) -> dict[str, Any]:
        return {
            "id": quota.id,
            "tenant_id": quota.tenant_id,
            "rep_id": quota.rep_id,
            "rep_name": quota.rep_name,
            "period": quota.period.value,
            "target_amount": quota.target_amount,
            "attained_amount": quota.attained_amount,
            "start_date": quota.start_date.isoformat(),
            "end_date": quota.end_date.isoformat(),
            "status": quota.status.value,
            "created_at": quota.created_at.isoformat(),
            "updated_at": quota.updated_at.isoformat(),
            "metadata": quota.metadata,
        }

    @staticmethod
    def _quota_from_snapshot_json(data: dict[str, Any]) -> Quota:
        return Quota(
            id=data["id"],
            tenant_id=data["tenant_id"],
            rep_id=data["rep_id"],
            rep_name=data.get("rep_name", ""),
            period=QuotaPeriod(data.get("period", QuotaPeriod.QUARTERLY.value)),
            target_amount=float(data.get("target_amount", 0.0)),
            attained_amount=float(data.get("attained_amount", 0.0)),
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            status=QuotaStatus(data.get("status", QuotaStatus.ACTIVE.value)),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata") or {},
        )

    @staticmethod
    def _team_to_snapshot_json(team: TeamAggregate | None) -> dict[str, Any] | None:
        if team is None:
            return None
        return {
            "tenant_id": team.tenant_id,
            "total_targets": team.total_targets,
            "total_attained": team.total_attained,
            "overall_attainment_percent": team.overall_attainment_percent,
            "rep_count": team.rep_count,
            "reps_on_track": team.reps_on_track,
            "reps_at_risk": team.reps_at_risk,
            "reps_missed": team.reps_missed,
        }

    @staticmethod
    def _team_from_snapshot_json(data: dict[str, Any] | None) -> TeamAggregate | None:
        if data is None:
            return None
        return TeamAggregate(
            tenant_id=data["tenant_id"],
            total_targets=float(data.get("total_targets", 0.0)),
            total_attained=float(data.get("total_attained", 0.0)),
            overall_attainment_percent=float(data.get("overall_attainment_percent", 0.0)),
            rep_count=int(data.get("rep_count", 0)),
            reps_on_track=int(data.get("reps_on_track", 0)),
            reps_at_risk=int(data.get("reps_at_risk", 0)),
            reps_missed=int(data.get("reps_missed", 0)),
        )

    def _snapshot_to_domain(self, model: QuotaSnapshotModel) -> QuotaSnapshot:
        return QuotaSnapshot(
            id=model.id,
            tenant_id=model.tenant_id,
            period_label=model.period_label,
            quotas=[self._quota_from_snapshot_json(item) for item in (model.quotas or [])],
            team=self._team_from_snapshot_json(model.team),
            created_at=model.created_at,
        )


class PostgresTerritoryRepository(TerritoryRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, territory: Territory) -> Territory:
        stmt = select(TerritoryModel).where(TerritoryModel.id == territory.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.name = territory.name
            model.region = territory.region
            model.rep_id = territory.rep_id
            model.rep_name = territory.rep_name
            model.account_ids = territory.account_ids
            model.extra_metadata = territory.metadata
            model.updated_at = datetime.now(timezone.utc)
        else:
            model = TerritoryModel(
                id=territory.id, tenant_id=territory.tenant_id,
                name=territory.name, region=territory.region,
                rep_id=territory.rep_id, rep_name=territory.rep_name,
                account_ids=territory.account_ids,
                extra_metadata=territory.metadata,
            )
            self.session.add(model)
        await self.session.flush()
        return territory

    async def get(self, territory_id: str) -> Territory | None:
        stmt = select(TerritoryModel).where(TerritoryModel.id == territory_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def delete(self, territory_id: str) -> bool:
        from sqlalchemy import delete as sa_delete
        result = await self.session.execute(
            sa_delete(TerritoryModel).where(TerritoryModel.id == territory_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def list_by_tenant(
        self, tenant_id: str, rep_id: str | None = None,
        region: str | None = None, limit: int = 50,
    ) -> list[Territory]:
        stmt = select(TerritoryModel).where(TerritoryModel.tenant_id == tenant_id)
        if rep_id:
            stmt = stmt.where(TerritoryModel.rep_id == rep_id)
        if region:
            stmt = stmt.where(TerritoryModel.region == region)
        stmt = stmt.order_by(TerritoryModel.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_rep(self, tenant_id: str, rep_id: str) -> list[Territory]:
        return await self.list_by_tenant(tenant_id, rep_id=rep_id)

    async def find_territory_for_account(self, tenant_id: str, account_id: str) -> Territory | None:
        stmt = select(TerritoryModel).where(
            TerritoryModel.tenant_id == tenant_id,
            cast(TerritoryModel.account_ids, JSONB).contains([account_id]),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: TerritoryModel) -> Territory:
        return Territory(
            id=model.id, tenant_id=model.tenant_id,
            name=model.name, region=model.region or "",
            rep_id=model.rep_id or "", rep_name=model.rep_name or "",
            account_ids=model.account_ids or [],
            metadata=model.extra_metadata or {},
            created_at=model.created_at, updated_at=model.updated_at,
        )


class PostgresEvidenceRepository:
    """P2-6: Postgres-backed evidence chain repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_insight(self, insight: Insight) -> Insight:
        from domains.commercial.infrastructure.models import InsightModel
        model = InsightModel(
            id=insight.id, tenant_id=insight.tenant_id,
            category=insight.category.value, title=insight.title,
            description=insight.description, target_id=insight.target_id,
            target_type=insight.target_type, overall_confidence=insight.overall_confidence,
            confidence_level=insight.confidence_level.value,
            extra_metadata=insight.metadata,
            created_at=insight.created_at, updated_at=insight.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return insight

    async def get_insight(self, insight_id: str) -> Insight | None:
        from domains.commercial.infrastructure.models import InsightModel
        from sqlalchemy import select
        stmt = select(InsightModel).where(InsightModel.id == insight_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        evidence = await self.list_evidence(insight_id)
        return self._to_domain(model, evidence)

    async def list_insights(
        self,
        tenant_id: str,
        target_id: str | None = None,
        target_type: str | None = None,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        from domains.commercial.infrastructure.models import InsightModel
        from sqlalchemy import select
        q = select(InsightModel).where(InsightModel.tenant_id == tenant_id)
        if target_id:
            q = q.where(InsightModel.target_id == target_id)
        if target_type:
            q = q.where(InsightModel.target_type == target_type)
        if category:
            q = q.where(InsightModel.category == category.value)
        q = q.order_by(InsightModel.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        models = result.scalars().all()
        insights = []
        for m in models:
            evidence = await self.list_evidence(m.id)
            insights.append(self._to_domain(m, evidence))
        return insights

    async def list_insights_by_confidence(
        self,
        tenant_id: str,
        min_confidence: float = 0.0,
        category: InsightCategory | None = None,
        limit: int = 50,
    ) -> list[Insight]:
        from domains.commercial.infrastructure.models import InsightModel
        from sqlalchemy import select
        q = select(InsightModel).where(
            InsightModel.tenant_id == tenant_id,
            InsightModel.overall_confidence >= min_confidence,
        )
        if category:
            q = q.where(InsightModel.category == category.value)
        q = q.order_by(InsightModel.overall_confidence.desc()).limit(limit)
        result = await self.session.execute(q)
        models = result.scalars().all()
        insights = []
        for m in models:
            evidence = await self.list_evidence(m.id)
            insights.append(self._to_domain(m, evidence))
        return insights

    async def save_evidence(self, insight_id: str, evidence: EvidenceItem) -> EvidenceItem:
        from domains.commercial.infrastructure.models import EvidenceItemModel
        model = EvidenceItemModel(
            id=evidence.id, insight_id=insight_id,
            evidence_type=evidence.evidence_type.value,
            source_domain=evidence.source.source_domain,
            source_type=evidence.source.source_type,
            source_id=evidence.source.source_id,
            source_name=evidence.source.source_name,
            description=evidence.description,
            confidence=evidence.confidence,
            confidence_level=evidence.confidence_level.value,
            extra_data={
                **(evidence.data or {}),
                **({"evidence_kind": evidence.evidence_kind.value} if evidence.evidence_kind else {}),
            },
            created_at=evidence.recorded_at, updated_at=evidence.recorded_at,
        )
        self.session.add(model)
        await self.session.flush()
        return evidence

    async def list_evidence(self, insight_id: str) -> list[EvidenceItem]:
        from domains.commercial.infrastructure.models import EvidenceItemModel
        from sqlalchemy import select
        stmt = select(EvidenceItemModel).where(
            EvidenceItemModel.insight_id == insight_id
        ).order_by(EvidenceItemModel.created_at)
        result = await self.session.execute(stmt)
        return [self._evidence_to_domain(m) for m in result.scalars().all()]

    async def count_by_category(self, tenant_id: str) -> dict[str, int]:
        from domains.commercial.infrastructure.models import InsightModel
        from sqlalchemy import select, func
        stmt = select(
            InsightModel.category, func.count(InsightModel.id)
        ).where(
            InsightModel.tenant_id == tenant_id
        ).group_by(InsightModel.category)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    async def count_by_confidence(self, tenant_id: str) -> dict[str, int]:
        from domains.commercial.infrastructure.models import InsightModel
        from sqlalchemy import select, func
        stmt = select(
            InsightModel.confidence_level, func.count(InsightModel.id)
        ).where(
            InsightModel.tenant_id == tenant_id
        ).group_by(InsightModel.confidence_level)
        result = await self.session.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    def _to_domain(self, model, evidence: list[EvidenceItem] | None = None) -> Insight:
        from domains.commercial.evidence.contracts.models import (
            Insight, InsightCategory, ConfidenceLevel,
        )
        return Insight(
            id=model.id, tenant_id=model.tenant_id,
            category=InsightCategory(model.category),
            title=model.title, description=model.description,
            target_id=model.target_id, target_type=model.target_type,
            overall_confidence=model.overall_confidence,
            confidence_level=ConfidenceLevel(model.confidence_level),
            evidence_items=evidence or [],
            metadata=model.extra_metadata or {},
            created_at=model.created_at, updated_at=model.updated_at,
        )

    def _evidence_to_domain(self, model) -> EvidenceItem:
        from domains.commercial.evidence.contracts.models import (
            EvidenceItem, EvidenceType, EvidenceSource, ConfidenceLevel, EvidenceKind,
        )
        extra_data = dict(model.extra_data or {})
        raw_kind = extra_data.pop("evidence_kind", None)
        try:
            evidence_kind = EvidenceKind(raw_kind) if raw_kind else None
        except (TypeError, ValueError):
            evidence_kind = None
        return EvidenceItem(
            id=model.id,
            evidence_type=EvidenceType(model.evidence_type),
            source=EvidenceSource(
                source_domain=model.source_domain,
                source_type=model.source_type,
                source_id=model.source_id,
                source_name=model.source_name,
            ),
            description=model.description,
            confidence=model.confidence,
            confidence_level=ConfidenceLevel(model.confidence_level),
            evidence_kind=evidence_kind,
            data=extra_data,
            recorded_at=model.created_at,
        )
