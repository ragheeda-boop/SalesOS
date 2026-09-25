import pytest

from domains.workflow.outcome_contract import OutcomeStatus, WorkflowOutcome, transition_outcome


def test_workflow_outcome_requires_idempotency_and_result_link():
    started = WorkflowOutcome("ex-1", "idem-1", OutcomeStatus.STARTED, "create_task")
    completed = transition_outcome(started, OutcomeStatus.COMPLETED, result_ref="task-1")
    assert completed.result_ref == "task-1"
    assert transition_outcome(completed, OutcomeStatus.COMPLETED) == completed
    with pytest.raises(ValueError, match="terminal"):
        transition_outcome(completed, OutcomeStatus.FAILED, error_code="late")


def test_failed_outcome_requires_error_code():
    started = WorkflowOutcome("ex-1", "idem-1", OutcomeStatus.STARTED, "sync")
    with pytest.raises(ValueError, match="error code"):
        transition_outcome(started, OutcomeStatus.FAILED)
