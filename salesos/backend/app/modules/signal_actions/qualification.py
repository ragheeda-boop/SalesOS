"""Signal Qualification Engine — classify + score signals from Agent Reach.

Deterministic, no LLM. Each signal type has a base priority weight.
Recency and source diversity modify the final score.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .models import IntentLevel, SignalPriority, SignalQualification


# Base priority weights by signal type (0-100)
SIGNAL_TYPE_WEIGHTS: dict[str, float] = {
    "hiring": 65,
    "funding": 85,
    "partnership": 55,
    "expansion": 70,
    "leadership": 60,
    "product": 50,
    "regulatory": 40,
    "rebrand": 35,
    "hiring_slowdown": 75,
    "layoffs": 80,
    "acquisition": 90,
    "ipo": 85,
    "integration": 45,
    "security": 30,
    "other": 20,
}

# Confidence multipliers
CONFIDENCE_MULTIPLIERS: dict[str, float] = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4,
}


def _recency_weight(detected_at: datetime, now: datetime | None = None) -> float:
    """Recency decay: 1.0 for today, decays to 0.3 over 90 days."""
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


def qualify_signal(
    signal_id: str,
    company_name: str,
    signal_type: str,
    raw_confidence: str,
    detected_at: datetime,
    source_count: int = 1,
) -> SignalQualification:
    """Qualify a single signal and compute priority score.

    Priority score = base_weight * confidence_multiplier * recency_weight
    """
    base = SIGNAL_TYPE_WEIGHTS.get(signal_type, 20)
    conf_mult = CONFIDENCE_MULTIPLIERS.get(raw_confidence, 0.5)
    recency = _recency_weight(detected_at)

    # Source diversity boost: +5% per additional source (max +20%)
    source_boost = min(0.2, (source_count - 1) * 0.05)

    score = min(100.0, base * conf_mult * recency * (1 + source_boost))

    # Map score to priority
    if score >= 75:
        priority = SignalPriority.CRITICAL
    elif score >= 55:
        priority = SignalPriority.HIGH
    elif score >= 35:
        priority = SignalPriority.MEDIUM
    elif score >= 15:
        priority = SignalPriority.LOW
    else:
        priority = SignalPriority.NOISE

    # Intent contribution: signal_type specific scaling
    intent_contrib = score * _intent_scale(signal_type)

    notes = (
        f"base={base:.0f} conf={raw_confidence}({conf_mult:.1f}) "
        f"recency={recency:.2f} sources={source_count}(+{source_boost:.0%})"
    )

    return SignalQualification(
        signal_id=signal_id,
        company_name=company_name,
        signal_type=signal_type,
        raw_confidence=raw_confidence,
        priority=priority,
        priority_score=round(score, 2),
        intent_contribution=round(intent_contrib, 2),
        qualification_notes=notes,
    )


def _intent_scale(signal_type: str) -> float:
    """How much a signal type contributes to buying intent (0-1)."""
    scales = {
        "funding": 0.9,  # Funded companies buy
        "hiring": 0.7,  # Hiring = growing = buying
        "expansion": 0.8,  # Expanding = buying
        "partnership": 0.6,  # Partnering = ecosystem
        "leadership": 0.5,  # New execs = change = buying
        "product": 0.4,  # Product launch = budget
        "acquisition": 0.3,  # Acquired = distraction
        "layoffs": 0.2,  # Layoffs = budget cuts
        "hiring_slowdown": 0.15,  # Slowdown = caution
        "ipo": 0.3,  # IPO = compliance buying
        "integration": 0.5,  # Integration = ecosystem
        "regulatory": 0.3,  # Regulatory = compliance
        "rebrand": 0.2,  # Rebrand = marketing spend
        "security": 0.15,  # Security = risk-averse
        "other": 0.1,
    }
    return scales.get(signal_type, 0.1)


def compute_intent_level(qualifications: list[SignalQualification]) -> tuple[IntentLevel, float]:
    """Aggregate qualified signals into an intent level.

    Returns (IntentLevel, score 0-100).
    """
    if not qualifications:
        return IntentLevel.UNKNOWN, 0.0

    # Aggregate intent contributions
    total_intent = sum(q.intent_contribution for q in qualifications)
    count = len(qualifications)

    # Normalize: expected max ~15 signals * 80 intent = 1200
    # Scale to 0-100
    raw_score = min(100.0, (total_intent / max(count, 1)) * 1.2)

    # Boost for multiple signal types
    types = {q.signal_type for q in qualifications}
    diversity_bonus = min(15.0, len(types) * 3)
    score = min(100.0, raw_score + diversity_bonus)

    if score >= 75:
        level = IntentLevel.VERY_HIGH
    elif score >= 55:
        level = IntentLevel.HIGH
    elif score >= 35:
        level = IntentLevel.MEDIUM
    elif score >= 15:
        level = IntentLevel.LOW
    else:
        level = IntentLevel.UNKNOWN

    return level, round(score, 2)
