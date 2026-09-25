"""Idempotent workflow outcome contract for automation measurement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OutcomeStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True)
class WorkflowOutcome:
    execution_id: str
    idempotency_key: str
    status: OutcomeStatus
    action: str
    result_ref: str | None = None
    error_code: str | None = None


def transition_outcome(current: WorkflowOutcome, target: OutcomeStatus, *, result_ref: str | None = None, error_code: str | None = None) -> WorkflowOutcome:
    if not current.execution_id or not current.idempotency_key:
        raise ValueError("execution_id and idempotency_key are required")
    if current.status in {OutcomeStatus.COMPLETED, OutcomeStatus.EXHAUSTED}:
        if target != current.status:
            raise ValueError("terminal workflow outcomes cannot transition")
        return current
    if target == OutcomeStatus.COMPLETED and not result_ref:
        raise ValueError("completed outcomes require a result reference")
    if target in {OutcomeStatus.FAILED, OutcomeStatus.EXHAUSTED} and not error_code:
        raise ValueError("failed outcomes require an error code")
    return WorkflowOutcome(current.execution_id, current.idempotency_key, target, current.action, result_ref, error_code)
