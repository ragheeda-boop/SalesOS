"""Signal-driven Sales Actions — Evidence -> Signals -> Decision -> Action.

Architecture:
    Agent Reach (intelligence) -> Evidence -> Signals
        -> Qualification (score + classify)
        -> Account Priority (intent score)
        -> Next Best Action (deterministic decision)
        -> Sales Action (execute + audit trail)

Separation: Agent Reach owns intelligence. This module owns decision + execution.
"""

from .models import (
    AccountPriority,
    ActionType,
    ActionUrgency,
    IntentLevel,
    NextBestAction,
    SignalPriority,
    SignalQualification,
    SalesAction,
)
from .qualification import qualify_signal, compute_intent_level
from .priority import score_account
from .nba import generate_nba
from .actions import ActionExecutor

__all__ = [
    "AccountPriority",
    "ActionType",
    "ActionUrgency",
    "IntentLevel",
    "NextBestAction",
    "SignalPriority",
    "SignalQualification",
    "SalesAction",
    "qualify_signal",
    "compute_intent_level",
    "score_account",
    "generate_nba",
    "ActionExecutor",
]
