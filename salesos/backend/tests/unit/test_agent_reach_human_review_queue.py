"""Unit tests for the review-only Human Review Queue builder."""

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

from agent_reach_human_review_queue import (  # noqa: E402
    CONF_HIGH,
    CONF_MEDIUM,
    DECIDE_APPROVE,
    DECIDE_DOMAIN_FIX,
    DECIDE_PARK,
    DECIDE_REJECT,
    EXPECTED_DOMAIN_HUMAN_COUNT,
    EXPECTED_ORIGINAL_COUNT,
    SOURCE_DOMAIN,
    SOURCE_ORIGINAL,
    assert_safe_output_dir,
    build_human_review_queue,
    clear_name_domain_overlap,
    is_homepage_social,
    is_unresolved,
    load_domain_human_rows,
    propose_decision,
    union_account_ids,
    usable_ready_values,
)

HUMAN_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "primary_domain",
    "usable_domain",
    "attempted_agent_reach",
    "enrichment_status",
    "quality_categories",
    "issue_evidence",
    "why_human_review",
    "recommended_action",
]
DOMAIN_HEADERS = [
    "Master Account ID",
    "company_name",
    "tier",
    "tier_bucket",
    "old_domain",
    "classification",
    "corrected_domain",
    "evidence_source",
    "confidence",
    "reason",
    "quality_categories",
    "issue_evidence",
]
PATCH_HEADERS = [
    "Master Account ID",
    "company_name",
    "source_domain",
    "tier",
    "field_type",
    "value",
    "source_method",
    "review_status",
    "quality_flag",
    "notes",
]


def _write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _human_row(  # noqa: PLR0913
    account_id: str,
    domain: str,
    *,
    name: str = "Acme",
    status: str = "QUALITY_BACKLOG",
    categories: str = "company_domain_mismatch",
    evidence: str = "domain belongs to another company",
) -> dict[str, str]:
    return {
        "Master Account ID": account_id,
        "company_name": name,
        "tier": "TIER C - CS QUALIFIED",
        "tier_bucket": "TIER C",
        "primary_domain": domain,
        "usable_domain": "true",
        "attempted_agent_reach": "true",
        "enrichment_status": status,
        "quality_categories": categories,
        "issue_evidence": evidence,
        "why_human_review": "Quality flags require a human decision.",
        "recommended_action": "Review on a copy only.",
    }


def _domain_row(
    account_id: str,
    domain: str,
    *,
    name: str = "Acme",
    classification: str = "needs_human_review",
) -> dict[str, str]:
    return {
        "Master Account ID": account_id,
        "company_name": name,
        "tier": "TIER C - CS QUALIFIED",
        "tier_bucket": "TIER C",
        "old_domain": domain,
        "classification": classification,
        "corrected_domain": "",
        "evidence_source": "two official hosts remain plausible",
        "confidence": "medium",
        "reason": "Human must choose which host to keep.",
        "quality_categories": "invalid_or_generic_domain",
        "issue_evidence": "not unique enough",
    }


def test_union_keeps_original_and_adds_new_domain_ids() -> None:
    original = [_human_row("MA-0000001", "a.com"), _human_row("MA-0000002", "b.com")]
    domain = [_domain_row("MA-0000002", "b.com"), _domain_row("MA-0000999", "c.com")]
    ordered, sources = union_account_ids(original, domain)
    assert ordered == ["MA-0000001", "MA-0000002", "MA-0000999"]
    assert sources["MA-0000001"] == SOURCE_ORIGINAL
    assert sources["MA-0000002"] == SOURCE_ORIGINAL
    assert sources["MA-0000999"] == SOURCE_DOMAIN


