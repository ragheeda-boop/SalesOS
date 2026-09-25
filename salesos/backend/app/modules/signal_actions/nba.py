"""Next Best Action Engine — deterministic decision engine.

Produces actionable recommendations from account priority + signal context.
No LLM. Deterministic rules based on signal types, intent, and CRM state.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .models import (
    ActionType,
    AccountPriority,
    IntentLevel,
    NextBestAction,
    SignalPriority,
    SignalQualification,
)


def generate_nba(
    priority: AccountPriority,
    qualifications: list[SignalQualification],
) -> NextBestAction:
    """Generate a single Next Best Action for an account.

    Rules-based: signal type + intent level + CRM context -> action.
    """
    action_type = priority.recommended_action
    urgency = priority.action_urgency

    # Build rationale from top signals
    top_signals = sorted(qualifications, key=lambda q: q.priority_score, reverse=True)[:3]
    signal_summary = ", ".join(
        f"{q.signal_type}(score={q.priority_score:.0f})" for q in top_signals
    )
    signal_ids = [q.signal_id for q in top_signals if q.signal_id]

    # Generate action-specific content
    title, description, channel, message = _action_content(
        action_type, priority.company_name, top_signals, priority.intent_level
    )

    rationale = (
        f"Intent={priority.intent_level.value}({priority.intent_score:.0f}/100), "
        f"signals=[{signal_summary}], "
        f"critical={priority.critical_signals}, high={priority.high_signals}"
    )

    # Expiry based on urgency
    expires = _expiry(urgency)

    return NextBestAction(
        company_name=priority.company_name,
        tenant_id=priority.tenant_id,
        action_type=action_type,
        urgency=urgency,
        title=title,
        description=description,
        rationale=rationale,
        signal_ids=signal_ids,
        confidence=min(1.0, priority.intent_score / 100),
        channel=channel,
        suggested_message=message,
        expires_at=expires,
        metadata={
            "intent_score": priority.intent_score,
            "signal_count": priority.signal_count,
        },
    )


def _action_content(
    action: ActionType,
    company: str,
    top_signals: list[SignalQualification],
    intent: IntentLevel,
) -> tuple[str, str, str, str]:
    """Generate title, description, channel, message for each action type."""
    signal_types = [q.signal_type for q in top_signals]

    if action == ActionType.CALL:
        return (
            f"Call {company} — high-priority signals detected",
            f"Multiple strong signals ({', '.join(signal_types[:3])}) indicate active buying intent. "
            f"A direct call is the fastest path to engagement.",
            "phone",
            f"Hi, I noticed {company} has been in the news recently regarding "
            f"{', '.join(signal_types[:2])}. I'd love to discuss how we can help.",
        )

    if action == ActionType.EMAIL:
        return (
            f"Email {company} — intent signals detected",
            f"Recent signals ({', '.join(signal_types[:3])}) suggest active interest. "
            f"An email with relevant context should establish initial contact.",
            "email",
            f"Subject: Following up on {company}'s recent {signal_types[0] if signal_types else 'activity'}\n\n"
            f"Hi, I noticed {company} has been making moves in "
            f"{', '.join(signal_types[:2])}. We help companies like yours...",
        )

    if action == ActionType.WHATSAPP:
        return (
            f"WhatsApp {company} — quick touch",
            f"Signal activity detected. A brief WhatsApp message is appropriate.",
            "whatsapp",
            f"Hi from SalesOS! I noticed {company}'s recent "
            f"{signal_types[0] if signal_types else 'activity'}. Quick question...",
        )

    if action == ActionType.CREATE_OPPORTUNITY:
        return (
            f"Create opportunity for {company}",
            f"Intent score {intent.value} with {len(top_signals)} signals. "
            f"Account is ready for pipeline.",
            "internal",
            "",
        )

    if action == ActionType.PROPOSAL:
        return (
            f"Send proposal to {company}",
            f"High intent with active opportunity. Proposal stage is appropriate.",
            "internal",
            "",
        )

    if action == ActionType.FOLLOW_UP:
        return (
            f"Follow up with {company} — urgent signals",
            f"Critical signals detected on active opportunity. Immediate follow-up required.",
            "internal",
            "",
        )

    if action == ActionType.MEETING:
        return (
            f"Schedule meeting with {company}",
            f"Strong signals warrant a dedicated meeting to discuss needs.",
            "internal",
            "",
        )

    if action == ActionType.RESEARCH:
        return (
            f"Research {company} further",
            f"Weak or mixed signals. Gather more intelligence before acting.",
            "internal",
            "",
        )

    if action == ActionType.CREATE_TASK:
        return (
            f"Create task for {company}",
            f"Monitor account for further signals.",
            "internal",
            "",
        )

    return (
        f"Monitor {company}",
        "No actionable signals. Continue monitoring.",
        "",
        "",
    )


def _expiry(urgency) -> datetime:
    """Action expiry based on urgency."""
    now = datetime.now(UTC)
    if urgency == "immediate":
        return now + timedelta(hours=4)
    if urgency == "today":
        return now + timedelta(days=1)
    if urgency == "this_week":
        return now + timedelta(days=7)
    if urgency == "next_week":
        return now + timedelta(days=14)
    return now + timedelta(days=30)
