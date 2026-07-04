"""Opportunity Domain — deal tracking with pipeline stages.

Part of Commercial Platform (RT1).

Key business rules:
- An Opportunity belongs to a Tenant and is associated with a Company
- Stage progression is forward-only (can't go back except to recycle)
- Stage changes are immutable events (via Timeline)
- Probability is default per stage + manual override
- Won/Lost are terminal states
"""

from .contracts.models import Opportunity, OpportunityStage, PipelineDefinition
from .contracts.repository import OpportunityQuery, OpportunityRepository

__all__ = [
    "Opportunity",
    "OpportunityStage",
    "PipelineDefinition",
    "OpportunityQuery",
    "OpportunityRepository",
]
