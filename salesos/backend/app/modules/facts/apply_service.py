"""Atomic, human-approved application of canonical facts to CRM.

This is deliberately a separate boundary from proposal creation and review.
Only an APPROVED fact can cross it, the target and tenant are locked in the
same transaction, and every mutation gets an append-only FACT_APPLIED event.
Identity/control fields stay outside the allowlist even if a proposal exists.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company
from app.modules.contact.models import Contact
from app.modules.facts.models import CanonicalFact, CanonicalFactEvent


class FactApplyError(ValueError):
    """Base error for a governed CRM apply operation."""


class FactApplyNotFound(FactApplyError):
    """The approved fact is not visible in the authenticated tenant."""


class FactApplyRejected(FactApplyError):
    """The fact cannot be applied under the write-boundary policy."""


# Keep this independent from proposal scoring: a new proposal field must not
# silently become a CRM write field.
CRM_APPLY_FIELDS: dict[str, frozenset[str]] = {
    "company": frozenset(
        {
            "city",
            "region",
            "industry",
            "website",
            "employees_count",
            "annual_revenue",
            "activity_description",
            "legal_form",
            "latitude",
            "longitude",
            "phone",
            "email",
            "address",
            "capital",
            "incorporation_date",
            "confidence_score",
        }
    ),
    "contact": frozenset(
        {"email", "phone", "mobile", "position", "position_ar", "department"}
    ),
}


@dataclass(frozen=True)
class FactApplyResult:
    fact_id: uuid.UUID
    status: str
    changed: bool
    subject_type: str
    subject_id: uuid.UUID
    field_name: str
    previous_value: Any
    applied_value: Any
    applied_at: datetime


def _json_value(value: Any) -> Any:
    """Reject containers that could smuggle multiple field updates."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list) and all(isinstance(x, (str, int, float, bool)) for x in value):
        return list(value)
    raise FactApplyRejected("approved CRM values must be scalar JSON values")


def _coerce_value(field_name: str, value: Any) -> Any:
    value = _json_value(value)
    if field_name in {"employees_count"}:
        if isinstance(value, bool) or not isinstance(value, int):
            raise FactApplyRejected(f"{field_name} requires an integer")
    if field_name in {"annual_revenue", "latitude", "longitude", "capital", "confidence_score"}:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FactApplyRejected(f"{field_name} requires a number")
    if field_name == "incorporation_date":
        if not isinstance(value, str):
            raise FactApplyRejected("incorporation_date requires ISO date text")
        try:
            value = date.fromisoformat(value)
        except ValueError as exc:
            raise FactApplyRejected("incorporation_date requires ISO date text") from exc
    return value


def _event_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


class FactApplyService:
    """Apply one approved fact atomically and idempotently."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def apply(
        self,
        *,
        tenant_id: str | uuid.UUID,
        fact_id: str | uuid.UUID,
        actor_id: str,
        reason: str,
    ) -> FactApplyResult:
        try:
            tenant_uuid = uuid.UUID(str(tenant_id))
            fact_uuid = uuid.UUID(str(fact_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise FactApplyRejected("tenant_id and fact_id must be UUIDs") from exc
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise FactApplyRejected("a verified actor_id is required")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
            raise FactApplyRejected("a non-empty apply reason is required")

        current_tenant = (
            await self.session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        ).scalar_one_or_none()
        if current_tenant != str(tenant_uuid):
            raise FactApplyRejected("tenant_id must match the authenticated database tenant scope")

        fact = (
            await self.session.execute(
                select(CanonicalFact)
                .where(CanonicalFact.id == fact_uuid, CanonicalFact.tenant_id == tenant_uuid)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if fact is None:
            raise FactApplyNotFound("fact proposal not found in the authenticated tenant")
        if fact.status == "APPLIED":
            if fact.applied_at is None:
                raise FactApplyRejected("applied fact is missing its applied timestamp")
            value = _coerce_value(fact.field_name, fact.proposed_value)
            return FactApplyResult(
                fact_id=fact.id,
                status=fact.status,
                changed=False,
                subject_type=fact.subject_type,
                subject_id=fact.subject_id,
                field_name=fact.field_name,
                previous_value=value,
                applied_value=value,
                applied_at=fact.applied_at,
            )
        if fact.status != "APPROVED":
            raise FactApplyRejected("only human-approved facts can be applied")
        if not fact.reviewer_id or not fact.reviewed_at:
            raise FactApplyRejected("approved facts require reviewer identity and timestamp")
        allowed = CRM_APPLY_FIELDS.get(fact.subject_type, frozenset())
        if fact.field_name not in allowed:
            raise FactApplyRejected("field is not allowlisted for CRM apply")

        target_model = Company if fact.subject_type == "company" else Contact
        target = (
            await self.session.execute(
                select(target_model)
                .where(target_model.id == fact.subject_id, target_model.tenant_id == tenant_uuid)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if target is None:
            raise FactApplyNotFound("CRM target not found in the authenticated tenant")
        value = _coerce_value(fact.field_name, fact.proposed_value)
        previous = getattr(target, fact.field_name)
        setattr(target, fact.field_name, value)
        applied_at = datetime.now(UTC)
        fact.status = "APPLIED"
        fact.applied_at = applied_at
        self.session.add(
            CanonicalFactEvent(
                tenant_id=tenant_uuid,
                fact_id=fact.id,
                event_type="FACT_APPLIED",
                from_status="APPROVED",
                to_status="APPLIED",
                actor_type="human",
                actor_id=actor_id.strip(),
                reason=reason.strip(),
                event_data={
                    "subject_type": fact.subject_type,
                    "subject_id": str(fact.subject_id),
                    "field_name": fact.field_name,
                    "previous_value": _event_value(previous),
                    "applied_value": _event_value(value),
                },
            )
        )
        return FactApplyResult(
            fact_id=fact.id,
            status="APPLIED",
            changed=True,
            subject_type=fact.subject_type,
            subject_id=fact.subject_id,
            field_name=fact.field_name,
            previous_value=previous,
            applied_value=value,
            applied_at=applied_at,
        )
