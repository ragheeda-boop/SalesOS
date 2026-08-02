"""STORY-05-01 — every subscription state transition unit-tested (R-05)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.billing.service import initial_status_for_provision
from app.modules.billing.state_machine import (
    SubscriptionEvent,
    SubscriptionStatus,
    SubscriptionTransitionError,
    allowed_events,
    apply_transition,
    can_transition,
    transition_matrix,
)


# Happy-path matrix from TEST_STRATEGY + architecture §16
_HAPPY_PATH: list[tuple[str, str, str]] = [
    ("trial", "activate", "active"),
    ("active", "mark_past_due", "past_due"),
    ("past_due", "suspend", "suspended"),
    ("suspended", "reactivate", "active"),
    ("active", "churn", "churned"),
]


@pytest.mark.parametrize(("src", "event", "dst"), _HAPPY_PATH)
def test_happy_path_transitions(src: str, event: str, dst: str) -> None:
    assert apply_transition(src, event).value == dst
    assert can_transition(src, event) is True


@pytest.mark.parametrize(
    ("src", "event", "dst"),
    [
        ("trial", "suspend", "suspended"),
        ("trial", "churn", "churned"),
        ("active", "suspend", "suspended"),
        ("past_due", "activate", "active"),
        ("past_due", "churn", "churned"),
        ("suspended", "churn", "churned"),
        ("churned", "resubscribe_trial", "trial"),
        ("churned", "resubscribe_active", "active"),
    ],
)
def test_ops_edges(src: str, event: str, dst: str) -> None:
    assert apply_transition(src, event).value == dst


@pytest.mark.parametrize(
    ("src", "event"),
    [
        ("trial", "mark_past_due"),
        ("trial", "reactivate"),
        ("active", "activate"),
        ("active", "reactivate"),
        ("suspended", "activate"),
        ("suspended", "mark_past_due"),
        ("churned", "suspend"),
        ("churned", "activate"),
        ("past_due", "reactivate"),
    ],
)
def test_illegal_transitions_raise(src: str, event: str) -> None:
    with pytest.raises(SubscriptionTransitionError):
        apply_transition(src, event)
    assert can_transition(src, event) is False


def test_unknown_status_and_event() -> None:
    with pytest.raises(SubscriptionTransitionError):
        apply_transition("nope", "activate")
    with pytest.raises(SubscriptionTransitionError):
        apply_transition("trial", "nope")


def test_full_lifecycle_chain() -> None:
    status = SubscriptionStatus.TRIAL
    for event in (
        SubscriptionEvent.ACTIVATE,
        SubscriptionEvent.MARK_PAST_DUE,
        SubscriptionEvent.SUSPEND,
        SubscriptionEvent.REACTIVATE,
        SubscriptionEvent.CHURN,
    ):
        status = apply_transition(status, event)
    assert status == SubscriptionStatus.CHURNED
    status = apply_transition(status, SubscriptionEvent.RESUBSCRIBE_TRIAL)
    assert status == SubscriptionStatus.TRIAL


def test_allowed_events_and_matrix_cover_all_defined() -> None:
    matrix = transition_matrix()
    assert set(matrix) == {s.value for s in SubscriptionStatus}
    for src, event, dst in _HAPPY_PATH:
        assert matrix[src][event] == dst
    assert SubscriptionEvent.ACTIVATE in allowed_events("trial")
    assert SubscriptionEvent.REACTIVATE in allowed_events("suspended")


def test_initial_status_for_provision() -> None:
    assert initial_status_for_provision(trial_ends_at=None) == SubscriptionStatus.ACTIVE
    assert (
        initial_status_for_provision(trial_ends_at=datetime.now(UTC))
        == SubscriptionStatus.TRIAL
    )
