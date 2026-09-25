"""Account Priority Engine — intent score from signals + CRM context.

Combines qualified signals with account metadata to produce
a single priority score and recommended action.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .models import (
    AccountPriority,
    ActionType,
    ActionUrgency,
    IntentLevel,
    SignalPriority,
    SignalQualification,
)


def score_account(
    company_name: str,
    tenant_id: str,
    qualifications: list[SignalQualification],
    crm_data: dict | None = None,
) -> AccountPriority:
    """Score an account based on qualified signals + CRM context.

    crm_data (optional):
        - has_opportunity: bool
        - deal_stage: str
        - last_activity_days: int
        - employee_count: int
        - revenue_range: str
    """
    crm = crm_data or {}

    # Signal aggregation
    signal_count = len(qualifications)
    critical = sum(1 for q in qualifications if q.priority == SignalPriority.CRITICAL)
    high = sum(1 for q in qualifications if q.priority == SignalPriority.HIGH)
    recency = max((q.qualified_at for q in qualifications), default=datetime.now(UTC))
    recency_score = _recency_weight(recency)

    # Diversity: unique signal types
    types = list({q.signal_type for q in qualifications})
    diversity_score = min(1.0, len(types) / 5)  # 5 types = max diversity

    # Top signal types by priority
    sorted_quals = sorted(qualifications, key=lambda q: q.priority_score, reverse=True)
    top_types = list({q.signal_type for q in sorted_quals[:5]})

    # Intent level from qualification engine
    from .qualification import compute_intent_level
    intent_level, intent_score = compute_intent_level(qualifications)

    # CRM boost
    intent_score += _crm_boost(crm)
    intent_score = min(100.0, intent_score)

    # Recalculate intent level after CRM boost
    if intent_score >= 75:
        intent_level = IntentLevel.VERY_HIGH
    elif intent_score >= 55:
        intent_level = IntentLevel.HIGH
    elif intent_score >= 35:
        intent_level = IntentLevel.MEDIUM
    elif intent_score >= 15:
        intent_level = IntentLevel.LOW
    else:
        intent_level = IntentLevel.UNKNOWN

    # Recommended action
    action, urgency = _recommend_action(
        intent_level, critical, high, signal_count, crm
    )

    return AccountPriority(
        company_name=company_name,
        tenant_id=tenant_id,
        intent_level=intent_level,
        intent_score=round(intent_score, 2),
        signal_count=signal_count,
        critical_signals=critical,
        high_signals=high,
        recency_score=round(recency_score, 2),
        diversity_score=round(diversity_score, 2),
        top_signal_types=top_types,
        recommended_action=action,
        action_urgency=urgency,
        metadata={
            "crm_boost": _crm_boost(crm),
            "has_opportunity": crm.get("has_opportunity", False),
        },
    )


def _recency_weight(detected_at: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(UTC)
    age_days = max(0, (now - detected_at).days)
    if age_days <= 1:
        return 1.0
    if age_days <= 7:
        return 0.9
    if age_days <= 30:
        return 0.7
    if age_days <= 60:
        return 0.5
    return 0.3


def _crm_boost(crm: dict) -> float:
    """CRM context boost to intent score."""
    boost = 0.0
    if crm.get("has_opportunity"):
        boost += 10  # Active opportunity = higher priority
    last_activity = crm.get("last_activity_days")
    if last_activity is not None:
        if last_activity <= 7:
            boost += 8  # Recent activity
        elif last_activity <= 30:
            boost += 5
        elif last_activity <= 90:
            boost += 2
    emp = crm.get("employee_count")
    if emp and emp > 500:
        boost += 5  # Enterprise
    elif emp and emp > 50:
        boost += 3  # Mid-market
    return min(20.0, boost)


def _recommend_action(
    intent_level: IntentLevel,
    critical: int,
    high: int,
    signal_count: int,
    crm: dict,
) -> tuple[ActionType, ActionUrgency]:
    """Determine recommended action and urgency from signals + context."""

    # Critical signals -> immediate action
    if critical >= 2:
        if crm.get("has_opportunity"):
            return ActionType.FOLLOW_UP, ActionUrgency.IMMEDIATE
        return ActionType.CALL, ActionUrgency.IMMEDIATE

    if critical >= 1:
        if signal_count >= 5:
            return ActionType.MEETING, ActionUrgency.TODAY
        return ActionType.EMAIL, ActionUrgency.TODAY

    # High intent
    if intent_level in (IntentLevel.VERY_HIGH, IntentLevel.HIGH):
        if not crm.get("has_opportunity"):
            return ActionType.CREATE_OPPORTUNITY, ActionUrgency.THIS_WEEK
        return ActionType.PROPOSAL, ActionUrgency.THIS_WEEK

    # Medium intent
    if intent_level == IntentLevel.MEDIUM:
        if signal_count >= 3:
            return ActionType.RESEARCH, ActionUrgency.THIS_WEEK
        return ActionType.EMAIL, ActionUrgency.NEXT_WEEK

    # Low intent
    if intent_level == IntentLevel.LOW:
        return ActionType.RESEARCH, ActionUrgency.MONITOR

    # Unknown
    return ActionType.NO_ACTION, ActionUrgency.MONITOR
