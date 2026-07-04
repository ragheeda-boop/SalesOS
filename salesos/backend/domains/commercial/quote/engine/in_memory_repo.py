"""In-memory Quote repository for testing and development."""

from __future__ import annotations

from ..contracts.models import Quote, QuoteStatus
from ..contracts.repository import QuoteRepository, QuoteRevenueKPIs


class InMemoryQuoteRepository(QuoteRepository):

    def __init__(self):
        self._quotes: dict[str, Quote] = {}

    async def save(self, quote: Quote) -> Quote:
        self._quotes[quote.id] = quote
        return quote

    async def get(self, quote_id: str) -> Quote | None:
        return self._quotes.get(quote_id)

    async def get_by_opportunity(self, opportunity_id: str) -> list[Quote]:
        return [q for q in self._quotes.values() if q.opportunity_id == opportunity_id]

    async def list_by_tenant(self, tenant_id: str, status: QuoteStatus | None = None) -> list[Quote]:
        items = [q for q in self._quotes.values() if q.tenant_id == tenant_id]
        if status:
            items = [q for q in items if q.status == status]
        return items

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for q in self._quotes.values():
            if q.tenant_id == tenant_id:
                counts[q.status.value] = counts.get(q.status.value, 0) + 1
        return counts

    async def revenue_kpis(self, tenant_id: str) -> QuoteRevenueKPIs:
        quotes = [q for q in self._quotes.values() if q.tenant_id == tenant_id]
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
