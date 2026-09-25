"""Unit tests for the review-only Domain Correction classifier."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = BACKEND_ROOT / "scripts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_reach_domain_correction_review import (  # noqa: E402
    CLASS_CORRECTED,
    CLASS_HUMAN,
    CLASS_NONE,
    EXPECTED_QUEUE_COUNT,
    HIGH_CORRECTIONS,
    INPUT_QUEUE_NAME,
    REVIEW_HEADERS,
    assert_safe_output_dir,
    build_domain_correction_review,
    classify_account,
)

QUEUE_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "quality_categories",
    "issue_evidence",
]


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_HEADERS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _queue_row(
    account_id: str,
    domain: str,
    *,
    name: str = "Acme",
    categories: str = "typo_domain",
    evidence: str = "invalid host",
) -> dict[str, str]:
    return {
        "Master Account ID": account_id,
        "company_name": name,
        "tier": "TIER C - CS QUALIFIED",
        "tier_bucket": "TIER C",
        "primary_domain": domain,
        "quality_categories": categories,
        "issue_evidence": evidence,
    }


def test_high_confidence_merck_uses_official_group_domain() -> None:
    result = classify_account(
        _queue_row(
            "MA-0001268",
            "alahli.com.sa",
            name="شركة ميرك كي جي_الرياض",
            categories="invalid_or_generic_domain",
        )
    )
    assert result.classification == CLASS_CORRECTED
    assert result.corrected_domain == "merckgroup.com"
    assert result.confidence == "high"
    assert result.agent_reach_eligible is True


def test_truncated_saudi_re_repairs_to_official_net() -> None:
    result = classify_account(_queue_row("MA-0110687", "saudire.ne"))
    assert result.classification == CLASS_CORRECTED
    assert result.corrected_domain == "saudire.net"
    assert result.agent_reach_eligible is True


def test_british_embassy_is_corrected_but_not_agent_reach() -> None:
    result = classify_account(
        _queue_row(
            "MA-0047607",
            "ukinsaudiarabia.fco.gov.uk",
            categories="government_domain",
        )
    )
    assert result.classification == CLASS_CORRECTED
    assert result.corrected_domain == "gov.uk"
    assert result.agent_reach_eligible is False


def test_consumer_email_typo_is_not_a_company_site() -> None:
    result = classify_account(_queue_row("MA-0076888", "icoloud.com"))
    assert result.classification == CLASS_NONE
    assert result.corrected_domain == ""
    assert result.agent_reach_eligible is False


def test_government_host_on_private_account_is_not_replaced() -> None:
    result = classify_account(
        _queue_row(
            "MA-0207192",
            "momra.gov.sa",
            categories="government_domain",
        )
    )
    assert result.classification == CLASS_NONE
    assert result.corrected_domain == ""


def test_nbb_dual_official_hosts_need_human_review() -> None:
    result = classify_account(
        _queue_row(
            "MA-0001240",
            "nbb.com.bh",
            categories="invalid_or_generic_domain",
        )
    )
    assert result.classification == CLASS_HUMAN
    assert result.corrected_domain == ""


def test_nupco_existing_official_is_not_replaced() -> None:
    result = classify_account(
        _queue_row(
            "MA-0260590",
            "nupco.com",
            categories="government_domain",
        )
    )
    assert result.classification == CLASS_NONE
    assert "already official" in result.reason.lower()


def test_random_garbage_host_is_no_safe_correction() -> None:
    result = classify_account(_queue_row("MA-0204147", "hvvgh.comh"))
    assert result.classification == CLASS_NONE
    assert result.corrected_domain == ""


def test_assert_safe_output_dir_rejects_input_plan_dir(tmp_path: Path) -> None:
    queue = tmp_path / INPUT_QUEUE_NAME
    queue.write_text("Master Account ID\nMA-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="input plan directory"):
        assert_safe_output_dir(tmp_path, queue)


def test_build_review_writes_204_and_isolated_ar_queue(tmp_path: Path) -> None:  # noqa: PLR0915
    input_dir = tmp_path / "input_plan"
    output_dir = tmp_path / "20260907T999999Z_domain_correction_review"
    shared_report = tmp_path / "DOMAIN_CORRECTION_REVIEW_REPORT.md"
    queue = input_dir / INPUT_QUEUE_NAME

    rows = []
    curated = [
        _queue_row("MA-0001268", "alahli.com.sa", name="Merck"),
        _queue_row("MA-0110687", "saudire.ne", name="Saudi Re"),
        _queue_row(
            "MA-0047607",
            "ukinsaudiarabia.fco.gov.uk",
            name="British Embassy",
            categories="government_domain",
        ),
        _queue_row("MA-0001240", "nbb.com.bh", name="NBB"),
        _queue_row("MA-0076888", "icoloud.com", name="Dreams"),
    ]
    rows.extend(curated)
    while len(rows) < EXPECTED_QUEUE_COUNT:
        index = len(rows) + 1
        rows.append(_queue_row(f"MA-PAD{index:04d}", f"rand{index}.comh"))
    _write_queue(queue, rows)

    master = tmp_path / "master.csv"
    with master.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Master Account ID",
                "Primary_Email",
                "All_Domains",
                "City",
                "has_phone",
                "has_social",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "Master Account ID": "MA-0001268",
                "Primary_Email": "abdullah.aldamkh@merckgroup.com",
                "All_Domains": "alahli.com.sa",
                "City": "الرياض",
                "has_phone": "false",
                "has_social": "false",
            }
        )

    stats = build_domain_correction_review(
        input_queue=queue,
        output_dir=output_dir,
        shared_report=shared_report,
        master_csv=master,
    )
    expected_corrected = 3
    expected_human = 1
    expected_none = EXPECTED_QUEUE_COUNT - expected_corrected - expected_human
    expected_ar = 2
    assert stats["queue_count"] == EXPECTED_QUEUE_COUNT
    assert stats["corrected_domain_found"] == expected_corrected
    assert stats["needs_human_review"] == expected_human
    assert stats["no_safe_correction"] == expected_none
    assert stats["agent_reach_run"] == "false"
    assert stats["phase_7_started"] is False

    review_path = output_dir / "domain_corrections_review_only.csv"
    with review_path.open("r", encoding="utf-8-sig", newline="") as handle:
        review_rows = list(csv.DictReader(handle))
    assert list(review_rows[0].keys()) == REVIEW_HEADERS
    assert len(review_rows) == EXPECTED_QUEUE_COUNT
    by_id = {row["Master Account ID"]: row for row in review_rows}
    assert by_id["MA-0001268"]["classification"] == CLASS_CORRECTED
    assert by_id["MA-0001268"]["corrected_domain"] == "merckgroup.com"
    assert by_id["MA-0001268"]["master_email"] == "abdullah.aldamkh@merckgroup.com"
    assert by_id["MA-0047607"]["agent_reach_eligible"] == "false"
    assert by_id["MA-0001240"]["classification"] == CLASS_HUMAN
    assert by_id["MA-0076888"]["classification"] == CLASS_NONE

    with (output_dir / "domain_corrections_agent_reach_queue.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        ar_rows = list(csv.DictReader(handle))
    ar_ids = {row["account_id"] for row in ar_rows}
    ar_domains = {row["domain"] for row in ar_rows}
    assert ar_ids == {"MA-0001268", "MA-0110687"}
    assert "gov.uk" not in ar_domains
    assert "merckgroup.com" in ar_domains
    assert "saudire.net" in ar_domains

    unresolved_path = output_dir / "domain_corrections_unresolved.csv"
    with unresolved_path.open("r", encoding="utf-8-sig", newline="") as handle:
        unresolved = list(csv.DictReader(handle))
    assert len(unresolved) == expected_none + expected_human
    assert all(
        row["classification"] in {CLASS_HUMAN, CLASS_NONE} for row in unresolved
    )

    report = (output_dir / "DOMAIN_CORRECTION_REVIEW_REPORT.md").read_text(encoding="utf-8")
    assert report == shared_report.read_text(encoding="utf-8")
    assert "DOMAIN CORRECTION REVIEW QUEUE CREATED" in report
    assert "NO MASTER OVERWRITE" in report
    assert "PHASE 7 NOT STARTED" in report
    assert queue.exists()
    plan = json.loads((output_dir / "plan.json").read_text(encoding="utf-8"))
    assert plan["pending_queue_total"] == expected_ar
    assert len(HIGH_CORRECTIONS) >= len(ar_ids)
