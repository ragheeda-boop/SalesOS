"""PostgreSQL repository for Decision Center — production implementation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, Index, String as sa_String, Text, and_, func, select, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from sdk.database import Base, BaseModel

from .models import (
    Decision,
    DecisionAudit,
    DecisionDomain,
    DecisionFeedback,
    DecisionStatus,
    DecisionTemplate,
    DecisionType,
    FeedbackAggregate,
    FeedbackRating,
)
from .repository import DecisionCenterRepository


def _aware_utc(dt: datetime) -> datetime:
    """Ensure tz-aware UTC for TIMESTAMPTZ columns (DEC-130d ORM align)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class DecisionModel(BaseModel):
    __tablename__ = "decision_center_decisions"
    __table_args__ = (
        # Live index names — metadata register (DEC-130d)
        Index("ix_dcd_entity", "entity_type", "entity_id"),
        Index("ix_dcd_status", "status"),
    )

    tenant_id: Mapped[str] = mapped_column(nullable=False, index=True)
    domain: Mapped[str] = mapped_column(nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(nullable=False)
    alternatives: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    decision_metadata: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    is_ensemble: Mapped[bool] = mapped_column(server_default=text("false"))
    ensemble_votes: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="active")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DecisionAuditModel(Base):
    __tablename__ = "decision_center_audits"

    decision_id: Mapped[str] = mapped_column(primary_key=True)
    input_context: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    reasoning_steps: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    confidence_breakdown: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    provider_used: Mapped[str] = mapped_column(nullable=False)
    alternatives_considered: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ensemble_metadata: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)