def test_hijacked_domain_is_rejected() -> None:
    decision = propose_decision(
        _human_row(
            "MA-0000697",
            "creative-academy.net",
            categories="hijacked_or_compromised",
            evidence="الموقع مخترق ويعرض محتوى قمار",
        ),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_REJECT
    assert decision.confidence == CONF_HIGH


def test_mismatch_domain_is_rejected() -> None:
    decision = propose_decision(
        _human_row("MA-0000426", "domain.com"),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_REJECT
    assert decision.confidence == CONF_HIGH


def test_garbage_placeholder_domain_is_rejected() -> None:
    decision = propose_decision(
        _human_row(
            "MA-0000536",
            "nfnzpb.pbz",
            categories="placeholder_or_fake",
            evidence="نطاق غير حقيقي/امتداد وهمي (gibberish)",
        ),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_REJECT
    assert decision.confidence == CONF_HIGH


def test_fake_phone_on_non_garbage_domain_is_parked() -> None:
    decision = propose_decision(
        _human_row(
            "MA-0253537",
            "tofm.com.sa",
            categories="placeholder_or_fake",
            evidence="الرقم المستخرج (+1 555 234-8765) هو رقم أمريكي وهمي",
        ),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_PARK
    assert is_unresolved(decision)


def test_global_parent_same_brand_is_parked() -> None:
    decision = propose_decision(
        _human_row(
            "MA-0093954",
            "averda.com",
            name="شركة افيردا السعودية",
            categories="global_parent_domain",
            evidence="النطاق يمثل شركة عالمية كبرى لإدارة النفايات",
        ),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_PARK
    assert decision.confidence == CONF_MEDIUM


def test_unrelated_global_host_is_rejected() -> None:
    decision = propose_decision(
        _human_row(
            "MA-0006520",
            "clerk.com",
            name="مؤسسة رشا عثمان",
            categories="global_parent_domain",
            evidence="الموقع يعرض شركة برمجيات عالمية لا علاقة لها بالمنشأة المسجلة",
        ),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_REJECT
    assert decision.confidence == CONF_HIGH


def test_domain_correction_human_is_parked() -> None:
    decision = propose_decision(
        _domain_row("MA-0001240", "nbb.com.bh", name="بنك البحرين الوطني ش م ب"),
        source=SOURCE_DOMAIN,
    )
    assert decision.proposed_decision == DECIDE_PARK
    assert decision.confidence == CONF_MEDIUM
    assert is_unresolved(decision)


def test_high_correction_requests_domain_fix() -> None:
    decision = propose_decision(
        _human_row("MA-0001268", "alahli.com.sa", name="شركة ميرك كي جي_الرياض"),
        source=SOURCE_ORIGINAL,
    )
    assert decision.proposed_decision == DECIDE_DOMAIN_FIX
    assert decision.suggested_domain_or_values == "merckgroup.com"
    assert decision.confidence == CONF_HIGH


def test_pending_review_high_when_name_overlaps_domain() -> None:
    values = [
        {
            "source_domain": "qelaaj.sa",
            "field_type": "لينكدإن",
            "value": "https://www.linkedin.com/company/qelaaj",
            "quality_flag": "ok",
        }
    ]
    decision = propose_decision(
        _human_row(
            "MA-0001105",
            "qelaaj.sa",
            name="شركة قلاع الجزيرة qelaaj",
            status="PENDING_REVIEW",
            categories="",
            evidence="",
        ),
        source=SOURCE_ORIGINAL,
        values=values,
    )
    assert decision.proposed_decision == DECIDE_APPROVE
    assert decision.confidence == CONF_HIGH


def test_pending_review_medium_without_name_overlap() -> None:
    values = [
        {
            "source_domain": "tnugroup.com",
            "field_type": "انستقرام",
            "value": "instagram.com/tnugroup_sa",
            "quality_flag": "ok",
        }
    ]
    decision = propose_decision(
        _human_row(
            "MA-0000024",
            "tnugroup.com",
            name="شركة تجارية بدون تطابق لاتيني",
            status="PENDING_REVIEW",
            categories="",
            evidence="",
        ),
        source=SOURCE_ORIGINAL,
        values=values,
    )
    assert decision.proposed_decision == DECIDE_APPROVE
    assert decision.confidence == CONF_MEDIUM
    assert is_unresolved(decision)


def test_homepage_socials_are_not_usable() -> None:
    values = [
        {
            "source_domain": "acme.com",
            "field_type": "تويتر/X",
            "value": "/x.com",
            "quality_flag": "ok",
        }
    ]
    assert usable_ready_values(values, "acme.com") == []
    assert is_homepage_social("/twitter.com")
    assert not is_homepage_social("https://twitter.com/intra_sa")


def test_clear_name_domain_overlap_requires_a_real_label() -> None:
    assert clear_name_domain_overlap("شركة قلاع الجزيرة qelaaj", "qelaaj.sa")
    assert not clear_name_domain_overlap("مؤسسة سلسبيل للمواد الغذائية", "the-skystar.com")


def test_altawi_ready_with_issues_is_approved() -> None:
    values = [
        {
            "source_domain": "altawi.org",
            "field_type": "تويتر/X",
            "value": "https://x.com/altawi1978",
            "quality_flag": "needs_review",
        }
    ]
    decision = propose_decision(
        _human_row(
            "MA-0213575",
            "altawi.org",
            name="مؤسسة خالد مشرف أحمد طاوي للمقاولات العامة",
            status="READY_WITH_ISSUES",
            categories="other",
            evidence="trailing markdown stripped",
        ),
        source=SOURCE_ORIGINAL,
        values=values,
    )
    assert decision.proposed_decision == DECIDE_APPROVE
    assert decision.confidence == CONF_HIGH


def test_absher_lookalike_is_rejected() -> None:
    decision = propose_decision(
        _human_row(
            "MA-0217631",
            "abshersetup.ae",
            name="شركة ميديا ميكرز",
            status="READY_WITH_ISSUES",
            categories="other",
            evidence="unrelated LinkedIn platform footer absher-business",
        ),
        source=SOURCE_ORIGINAL,
        values=[],
    )
    assert decision.proposed_decision == DECIDE_REJECT


def test_assert_safe_output_dir_rejects_input_and_forbidden(tmp_path: Path) -> None:
    queue = tmp_path / "human_review_queue.csv"
    queue.write_text("Master Account ID\nMA-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="input plan directory"):
        assert_safe_output_dir(tmp_path, queue)
    forbidden = tmp_path / "20260907T052756Z_final_closure"
    forbidden.mkdir()
    with pytest.raises(ValueError, match="prior dir"):
        assert_safe_output_dir(forbidden, queue)


def test_load_domain_human_rows_requires_seven(tmp_path: Path) -> None:
    path = tmp_path / "domain_corrections_review_only.csv"
    _write_csv(path, DOMAIN_HEADERS, [_domain_row("MA-1", "a.com")])
    with pytest.raises(ValueError, match="needs_human_review"):
        load_domain_human_rows(path)


def test_build_writes_unified_queue_and_patch(tmp_path: Path) -> None:
    input_dir = tmp_path / "input_plan"
    output_dir = tmp_path / "20260907T999999Z_human_review_queue"
    shared = tmp_path / "HUMAN_REVIEW_QUEUE_REPORT.md"
    human_path = input_dir / "human_review_queue.csv"
    domain_path = input_dir / "domain_corrections_review_only.csv"
    patch_path = input_dir / "master_enrichment_patch.csv"

    human_rows = [
        _human_row(f"MA-H{index:04d}", f"mismatch{index}.com")
        for index in range(EXPECTED_ORIGINAL_COUNT - 4)
    ]
    human_rows.extend(
        [
            _human_row(
                "MA-0000697",
                "creative-academy.net",
                categories="hijacked_or_compromised",
                evidence="الموقع مخترق",
            ),
            _human_row(
                "MA-0001105",
                "qelaaj.sa",
                name="شركة قلاع الجزيرة qelaaj",
                status="PENDING_REVIEW",
                categories="",
                evidence="",
            ),
            _human_row(
                "MA-0001240",
                "nbb.com.bh",
                name="بنك البحرين الوطني",
                status="QUALITY_BACKLOG",
                categories="company_domain_mismatch",
                evidence="Bahrain host",
            ),
            _human_row(
                "MA-0253537",
                "tofm.com.sa",
                categories="placeholder_or_fake",
                evidence="555 fake phone",
            ),
        ]
    )
    _write_csv(human_path, HUMAN_HEADERS, human_rows)

    domain_rows = [
        _domain_row("MA-0000540", "unec.ae"),
        _domain_row("MA-0001240", "nbb.com.bh"),
        _domain_row("MA-0094970", "vinnellarabia.com"),
        _domain_row("MA-0103334", "samba.com"),
        _domain_row("MA-0129195", "globalgroup.comsa"),
        _domain_row("MA-0144258", "tleleves.com"),
        _domain_row("MA-0295037", "sbi.co.in"),
    ]
    assert len(domain_rows) == EXPECTED_DOMAIN_HUMAN_COUNT
    _write_csv(domain_path, DOMAIN_HEADERS, domain_rows)
    _write_csv(
        patch_path,
        PATCH_HEADERS,
        [
            {
                "Master Account ID": "MA-0001105",
                "company_name": "شركة قلاع الجزيرة qelaaj",
                "source_domain": "qelaaj.sa",
                "tier": "TIER C",
                "field_type": "لينكدإن",
                "value": "https://www.linkedin.com/company/qelaaj",
                "source_method": "agent_reach_review_workbook",
                "review_status": "PENDING_REVIEW",
                "quality_flag": "ok",
                "notes": "",
            }
        ],
    )

    stats = build_human_review_queue(
        human_queue=human_path,
        domain_review_csv=domain_path,
        output_dir=output_dir,
        shared_report=shared,
        enrichment_patch=patch_path,
    )
    expected_added = EXPECTED_DOMAIN_HUMAN_COUNT - 1
    assert stats["original_count"] == EXPECTED_ORIGINAL_COUNT
    assert stats["added_from_domain_correction"] == expected_added
    assert stats["unified_unique_count"] == EXPECTED_ORIGINAL_COUNT + expected_added
    assert stats["agent_reach_run"] == "false"
    assert stats["master_overwrite"] is False
    assert stats["review_only_patch_created"] == "true"

    unified_path = output_dir / "human_review_unified_queue.csv"
    with unified_path.open("r", encoding="utf-8-sig", newline="") as handle:
        unified = list(csv.DictReader(handle))
    assert len(unified) == EXPECTED_ORIGINAL_COUNT + expected_added
    by_id = {row["Master Account ID"]: row for row in unified}
    assert by_id["MA-0001105"]["queue_source"] == SOURCE_ORIGINAL
    assert by_id["MA-0001240"]["queue_source"] == SOURCE_ORIGINAL
    assert by_id["MA-0000540"]["queue_source"] == SOURCE_DOMAIN

    with (output_dir / "human_review_decision_suggestions.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        decisions = {row["Master Account ID"]: row for row in csv.DictReader(handle)}
    assert decisions["MA-0000697"]["proposed_decision"] == DECIDE_REJECT
    assert decisions["MA-0001105"]["proposed_decision"] == DECIDE_APPROVE
    assert decisions["MA-0001105"]["confidence"] == CONF_HIGH
    assert decisions["MA-0000540"]["proposed_decision"] == DECIDE_PARK
    assert decisions["MA-0253537"]["proposed_decision"] == DECIDE_PARK

    report = (output_dir / "HUMAN_REVIEW_QUEUE_REPORT.md").read_text(encoding="utf-8")
    assert report == shared.read_text(encoding="utf-8")
    assert "HUMAN REVIEW QUEUE PREPARED" in report
    assert "NO MASTER OVERWRITE" in report
    assert "PHASE 7 NOT STARTED" in report
    assert human_path.exists()
    assert not (output_dir / "01_Master_Accounts.csv").exists()
