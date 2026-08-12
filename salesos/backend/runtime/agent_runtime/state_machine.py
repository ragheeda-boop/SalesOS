"""
Agent State Machine — valid transitions and fencing guards.

Enforces:
  - Only valid status transitions
  - Fencing: lease_generation check on every worker-originated mutation
  - INV-03: fencing + mutation must be atomic
"""
from __future__ import annotations

VALID_TRANSITIONS: dict[str, set[str]] = {
    # Duplicate "PENDING" key previously overwrote CLAIMED with EXHAUSTED only.
    "PENDING":            {"CLAIMED", "EXHAUSTED"},
    "CLAIMED":            {"RUNNING", "PENDING"},
    "RUNNING":            {"COMPLETED", "FAILED", "REQUIRES_APPROVAL", "PENDING"},
    "REQUIRES_APPROVAL":  {"PENDING"},
    "FAILED":             {"PENDING", "EXHAUSTED"},
}

TERMINAL_STATUSES = frozenset({"COMPLETED", "EXHAUSTED"})


def is_valid_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES


def is_worker_recoverable(status: str) -> bool:
    return status in ("CLAIMED", "RUNNING")


def requires_fencing(status: str) -> bool:
    return status in ("CLAIMED", "RUNNING")


ALL_STATUSES = frozenset({
    "PENDING", "CLAIMED", "RUNNING", "REQUIRES_APPROVAL",
    "COMPLETED", "FAILED", "EXHAUSTED",
})

COMPLETION_REASONS = frozenset({
    "SUCCESS", "PARTIAL_BUDGET", "PARTIAL_DATA", "NO_ACTION_REQUIRED",
})