class DecisionFeedbackModel(Base):
    __tablename__ = "decision_center_feedback"
    __table_args__ = (Index("ix_dcf_decision", "decision_id"),)

    id: Mapped[str] = mapped_column(primary_key=True)
    decision_id: Mapped[str] = mapped_column(nullable=False, index=True)
    rating: Mapped[str] = mapped_column(nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DecisionTemplateModel(Base):
    __tablename__ = "decision_center_templates"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    template_type: Mapped[str] = mapped_column(nullable=False, index=True)
    config: Mapped[dict | None] = mapped_column(type_=JSONB, nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(nullable=True, index=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def _decision_from_row(row: DecisionModel) -> Decision:
    ens_votes = None
    if row.ensemble_votes:
        from .models import EnsembleVote as EV
        ens_votes = [
            EV(
                provider=v.get("provider", ""),
                decision=v.get("decision", ""),
                confidence=v.get("confidence", 0.0),
                reasoning=v.get("reasoning", ""),
                raw_response=v.get("rawResponse"),
                latency_ms=v.get("latencyMs"),
            )
            for v in row.ensemble_votes
        ] if isinstance(row.ensemble_votes, list) else None

    return Decision(
        id=str(row.id),
        domain=DecisionDomain(row.domain),
        type=DecisionType(row.decision_type),
        entity_id=row.entity_id,
        entity_type=row.entity_type,
        decision=row.decision,
        confidence=row.confidence,
        reasoning=row.reasoning or "",
        provider=row.provider,
        alternatives=row.alternatives or [],
        timestamp=row.timestamp.replace(tzinfo=timezone.utc) if row.timestamp.tzinfo is None else row.timestamp,
        status=DecisionStatus(row.status),
        metadata=row.decision_metadata,
        ensemble_votes=ens_votes,
        is_ensemble=row.is_ensemble,
    )


def _audit_from_row(row: DecisionAuditModel) -> DecisionAudit:
    return DecisionAudit(
        decision_id=row.decision_id,
        input_context=row.input_context or {},
        reasoning_steps=row.reasoning_steps or [],
        confidence_breakdown=row.confidence_breakdown or {},
        provider_used=row.provider_used,
        alternatives_considered=row.alternatives_considered or [],
        timestamp=row.timestamp.replace(tzinfo=timezone.utc) if row.timestamp.tzinfo is None else row.timestamp,
        ensemble_metadata=row.ensemble_metadata,
    )


def _feedback_from_row(row: DecisionFeedbackModel) -> DecisionFeedback:
    return DecisionFeedback(
        id=row.id,
        decision_id=row.decision_id,
        rating=FeedbackRating(row.rating),
        comment=row.comment,
        actor_id=row.actor_id,
        created_at=row.created_at.replace(tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at,
    )


def _template_from_row(row: DecisionTemplateModel) -> DecisionTemplate:
    return DecisionTemplate(
        id=row.id,
        name=row.name,
        type=DecisionType(row.template_type),
        config=row.config or {},
        tenant_id=row.tenant_id or "",
        created_at=row.created_at.replace(tzinfo=timezone.utc) if row.created_at.tzinfo is None else row.created_at,
    )


class PostgresDecisionCenterRepository(DecisionCenterRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_decision(self, decision: Decision) -> Decision:
        tenant = (decision.metadata or {}).get("tenant_id", "")
        row = DecisionModel(
            id=uuid.uuid4(),
            tenant_id=tenant,
            domain=decision.domain.value,
            decision_type=decision.type.value,
            entity_id=decision.entity_id,
            entity_type=decision.entity_type,
            decision=decision.decision,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            provider=decision.provider,
            alternatives=decision.alternatives or None,
            decision_metadata=decision.metadata,
            is_ensemble=decision.is_ensemble,
            ensemble_votes=[
                {
                    "provider": v.provider,
                    "decision": v.decision,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                    "rawResponse": v.raw_response,
                    "latencyMs": v.latency_ms,
                }
                for v in decision.ensemble_votes
            ] if decision.ensemble_votes else None,
            status=decision.status.value,
            timestamp=_aware_utc(decision.timestamp),
        )
        self._session.add(row)
        await self._session.flush()
        decision.id = str(row.id)
        return decision

    async def get_decision(self, decision_id: str, tenant_id: str) -> Optional[Decision]:
        try:
            uid = uuid.UUID(decision_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(DecisionModel).where(
                DecisionModel.id == uid,
                DecisionModel.tenant_id == tenant_id,
            )
        )
        row = result.scalar_one_or_none()
        return _decision_from_row(row) if row else None

    async def update_decision_status(
        self, decision_id: str, tenant_id: str, status: str
    ) -> Optional[Decision]:
        try:
            uid = uuid.UUID(decision_id)
        except ValueError:
            return None
        result = await self._session.execute(
            select(DecisionModel).where(
                DecisionModel.id == uid,
                DecisionModel.tenant_id == tenant_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = status
        await self._session.flush()
        return _decision_from_row(row)

    async def list_decisions(
        self,
        tenant_id: str,
        domain: Optional[str] = None,
        decision_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        confidence_min: Optional[float] = None,
        confidence_max: Optional[float] = None,
        entity_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Decision], int]:
        filters = [DecisionModel.tenant_id == tenant_id]
        if domain:
            filters.append(DecisionModel.domain == domain)
        if decision_type:
            filters.append(DecisionModel.decision_type == decision_type)
        if entity_id:
            filters.append(DecisionModel.entity_id == entity_id)
        if status:
            filters.append(DecisionModel.status == status)
        if confidence_min is not None:
            filters.append(DecisionModel.confidence >= confidence_min)
        if confidence_max is not None:
            filters.append(DecisionModel.confidence <= confidence_max)
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                filters.append(DecisionModel.timestamp >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                filters.append(DecisionModel.timestamp <= dt_to)
            except ValueError:
                pass

        where = and_(*filters)
        count_q = select(func.count()).select_from(DecisionModel).where(where)
        total = await self._session.scalar(count_q) or 0

        q = select(DecisionModel).where(where).order_by(DecisionModel.timestamp.desc())
        q = q.offset(offset).limit(limit)
        rows = (await self._session.execute(q)).scalars().all()
        return [_decision_from_row(r) for r in rows], total

    async def save_audit(self, audit: DecisionAudit) -> DecisionAudit:
        row = DecisionAuditModel(
            decision_id=audit.decision_id,
            input_context=audit.input_context,
            reasoning_steps=audit.reasoning_steps,
            confidence_breakdown=audit.confidence_breakdown,
            provider_used=audit.provider_used,
            alternatives_considered=audit.alternatives_considered,
            timestamp=_aware_utc(audit.timestamp),
            ensemble_metadata=audit.ensemble_metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return audit

    async def get_audit(self, decision_id: str, tenant_id: str) -> Optional[DecisionAudit]:
        if await self.get_decision(decision_id, tenant_id) is None:
            return None
        result = await self._session.execute(
            select(DecisionAuditModel).where(DecisionAuditModel.decision_id == decision_id)
        )
        row = result.scalar_one_or_none()
        return _audit_from_row(row) if row else None

    async def save_feedback(self, feedback: DecisionFeedback) -> DecisionFeedback:
        row = DecisionFeedbackModel(
            id=feedback.id,
            decision_id=feedback.decision_id,
            rating=feedback.rating.value,
            comment=feedback.comment,
            actor_id=feedback.actor_id,
            created_at=_aware_utc(feedback.created_at),
        )
        self._session.add(row)
        await self._session.flush()
        return feedback

    async def get_feedback_for_decision(
        self, decision_id: str, tenant_id: str
    ) -> list[DecisionFeedback]:
        if await self.get_decision(decision_id, tenant_id) is None:
            return []
        result = await self._session.execute(
            select(DecisionFeedbackModel).where(
                DecisionFeedbackModel.decision_id == decision_id
            ).order_by(DecisionFeedbackModel.created_at.desc())
        )
        return [_feedback_from_row(r) for r in result.scalars().all()]

    async def get_feedback_by_type(self, tenant_id: str) -> list[FeedbackAggregate]:
        from sqlalchemy import case

        base = (
            select(
                DecisionModel.decision_type,
                func.count().label("total"),
                func.sum(case((DecisionFeedbackModel.rating == "up", 1), else_=0)).label("up_count"),
                func.sum(case((DecisionFeedbackModel.rating == "down", 1), else_=0)).label("down_count"),
            )
            .select_from(DecisionModel)
            .join(
                DecisionFeedbackModel,
                func.cast(DecisionModel.id, sa_String) == DecisionFeedbackModel.decision_id,
            )
            .where(DecisionModel.tenant_id == tenant_id)
            .group_by(DecisionModel.decision_type)
        )
        rows = (await self._session.execute(base)).all()
        results = []
        for r in rows:
            total = r.total or 0
            up = r.up_count or 0
            down = r.down_count or 0
            results.append(
                FeedbackAggregate(
                    decision_type=r.decision_type,
                    total_feedback=total,
                    up_count=up,
                    down_count=down,
                    approval_rate=up / total if total > 0 else 0.0,
                )
            )
        return results

    async def save_template(self, template: DecisionTemplate) -> DecisionTemplate:
        row = DecisionTemplateModel(
            id=template.id,
            name=template.name,
            template_type=template.type.value,
            config=template.config,
            tenant_id=template.tenant_id if template.tenant_id else None,
            created_at=_aware_utc(template.created_at),
        )
        self._session.add(row)
        await self._session.flush()
        return template

    async def get_template(self, template_id: str, tenant_id: str = "") -> Optional[DecisionTemplate]:
        result = await self._session.execute(
            select(DecisionTemplateModel).where(
                DecisionTemplateModel.id == template_id,
                (DecisionTemplateModel.tenant_id == tenant_id) | (DecisionTemplateModel.tenant_id.is_(None)),
            )
        )
        row = result.scalar_one_or_none()
        return _template_from_row(row) if row else None

    async def list_templates(self, template_type: Optional[str] = None, tenant_id: str = "") -> list[DecisionTemplate]:
        q = select(DecisionTemplateModel).where(
            (DecisionTemplateModel.tenant_id == tenant_id) | (DecisionTemplateModel.tenant_id.is_(None))
        )
        if template_type:
            q = q.where(DecisionTemplateModel.template_type == template_type)
        q = q.order_by(DecisionTemplateModel.created_at.desc())
        rows = (await self._session.execute(q)).scalars().all()
        return [_template_from_row(r) for r in rows]

    async def delete_template(self, template_id: str, tenant_id: str = "") -> bool:
        result = await self._session.execute(
            select(DecisionTemplateModel).where(
                DecisionTemplateModel.id == template_id,
                (DecisionTemplateModel.tenant_id == tenant_id) | (DecisionTemplateModel.tenant_id.is_(None)),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def update_template(
        self, template_id: str, updates: dict, tenant_id: str = ""
    ) -> Optional[DecisionTemplate]:
        result = await self._session.execute(
            select(DecisionTemplateModel).where(
                DecisionTemplateModel.id == template_id,
                (DecisionTemplateModel.tenant_id == tenant_id) | (DecisionTemplateModel.tenant_id.is_(None)),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        if "name" in updates:
            row.name = updates["name"]
        if "config" in updates:
            row.config = updates["config"]
        await self._session.flush()
        return _template_from_row(row)
