"""Proposal Domain — communication layer, not commercial truth.

Proposal references Quote revisions. It never duplicates pricing.
Its lifecycle is about business communication: generated → delivered → viewed → accepted.
Acceptance is an event the Rule Engine consumes — Proposal doesn't close opportunities.
"""

from .contracts.models import Proposal, ProposalSection, ProposalStatus, ProposalTemplate
from .contracts.repository import ProposalKPIs, ProposalRepository
from .engine.service import ProposalService

__all__ = [
    "Proposal",
    "ProposalSection",
    "ProposalStatus",
    "ProposalTemplate",
    "ProposalKPIs",
    "ProposalRepository",
    "ProposalService",
]
