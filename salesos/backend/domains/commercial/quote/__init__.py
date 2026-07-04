"""Quote Domain — commercial agreement draft, not a document.

Quote is the first Aggregate that manages commercial commitment.
It produces revenue KPIs and drives the transition from sales process
to revenue operations.

State: Draft → Submitted → Approved → Sent → Accepted | Rejected | Expired
"""

from .contracts.models import ApprovalState, Quote, QuoteLine, QuoteRevision, QuoteStatus
from .contracts.repository import QuoteRepository, QuoteRevenueKPIs
from .engine.service import QuoteService

__all__ = [
    "ApprovalState",
    "Quote",
    "QuoteLine",
    "QuoteRevision",
    "QuoteStatus",
    "QuoteRepository",
    "QuoteRevenueKPIs",
    "QuoteService",
]
