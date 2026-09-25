"""Unit tests for the review-only missing-data completion plan helper."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = BACKEND_ROOT / "scripts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_final_closure import (  # noqa: E402
    BACKLOG_HEADERS,
    METHOD_DOMAIN,
    METHOD_EXTERNAL,
    METHOD_HUMAN,
    METHOD_INSUFFICIENT,
    SUMMARY_HEADERS,
)
from agent_reach_missing_data_completion_plan import (  # noqa: E402
    PILOT_SLICE_SIZE,
    assert_safe_output_dir,
    build_completion_plan,
    classify_unattempted_remainder,
    recommended_action_for_categories,
    split_backlog_by_method,
    why_agent_reach_cannot_finish,
    why_human_review,
)


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _backlog_row(  # noqa: PLR0913
    account_id: str,
    method: str,
    *,
    name: str = "Acme",
    tier: str = "TIER C - CS QUALIFIED",
    bucket: str = "TIER C",
    domain: str = "acme.com",
    usable: str = "true",
    attempted: str = "true",
    status: str = "QUALITY_BACKLOG",
    categories: str = "no_contact_found",
    notes: str = "agent_reach_already_attempted;QUALITY_BACKLOG",
) -> dict[str, str]:
    return {
        "Master Account ID": account_id,
        "company_name": name,
        "tier": tier,
        "tier_bucket": bucket,
        "primary_domain": domain,
        "usable_domain": usable,
        "attempted_agent_reach": attempted,
        "enrichment_status": status,
        "missing_phone": "true",
        "missing_whatsapp": "true",
        "missing_linkedin": "true",
        "missing_other_social": "true",
        "invalid_dead_or_mismatch_site": "false",
        "quality_issues_only": "true",
        "no_recoverable_website_social_evidence": "true",
        "quality_categories": categories,
        "next_method": method,
        "notes": notes,
    }


def test_split_backlog_by_method():
    rows = [
        _backlog_row("MA-1", METHOD_DOMAIN, categories="typo_domain"),
        _backlog_row("MA-2", METHOD_HUMAN, categories="company_domain_mismatch"),
        _backlog_row("MA-3", METHOD_EXTERNAL),
        _backlog_row("MA-4", METHOD_INSUFFICIENT, attempted="false", categories=""),
    ]
    buckets = split_backlog_by_method(rows)
    assert [row["Master Account ID"] for row in buckets[METHOD_DOMAIN]] == ["MA-1"]
    assert [row["Master Account ID"] for row in buckets[METHOD_HUMAN]] == ["MA-2"]
    assert [row["Master Account ID"] for row in buckets[METHOD_EXTERNAL]] == ["MA-3"]
    assert [row["Master Account ID"] for row in buckets[METHOD_INSUFFICIENT]] == ["MA-4"]


def test_recommended_action_and_why_text():
    assert "typo" in recommended_action_for_categories({"typo_domain"}).lower()
    human = why_human_review(
        _backlog_row("MA-2", METHOD_HUMAN, categories="company_domain_mismatch")
    )
    assert "re-fetch" in human.lower() or "re-fetch" in human
    external = why_agent_reach_cannot_finish(_backlog_row("MA-3", METHOD_EXTERNAL))
    assert "already fetched" in external.lower() or "already attempted" in external.lower()
    skipped = why_agent_reach_cannot_finish(
        _backlog_row("MA-9", METHOD_EXTERNAL, attempted="false", categories="")
    )
    assert "separate approval" in skipped.lower()


def test_classify_unattempted_remainder():
    counts = {"goodco.com": 1, "shared.com": 80}
    assert (
        classify_unattempted_remainder(
            domain="goodco.com",
            domain_counts=counts,
            master_has_phone=True,
            master_has_social=True,
        )
        == METHOD_EXTERNAL
    )
    assert (
        classify_unattempted_remainder(
            domain="",
            domain_counts=counts,
            master_has_phone=False,
            master_has_social=False,
        )
        == METHOD_INSUFFICIENT
    )


def test_refuse_write_inside_closure_dir(tmp_path: Path):
    closure = tmp_path / "20260907T052756Z_final_closure"
    closure.mkdir()
    with pytest.raises(ValueError, match="final-closure"):
        assert_safe_output_dir(closure, closure)
    with pytest.raises(ValueError, match="final-closure"):
        assert_safe_output_dir(closure / "nested", closure)


def test_build_completion_plan_from_tiny_closure(tmp_path: Path):
    closure = tmp_path / "closure"
    output = tmp_path / "20260907T120000Z_missing_data_completion_plan"
    report = tmp_path / "MISSING_DATA_COMPLETION_PLAN.md"
    _write_csv(
        closure / "missing_data_backlog.csv",
        BACKLOG_HEADERS,
        [
            _backlog_row(
                "MA-D1",
                METHOD_DOMAIN,
                bucket="TIER C",
                domain="brand.vom",
                categories="typo_domain",
            ),
            _backlog_row(
                "MA-H1",
                METHOD_HUMAN,
                bucket="TIER B",
                tier="TIER B",
                categories="company_domain_mismatch",
            ),
            _backlog_row("MA-E1", METHOD_EXTERNAL, bucket="CLASS A", tier="CLASS A"),
            _backlog_row(
                "MA-P1",
                METHOD_INSUFFICIENT,
                attempted="false",
                usable="false",
                domain="",
                categories="",
            ),
        ],
    )
    _write_csv(
        closure / "missing_data_backlog_summary.csv",
        SUMMARY_HEADERS,
        [
            {
                "tier_bucket": "TIER C",
                "next_method": METHOD_DOMAIN,
                "accounts": "1",
                "missing_phone": "1",
                "missing_whatsapp": "1",
                "missing_linkedin": "1",
                "missing_other_social": "1",
                "invalid_dead_or_mismatch_site": "0",
                "quality_issues_only": "1",
                "no_recoverable_website_social_evidence": "0",
                "attempted_agent_reach": "1",
            }
        ],
    )
    _write_csv(
        closure / "master_quality_issues_patch.csv",
        [
            "Master Account ID",
            "company_name",
            "domain",
            "issue",
            "issue_category",
            "recommended_action",
        ],
        [
            {
                "Master Account ID": "MA-D1",
                "company_name": "Acme",
                "domain": "brand.vom",
                "issue": "لاحقة غير حقيقية .vom",
                "issue_category": "typo_domain",
                "recommended_action": "Review Primary_Domain",
            }
        ],
    )
    for name in (
        "missing_phone.csv",
        "missing_whatsapp.csv",
        "missing_linkedin.csv",
        "missing_other_social.csv",
        "invalid_dead_mismatch_sites.csv",
        "quality_issues_only.csv",
        "no_recoverable_evidence.csv",
    ):
        _write_csv(closure / name, BACKLOG_HEADERS, [_backlog_row("MA-E1", METHOD_EXTERNAL)])

    _write_csv(
        closure / "01_Master_Accounts_enriched_review_only.csv",
        [
            "Master Account ID",
            "Primary_Domain",
            "Primary_Phone",
            "Canonical_Company_Name",
            "Account_Tier_v2",
            "has_phone",
            "has_social",
        ],
        [
            {
                "Master Account ID": "MA-D1",
                "Primary_Domain": "brand.vom",
                "Primary_Phone": "",
                "Canonical_Company_Name": "Acme",
                "Account_Tier_v2": "TIER C - CS QUALIFIED",
                "has_phone": "false",
                "has_social": "false",
            },
            {
                "Master Account ID": "MA-SKIP1",
                "Primary_Domain": "skipco.com",
                "Primary_Phone": "+966500000001",
                "Canonical_Company_Name": "Skip Co",
                "Account_Tier_v2": "TIER B",
                "has_phone": "true",
                "has_social": "true",
            },
            {
                "Master Account ID": "MA-PARK2",
                "Primary_Domain": "",
                "Primary_Phone": "",
                "Canonical_Company_Name": "Parked Co",
                "Account_Tier_v2": "TIER D - NURTURE",
                "has_phone": "false",
                "has_social": "false",
            },
        ],
    )

    stats = build_completion_plan(
        closure_dir=closure,
        output_dir=output,
        report_path=report,
    )
    counts = stats["queue_counts"]
    expected_external = 2
    expected_parked = 2
    assert counts["domain_correction"] == 1
    assert counts["human_review"] == 1
    assert counts["external_source"] == expected_external
    assert counts["parked_no_evidence"] == expected_parked
    assert stats["phase_7_started"] is False
    assert stats["external_apis_called"] is False

    domain_path = output / "domain_correction_review_queue.csv"
    with domain_path.open("r", encoding="utf-8-sig", newline="") as handle:
        domain_rows = list(csv.DictReader(handle))
    assert domain_rows[0]["Master Account ID"] == "MA-D1"
    assert ".vom" in domain_rows[0]["issue_evidence"]
    assert "original master" in domain_rows[0]["recommended_action"]

    with (output / "external_source_candidate_queue.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        external_rows = list(csv.DictReader(handle))
    assert {row["Master Account ID"] for row in external_rows} == {"MA-E1", "MA-SKIP1"}
    assert all(row["external_approval_required"] == "true" for row in external_rows)
    assert sum(row["suggested_pilot_slice"] == "true" for row in external_rows) <= PILOT_SLICE_SIZE

    with (output / "parked_no_evidence_accounts.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        parked_ids = {row["Master Account ID"] for row in csv.DictReader(handle)}
    assert parked_ids == {"MA-P1", "MA-PARK2"}

    text = report.read_text(encoding="utf-8")
    copied = (output / "MISSING_DATA_COMPLETION_PLAN.md").read_text(encoding="utf-8")
    assert text == copied
    assert "PHASE 7 NOT STARTED" in text
    assert "NO PRODUCTION WRITES" in text
    assert "separate approval" in text.lower()
    assert not (closure / "domain_correction_review_queue.csv").exists()
