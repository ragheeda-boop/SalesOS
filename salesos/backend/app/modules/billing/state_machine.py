"""STORY-05-01 — Subscription status state machine (pure, no I/O).

Canonical lifecycle (SAAS_PLATFORM_ARCHITECTURE §16 / TEST_STRATEGY):

  trial → active → past_due → suspended → churned

Additional Owner/ops edges (explicit, unit-tested):

  - trial → suspended (manual TOS) | trial → churned (abandoned trial)
  - active → suspended (manual) | active → churned
  - past_due → active (payment recovered before suspend)
  - suspended → active (reactivate)
  - churned → trial | churned → active (resubscribe)

No Stripe / webhook side effects here — STORY-05-02+.
Not Production GO.
"""

from __future__ import annotations

from enum import StrEnum


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CHURNED = "churned"


class SubscriptionEvent(StrEnum):
    """Named triggers — keep webhook/dunning adapters mapped to these."""

    ACTIVATE = "activate"
    MARK_PAST_DUE = "mark_past_due"
    SUSPEND = "suspend"
    REACTIVATE = "reactivate"
    CHURN = "churn"
    RESUBSCRIBE_TRIAL = "resubscribe_trial"
    RESUBSCRIBE_ACTIVE = "resubscribe_active"


class SubscriptionTransitionError(ValueError):
    """Illegal status transition or unknown event."""


# (from_status, event) → to_status
_TRANSITIONS: dict[tuple[SubscriptionStatus, SubscriptionEvent], SubscriptionStatus] = {
    (SubscriptionStatus.TRIAL, SubscriptionEvent.ACTIVATE): SubscriptionStatus.ACTIVE,
    (SubscriptionStatus.TRIAL, SubscriptionEvent.SUSPEND): SubscriptionStatus.SUSPENDED,
    (SubscriptionStatus.TRIAL, SubscriptionEvent.CHURN): SubscriptionStatus.CHURNED,
    (SubscriptionStatus.ACTIVE, SubscriptionEvent.MARK_PAST_DUE): SubscriptionStatus.PAST_DUE,
    (SubscriptionStatus.ACTIVE, SubscriptionEvent.SUSPEND): SubscriptionStatus.SUSPENDED,
    (SubscriptionStatus.ACTIVE, SubscriptionEvent.CHURN): SubscriptionStatus.CHURNED,
    (SubscriptionStatus.PAST_DUE, SubscriptionEvent.ACTIVATE): SubscriptionStatus.ACTIVE,
    (SubscriptionStatus.PAST_DUE, SubscriptionEvent.SUSPEND): SubscriptionStatus.SUSPENDED,
    (SubscriptionStatus.PAST_DUE, SubscriptionEvent.CHURN): SubscriptionStatus.CHURNED,
    (SubscriptionStatus.SUSPENDED, SubscriptionEvent.REACTIVATE): SubscriptionStatus.ACTIVE,
    (SubscriptionStatus.SUSPENDED, SubscriptionEvent.CHURN): SubscriptionStatus.CHURNED,
    (SubscriptionStatus.CHURNED, SubscriptionEvent.RESUBSCRIBE_TRIAL): SubscriptionStatus.TRIAL,
    (SubscriptionStatus.CHURNED, SubscriptionEvent.RESUBSCRIBE_ACTIVE): SubscriptionStatus.ACTIVE,
}


def normalize_status(status: str | SubscriptionStatus) -> SubscriptionStatus:
    try:
        return SubscriptionStatus(str(status))
    except ValueError as exc:
        raise SubscriptionTransitionError(f"unknown subscription status: {status!r}") from exc


def normalize_event(event: str | SubscriptionEvent) -> SubscriptionEvent:
    try:
        return SubscriptionEvent(str(event))
    except ValueError as exc:
        raise SubscriptionTransitionError(f"unknown subscription event: {event!r}") from exc


def can_transition(
    status: str | SubscriptionStatus,
    event: str | SubscriptionEvent,
) -> bool:
    current = normalize_status(status)
    ev = normalize_event(event)
    return (current, ev) in _TRANSITIONS


def apply_transition(
    status: str | SubscriptionStatus,
    event: str | SubscriptionEvent,
) -> SubscriptionStatus:
    """Return next status or raise ``SubscriptionTransitionError``."""
    current = normalize_status(status)
    ev = normalize_event(event)
    nxt = _TRANSITIONS.get((current, ev))
    if nxt is None:
        raise SubscriptionTransitionError(
            f"illegal transition: status={current.value!r} event={ev.value!r}"
        )
    return nxt


def allowed_events(status: str | SubscriptionStatus) -> frozenset[SubscriptionEvent]:
    current = normalize_status(status)
    return frozenset(ev for (st, ev) in _TRANSITIONS if st == current)


def transition_matrix() -> dict[str, dict[str, str]]:
    """Human/docs-friendly map: status → {event: next_status}."""
    out: dict[str, dict[str, str]] = {s.value: {} for s in SubscriptionStatus}
    for (st, ev), nxt in _TRANSITIONS.items():
        out[st.value][ev.value] = nxt.value
    return out
