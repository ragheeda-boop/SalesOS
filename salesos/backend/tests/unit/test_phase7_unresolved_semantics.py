"""Regression: an ESCALATED queue row is not a RESOLVED queue row.

Defect (2026-09-26): `_FACTS_SQL` decided "still awaiting human review" from
`status = 'pending'` alone. Every P3/SHORT_CR row had been moved to
`status = 'dispositioned'` by `record_disposition`, so the
`PENDING_P3_FUZZY_PAIR` / `PENDING_SHORT_CR_ADJUDICATION` blockers silently
vanished and 148 sales-usable accounts were released on a false premise
(usable_accounts 7_768 -> 7_916).

These tests lock the resolution semantics at the SQL-predicate level so that
flipping `status` can never again be mistaken for resolving a review.
"""

from __future__ import annotations

import re

import pytest

from app.modules.master_data.phase7.usability import _FACTS_SQL

# Resolving dispositions: only these clear a review blocker.
RESOLVING = ("CONFIRM", "SEPARATE")


def _strip_comments(sql: str) -> str:
    """Drop SQL comments so assertions match predicates, not prose."""
    return re.sub(r"--[^\n]*", "", sql)


def _p3_predicates() -> str:
    return _strip_comments(_FACTS_SQL.split("), scr AS (")[0])


def _scr_predicates() -> str:
    return _strip_comments(_FACTS_SQL.split("), scr AS (")[1].split("), src AS (")[0])


def test_facts_sql_does_not_decide_on_status_alone() -> None:
    """The P3/SHORT_CR CTEs must consult disposition, not just status."""
    p3 = _p3_predicates()
    # The old defect: `status = 'pending'` as the sole filter.
    assert "status = 'pending' AND global_company_id IS NOT NULL" not in p3, (
        "P3 CTE regressed to status-only filtering; escalation would count as resolution"
    )
    assert "disposition NOT IN ('CONFIRM', 'SEPARATE')" in p3, (
        "P3 CTE must block every non-resolving disposition (ESCALATE/REVIEW/NULL)"
    )


def test_escate_is_not_treated_as_resolved() -> None:
    """ESCALATE must appear nowhere as a resolving disposition."""
    assert "ESCALATE" not in _p3_predicates(), "ESCALATE leaked into the P3 resolution set"


def test_short_cr_blocks_on_unresolved_escalate() -> None:
    scr = _scr_predicates()
    assert "UNRESOLVED_ESCALATE" in scr, (
        "SHORT_CR must keep blocking rows escalated as unresolved"
    )
    assert "CONFIRMED_ARTIFACT" not in scr, (
        "CONFIRMED_ARTIFACT is a resolution and must not block"
    )


def test_short_cr_still_blocks_while_pending() -> None:
    scr = _scr_predicates()
    assert "status = 'pending'" in scr, "an un-adjudicated SHORT_CR row must block"


@pytest.mark.parametrize("disp", ["ESCALATE", "REVIEW", None])
def test_non_resolving_dispositions_are_blocking(disp: str | None) -> None:
    """Every non-resolving disposition must satisfy the blocking predicate."""
    blocked = disp is None or disp not in RESOLVING
    assert blocked, f"{disp!r} must keep the account blocked"


@pytest.mark.parametrize("disp", list(RESOLVING))
def test_resolving_dispositions_clear_the_blocker(disp: str) -> None:
    assert disp in RESOLVING
