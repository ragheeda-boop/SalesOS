"""STORY-08-06 — ConflictResolutionPolicy + write-back feedback-loop exclusion."""

from __future__ import annotations

import pytest

from app.modules.integration_hub.conflict_policy import (
    ConflictResolutionPolicy,
    FeedbackLoopExclusionError,
    assert_no_feedback_loop_pull,
    filter_mappings_for_pull,
    policy_from_row,
    pull_excluded_fields,
)
from app.modules.integration_hub.field_mapping import FieldMapEntry, parse_field_mappings


def test_default_policy_excludes_salesos_authored_from_pull() -> None:
    policy = ConflictResolutionPolicy.default()
    banned = pull_excluded_fields(policy)
    assert "risk_score" in banned
    assert "ai_score" in banned
    assert "name" not in banned


def test_write_back_feedback_loop_exclusion_dedicated() -> None:
    """AC: SalesOS-authored fields never read back as fresh source data."""
    policy = ConflictResolutionPolicy.default()
    mappings = parse_field_mappings(
        [
            {"internal": "name", "external": "display_name", "direction": "pull"},
            {"internal": "risk_score", "external": "x_ai_risk", "direction": "pull"},
            {"internal": "ai_score", "external": "x_studio_ai_score", "direction": "bidirectional"},
        ]
    )
    with pytest.raises(FeedbackLoopExclusionError, match="risk_score"):
        assert_no_feedback_loop_pull(mappings, policy)

    filtered = filter_mappings_for_pull(mappings, policy)
    internals = {e.internal: e.direction for e in filtered}
    assert internals["name"] == "pull"
    assert "risk_score" not in internals
    # bidirectional AI field forced to push-only (write-back ok, pull blocked)
    assert internals["ai_score"] == "push"
    assert_no_feedback_loop_pull(filtered, policy)


def test_policy_from_row_forces_salesos_exclude() -> None:
    policy = policy_from_row(
        rules=[{"internal": "risk_score", "winner": "source", "exclude_from_pull": False}],
        salesos_authored_fields=["risk_score"],
        operational_fields=["name"],
    )
    rule = next(r for r in policy.rules if r.internal == "risk_score")
    assert rule.winner == "salesos"
    assert rule.exclude_from_pull is True


def test_filter_keeps_push_only_authored_fields() -> None:
    policy = ConflictResolutionPolicy.default()
    entries = (
        FieldMapEntry(internal="ai_score", external="x_ai", direction="push"),
        FieldMapEntry(internal="email", external="email_from", direction="pull"),
    )
    filtered = filter_mappings_for_pull(entries, policy)
    assert len(filtered) == 2
    assert_no_feedback_loop_pull(filtered, policy)
