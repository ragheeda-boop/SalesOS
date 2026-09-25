"""Signal-driven Sales Actions — models.

Architecture:
    Agent Reach Evidence → Signals → Qualification → Priority → NBA → Sales Action

Separation: Agent Reach owns intelligence. This module owns decision + execution.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class SignalPriority(str, enum.Enum):
    """Signal priority after qualification."""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Act within 24h
    MEDIUM = "medium"  # Act within 1 week
    LOW = "low"  # Monitor, no immediate action
    NOISE = "noise"  # Ignore


class IntentLevel(str, enum.Enum):
    """Buying intent level derived from signals."""

    VERY_HIGH = "very_high"  # Multiple strong signals
    HIGH = "high"  # Strong signal(s)
    MEDIUM = "medium"  # Weak or mixed signals
    LOW = "low"  # Minimal signals
    UNKNOWN = "unknown"  # No signals


class ActionType(str, enum.Enum):
    """Types of sales actions."""

    CALL = "call"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    RESEARCH = "research"
    CREATE_TASK = "create_task"
    CREATE_OPPORTUNITY = "create_opportunity"
    FOLLOW_UP = "follow_up"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    NO_ACTION = "no_action"


class ActionUrgency(str, enum.Enum):
    """Urgency of the recommended action."""

    IMMEDIATE = "immediate"  # Do now
    TODAY = "today"  # Do today
    THIS_WEEK = "this_week"  # Do this week
    NEXT_WEEK = "next_week"  # Do next week
    MONITOR = "monitor"  # Just watch


@dataclass
class SignalQualification:
    """Qualified signal with priority score."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_id: str = ""  # Reference to agent_signals.id
    company_name: str = ""
    signal_type: str = ""
    raw_confidence: str = ""  # high/medium/low from Agent Reach
    priority: SignalPriority = SignalPriority.NOISE
    priority_score: float = 0.0  # 0-100
    intent_contribution: float = 0.0  # How much this signal contributes to intent
    qualification_notes: str = ""
    qualified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "company_name": self.company_name,
            "signal_type": self.signal_type,
            "raw_confidence": self.raw_confidence,
            "priority": self.priority.value,
            "priority_score": self.priority_score,
            "intent_contribution": self.intent_contribution,
            "qualification_notes": self.qualification_notes,
            "qualified_at": self.qualified_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AccountPriority:
    """Account priority based on aggregated signals + CRM context."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    tenant_id: str = ""
    intent_level: IntentLevel = IntentLevel.UNKNOWN
    intent_score: float = 0.0  # 0-100
    signal_count: int = 0
    critical_signals: int = 0
    high_signals: int = 0
    recency_score: float = 0.0  # 0-1, how recent are signals
    diversity_score: float = 0.0  # 0-1, how many signal types
    top_signal_types: list[str] = field(default_factory=list)
    recommended_action: ActionType = ActionType.NO_ACTION
    action_urgency: ActionUrgency = ActionUrgency.MONITOR
    scored_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "intent_level": self.intent_level.value,
            "intent_score": self.intent_score,
            "signal_count": self.signal_count,
            "critical_signals": self.critical_signals,
            "high_signals": self.high_signals,
            "recency_score": self.recency_score,
            "diversity_score": self.diversity_score,
            "top_signal_types": self.top_signal_types,
            "recommended_action": self.recommended_action.value,
            "action_urgency": self.action_urgency.value,
            "scored_at": self.scored_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class NextBestAction:
    """Recommended next action for an account."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    tenant_id: str = ""
    action_type: ActionType = ActionType.NO_ACTION
    urgency: ActionUrgency = ActionUrgency.MONITOR
    title: str = ""
    description: str = ""
    rationale: str = ""  # Why this action
    signal_ids: list[str] = field(default_factory=list)  # Supporting signals
    confidence: float = 0.0  # 0-1
    channel: str = ""  # Recommended channel (email/phone/whatsapp)
    suggested_message: str = ""  # Draft message
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "action_type": self.action_type.value,
            "urgency": self.urgency.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "signal_ids": self.signal_ids,
            "confidence": self.confidence,
            "channel": self.channel,
            "suggested_message": self.suggested_message,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SalesAction:
    """Executed sales action (audit trail)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nba_id: str = ""  # Reference to NextBestAction
    company_name: str = ""
    tenant_id: str = ""
    user_id: str = ""
    action_type: ActionType = ActionType.NO_ACTION
    status: str = "pending"  # pending, in_progress, completed, skipped
    outcome: str = ""  # positive, neutral, negative
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nba_id": self.nba_id,
            "company_name": self.company_name,
            "action_type": self.action_type.value,
            "status": self.status,
            "outcome": self.outcome,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


@dataclass
class DashboardMetrics:
    """Aggregated metrics for the Signal Actions dashboard."""

    total_accounts: int = 0
    accounts_with_signals: int = 0
    critical_accounts: int = 0
    high_priority_accounts: int = 0
    pending_actions: int = 0
    completed_actions: int = 0
    top_actions: list[dict[str, Any]] = field(default_factory=list)
    top_signals: list[dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_accounts": self.total_accounts,
            "accounts_with_signals": self.accounts_with_signals,
            "critical_accounts": self.critical_accounts,
            "high_priority_accounts": self.high_priority_accounts,
            "pending_actions": self.pending_actions,
            "completed_actions": self.completed_actions,
            "top_actions": self.top_actions,
            "top_signals": self.top_signals,
            "generated_at": self.generated_at.isoformat(),
        }
