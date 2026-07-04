"""Activity Domain — business execution engine, not a log.

ActivitySession is the aggregate. Activities live inside sessions.
Outcomes are separate from Pipeline progression — a Rule Engine bridges them.
"""

from .contracts.models import Activity, ActivityOutcome, ActivitySession, ActivityType, OutcomeDefinition
from .contracts.repository import ActivityRepository, ActivitySessionQuery
from .contracts.outcome_catalog import OutcomeCatalog
from .engine.service import ActivityService
from .engine.rule_engine import ActivityRuleEngine

__all__ = [
    "Activity",
    "ActivityOutcome",
    "ActivitySession",
    "ActivityType",
    "OutcomeDefinition",
    "OutcomeCatalog",
    "ActivityRepository",
    "ActivitySessionQuery",
    "ActivityService",
    "ActivityRuleEngine",
]
