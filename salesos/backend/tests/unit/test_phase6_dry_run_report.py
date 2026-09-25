"""Safety checks for the Phase 6 dry-run report helper."""

import pytest

from scripts.phase6_dry_run import reconcile_streamed_result, write_human_report

EXPECTED_IDENTITY_CHANGE_ROWS = 2


def test_report_fails_closed_and_displays_unknown_safety_counters(tmp_path):
    report_path = tmp_path / "phase6-report.md"
    result = {
        "summary": {},
        "staged": {},
        "safety": {"unmapped_master_account_without_global_company_id": 1},
        "change_count": 0,
    }

    all_zero = write_human_report(report_path, result, [], max_accounts=None)

    assert all_zero is False
    report = report_path.read_text(encoding="utf-8")
    assert "unmapped_master_account_without_global_company_id" in report
    assert "| 1 | FAIL |" in report


def test_streamed_artifact_counts_reconcile_to_pipeline_output():
    result = {"change_count": 3}
    table_counts = {
        "md_identity_classifications": EXPECTED_IDENTITY_CHANGE_ROWS,
        "md_review_candidates": 1,
    }

    reconcile_streamed_result(result, table_counts)

    assert (
        result["staged"]["identity_classifications"]
        == EXPECTED_IDENTITY_CHANGE_ROWS
    )
    assert result["staged"]["review_candidates"] == 1
    assert result["staged"]["contact_relationships"] == 0
    assert result["database_transaction"] == "READ ONLY"


def test_streamed_artifact_mismatch_fails_closed():
    with pytest.raises(RuntimeError, match="does not reconcile"):
        reconcile_streamed_result({"change_count": 2}, {"md_review_candidates": 1})
