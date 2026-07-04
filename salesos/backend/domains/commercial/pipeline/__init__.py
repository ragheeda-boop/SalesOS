"""Pipeline Domain — aggregate defining stage progression, rules, SLAs, and KPIs.

Pipeline is NOT Workflow. Pipeline answers "where is the opportunity?"
Workflow (future) answers "what should happen next?"

Every Opportunity belongs to a Pipeline. The Pipeline defines:
- Stages (ordered, entry/exit criteria, SLA, probability defaults)
- Progression rules (valid transitions)
- Terminal states (won/lost)
- Reopen policy
"""

from .contracts.models import PipelineDefinition, PipelineKPI, StageDefinition, StageEntry
from .contracts.repository import PipelineKPIs, PipelineRepository
from .engine.service import PipelineService

__all__ = [
    "PipelineDefinition",
    "PipelineKPI",
    "StageDefinition",
    "StageEntry",
    "PipelineKPIs",
    "PipelineRepository",
    "PipelineService",
]
