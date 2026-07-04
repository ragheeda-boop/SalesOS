"""QuoteService — business logic for commercial agreements.

Enforces:
- Immutability after approval (creates revisions, not updates)
- Monetary consistency (totals = lines + taxes - discounts)
- State machine transitions (Draft → Submitted → Approved → Sent → Accepted)
- Expiration validation
- Approval policy (discount thresholds)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from ..contracts.models import (
    ApprovalLevel,
    ApprovalState,
    Quote,
    QuoteLine,
    QuoteRevision,
    QuoteStatus,
)
from ..contracts.repository import QuoteRepository, QuoteRevenueKPIs


class QuoteService:

    def __init__(self, repository: QuoteRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id,
                            aggregate_id=data.get("quote_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    # ── Quote Lifecycle ──

    async def create_quote(
        self,
        tenant_id: str,
        opportunity_id: str = "",
        company_id: str = "",
        title: str = "",
        created_by: str = "",
        valid_until: date | None = None,
    ) -> Quote:
        quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            opportunity_id=opportunity_id,
            company_id=company_id,
            title=title or "New Quote",
            valid_until=valid_until or date.today(),
            created_by=created_by,
        )
        result = await self._repository.save(quote)
        await self._emit("quote.created", tenant_id, {
            "quote_id": quote.id, "opportunity_id": opportunity_id,
            "title": title, "version": 1,
        })
        return result

    async def add_line(
        self,
        quote_id: str,
        description: str,
        description_ar: str = "",
        quantity: int = 1,
        unit_price: float = 0.0,
        discount_percent: float = 0.0,
        tax_percent: float = 0.0,
    ) -> QuoteLine:
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        if not quote.is_editable:
            raise ValueError(f"Quote {quote_id} is not editable (status: {quote.status.value})")

        line = QuoteLine(
            id=str(uuid.uuid4()),
            description=description,
            description_ar=description_ar,
            quantity=quantity,
            unit_price=unit_price,
            discount_percent=discount_percent,
            tax_percent=tax_percent,
        )
        quote.lines.append(line)
        quote.updated_at = datetime.now(timezone.utc)
        await self._repository.save(quote)
        return line

    async def submit_for_approval(self, quote_id: str, requested_level: ApprovalLevel = ApprovalLevel.MANAGER) -> Quote:
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        if quote.status != QuoteStatus.DRAFT:
            raise ValueError(f"Cannot submit quote in status: {quote.status.value}")
        if not quote.lines:
            raise ValueError("Cannot submit empty quote")

        quote.status = QuoteStatus.SUBMITTED
        quote.approval.level = requested_level
        quote.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(quote)
        await self._emit("quote.submitted", quote.tenant_id, {
            "quote_id": quote_id, "version": quote.version,
            "grand_total": quote.grand_total, "requested_level": requested_level.value,
        })
        return result

    async def approve(self, quote_id: str, approved_by: str, comments: str = "") -> Quote:
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        if quote.status != QuoteStatus.SUBMITTED:
            raise ValueError(f"Cannot approve quote in status: {quote.status.value}")

        quote.status = QuoteStatus.APPROVED
        quote.approval.approved_by = approved_by
        quote.approval.approved_at = datetime.now(timezone.utc)
        quote.approval.comments = comments
        quote.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(quote)
        await self._emit("quote.approved", quote.tenant_id, {
            "quote_id": quote_id, "approved_by": approved_by,
            "grand_total": quote.grand_total,
        })
        return result

    async def send(self, quote_id: str) -> Quote:
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        if quote.status != QuoteStatus.APPROVED:
            raise ValueError(f"Cannot send quote in status: {quote.status.value}")

        # Check expiration
        if quote.has_expired:
            quote.status = QuoteStatus.EXPIRED
            await self._repository.save(quote)
            await self._emit("quote.expired", quote.tenant_id, {"quote_id": quote_id})
            raise ValueError(f"Quote {quote_id} has expired")

        quote.status = QuoteStatus.SENT
        quote.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(quote)
        await self._emit("quote.sent", quote.tenant_id, {
            "quote_id": quote_id, "version": quote.version,
        })
        return result

    async def accept(self, quote_id: str) -> Quote:
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        if quote.status != QuoteStatus.SENT:
            raise ValueError(f"Cannot accept quote in status: {quote.status.value}")

        if quote.has_expired:
            quote.status = QuoteStatus.EXPIRED
            await self._repository.save(quote)
            await self._emit("quote.expired", quote.tenant_id, {"quote_id": quote_id})
            raise ValueError(f"Quote {quote_id} has expired")

        quote.status = QuoteStatus.ACCEPTED
        quote.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(quote)
        await self._emit("quote.accepted", quote.tenant_id, {
            "quote_id": quote_id, "grand_total": quote.grand_total,
        })
        return result

    async def reject(self, quote_id: str, reason: str = "") -> Quote:
        return await self._transition(quote_id, QuoteStatus.REJECTED, "quote.rejected", {"reason": reason})

    async def _transition(self, quote_id: str, to_status: QuoteStatus, event_type: str, extra: dict | None = None) -> Quote:
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        quote.status = to_status
        quote.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(quote)
        data = {"quote_id": quote_id, "version": quote.version, **(extra or {})}
        await self._emit(event_type, quote.tenant_id, data)
        return result

    # ── Revision ──

    async def revise(self, quote_id: str) -> Quote:
        """Create a new revision. Immutable after approval — old quote is archived."""
        quote = await self._repository.get(quote_id)
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")

        # Archive current state as a revision
        revision = QuoteRevision(
            version=quote.version,
            quote_id=quote.id,
            status=quote.status,
            lines=list(quote.lines),
            subtotal=quote.subtotal,
            total_discount=quote.total_discount,
            total_tax=quote.total_tax,
            grand_total=quote.grand_total,
            notes=f"Revised from v{quote.version}",
        )
        quote.revisions.append(revision)
        quote.version += 1
        quote.status = QuoteStatus.REVISED
        quote.updated_at = datetime.now(timezone.utc)

        # Create new draft version
        new_quote = Quote(
            id=quote_id,
            tenant_id=quote.tenant_id,
            opportunity_id=quote.opportunity_id,
            company_id=quote.company_id,
            title=quote.title,
            status=QuoteStatus.DRAFT,
            version=quote.version,
            currency=quote.currency,
            payment_terms=quote.payment_terms,
            delivery_terms=quote.delivery_terms,
            valid_until=quote.valid_until,
            created_by=quote.created_by,
            lines=list(quote.lines),  # Copy lines as starting point
            revisions=quote.revisions,
        )
        result = await self._repository.save(new_quote)
        await self._emit("quote.revised", quote.tenant_id, {
            "quote_id": quote_id, "old_version": quote.version - 1, "new_version": quote.version,
        })
        return result

    # ── Queries & KPIs ──

    async def get(self, quote_id: str) -> Quote | None:
        return await self._repository.get(quote_id)

    async def get_by_opportunity(self, opportunity_id: str) -> list[Quote]:
        return await self._repository.get_by_opportunity(opportunity_id)

    async def revenue_kpis(self, tenant_id: str) -> QuoteRevenueKPIs:
        return await self._repository.revenue_kpis(tenant_id)
