"""Unit tests for the review-only External Source Enrichment Pilot helper."""

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

from agent_reach_external_source_pilot import (  # noqa: E402
    CLASS_DATA_FOUND,
    CLASS_MANUAL,
    CLASS_NONE,
    CLASS_PAID,
    FORBIDDEN_OUTPUT_MARKERS,
    FULL_QUEUE_SIZE,
    PILOT_SIZE,
    STRATA_TARGETS,
    STRATUM_AR_HAS_CONTACT,
    STRATUM_DEAD_DOMAIN,
    STRATUM_LINKEDIN,
    STRATUM_PHONE,
    assert_safe_output_dir,
    assign_stratum,
    choose_sample,
    classification_counts,
    draw_stratified_sample,
    interleave_by_tier,
    is_diverse_slice,
    merge_research,
    patch_rows_from_results,
    scale_yield,
    unresolved_from_results,
    write_pilot_outputs,
)
from agent_reach_external_source_pilot_findings import FINDINGS  # noqa: E402


def _row(  # noqa: PLR0913
    account_id: str,
    *,
    name: str = "Acme",
    domain: str = "acme.com",
    usable: str = "true",
    attempted: str = "true",
    has_contacts: str = "false",
    missing_phone: str = "false",
    missing_linkedin: str = "true",
    missing_other: str = "true",
    categories: str = "no_contact_found",
    suggested: str = "false",
    status: str = "QUALITY_BACKLOG",
    why: str = "Agent Reach already fetched the listed domain.",
) -> dict[str, str]:
    return {
        "Master Account ID": account_id,
        "company_name": name,
        "tier": "CLASS A",
        "tier_bucket": "CLASS A",
        "primary_domain": domain,
        "usable_domain": usable,
        "attempted_agent_reach": attempted,
        "already_has_master_contacts": has_contacts,
        "enrichment_status": status,
        "quality_categories": categories,
        "issue_evidence": "no usable Saudi phone/social",
        "why_agent_reach_cannot_finish": why,
        "missing_phone": missing_phone,
        "missing_whatsapp": "true",
        "missing_linkedin": missing_linkedin,
        "missing_other_social": missing_other,
        "suggested_pilot_slice": suggested,
        "notes": "agent_reach_already_attempted",
        "review_only": "true",
    }


def test_pilot_findings_cover_forty_valid_classes() -> None:
    assert len(FINDINGS) == PILOT_SIZE
    assert len(set(FINDINGS)) == PILOT_SIZE
    for finding in FINDINGS.values():
        assert finding["classification"] in {
            CLASS_DATA_FOUND,
            CLASS_PAID,
            CLASS_MANUAL,
            CLASS_NONE,
        }
        if finding["classification"] == CLASS_DATA_FOUND:
            assert finding["field_found"]
            assert finding["value_found"]
            assert finding["source_url_or_note"]


def test_stratum_targets_sum_to_pilot_size() -> None:
    assert sum(STRATA_TARGETS.values()) == PILOT_SIZE


def test_assign_stratum_priority() -> None:
    has_contact_row = _row("MA-1", has_contacts="true", attempted="false")
    assert assign_stratum(has_contact_row) == STRATUM_AR_HAS_CONTACT
    assert assign_stratum(_row("MA-2", usable="false")) == STRATUM_DEAD_DOMAIN
    assert assign_stratum(_row("MA-3", categories="unreachable")) == STRATUM_DEAD_DOMAIN
    assert assign_stratum(_row("MA-4", missing_phone="true")) == STRATUM_PHONE
    assert (
        assign_stratum(_row("MA-5", missing_linkedin="true", missing_other="false"))
        == STRATUM_LINKEDIN
    )


def test_interleave_by_tier_round_robins() -> None:
    rows = [
        {**_row("MA-C1"), "tier_bucket": "CLASS A"},
        {**_row("MA-C2"), "tier_bucket": "CLASS A"},
        {**_row("MA-B1"), "tier_bucket": "TIER B"},
        {**_row("MA-D1"), "tier_bucket": "TIER D"},
    ]
    ordered = [row["Master Account ID"] for row in interleave_by_tier(rows)]
    assert ordered[0] == "MA-C1"
    assert ordered[1] == "MA-B1"
    assert ordered[2] == "MA-D1"
    assert ordered[3] == "MA-C2"


def test_suggested_slice_not_diverse_when_one_stratum() -> None:
    rows = [_row(f"MA-{index:07d}", suggested="true") for index in range(PILOT_SIZE)]
    diverse, reason = is_diverse_slice(rows)
    assert diverse is False
    assert "strata" in reason or "largest" in reason


def test_draw_stratified_sample_is_exactly_40_and_unique() -> None:
    pool: list[dict[str, str]] = []
    for index in range(20):
        pool.append(_row(f"MA-P{index:04d}", missing_phone="true", missing_linkedin="false"))
        pool.append(_row(f"MA-L{index:04d}", missing_linkedin="true", missing_other="false"))
        pool.append(_row(f"MA-O{index:04d}", missing_linkedin="false", missing_other="true"))
        pool.append(_row(f"MA-D{index:04d}", usable="false"))
        pool.append(_row(f"MA-C{index:04d}", has_contacts="true"))
        pool.append(
            _row(
                f"MA-A{index:04d}",
                missing_linkedin="false",
                missing_other="false",
                missing_phone="false",
            )
        )
        pool.append(
            _row(
                f"MA-U{index:04d}",
                attempted="false",
                missing_linkedin="false",
                missing_other="false",
                missing_phone="false",
            )
        )
        pool.append(_row(f"MA-X{index:04d}", categories="other"))
    sample = draw_stratified_sample(pool)
    ids = [row["Master Account ID"] for row in sample]
    assert len(sample) == PILOT_SIZE
    assert len(set(ids)) == PILOT_SIZE


def test_choose_sample_falls_back_to_stratified() -> None:
    suggested = [_row(f"MA-S{index:04d}", suggested="true") for index in range(PILOT_SIZE)]
    extras = [
        _row(f"MA-E{index:04d}", missing_phone="true", suggested="false") for index in range(30)
    ]
    extras += [
        _row(f"MA-F{index:04d}", usable="false", suggested="false") for index in range(20)
    ]
    extras += [
        _row(f"MA-G{index:04d}", has_contacts="true", suggested="false") for index in range(20)
    ]
    extras += [
        _row(
            f"MA-H{index:04d}",
            missing_linkedin="false",
            missing_other="true",
            suggested="false",
        )
        for index in range(20)
    ]
    extras += [
        _row(
            f"MA-I{index:04d}",
            attempted="false",
            missing_linkedin="false",
            missing_other="false",
            suggested="false",
        )
        for index in range(10)
    ]
    sample, method, note = choose_sample(suggested + extras)
    assert method == "stratified_by_gap_reason"
    assert "not used" in note
    assert len(sample) == PILOT_SIZE
    assert all(row["sampling_method"] == method for row in sample)


def test_choose_sample_keeps_diverse_suggested_slice() -> None:
    rows: list[dict[str, str]] = []
    builders = [
        lambda i: _row(f"MA-P{i:02d}", missing_phone="true", suggested="true"),
        lambda i: _row(
            f"MA-L{i:02d}", missing_linkedin="true", missing_other="false", suggested="true"
        ),
        lambda i: _row(
            f"MA-O{i:02d}", missing_linkedin="false", missing_other="true", suggested="true"
        ),
        lambda i: _row(f"MA-D{i:02d}", usable="false", suggested="true"),
        lambda i: _row(f"MA-C{i:02d}", has_contacts="true", suggested="true"),
        lambda i: _row(
            f"MA-A{i:02d}",
            missing_linkedin="false",
            missing_other="false",
            missing_phone="false",
            suggested="true",
        ),
        lambda i: _row(
            f"MA-U{i:02d}",
            attempted="false",
            missing_linkedin="false",
            missing_other="false",
            suggested="true",
        ),
        lambda i: _row(f"MA-X{i:02d}", categories="other", suggested="true"),
    ]
    index = 0
    while len(rows) < PILOT_SIZE:
        rows.append(builders[index % len(builders)](index))
        index += 1
    sample, method, note = choose_sample(rows)
    assert method == "suggested_pilot_slice"
    assert "diverse" in note
    assert len(sample) == PILOT_SIZE


def test_patch_and_unresolved_split() -> None:
    results = [
        {
            "Master Account ID": "MA-1",
            "company_name": "A",
            "primary_domain": "a.com",
            "classification": CLASS_DATA_FOUND,
            "field_found": "linkedin",
            "value_found": "https://www.linkedin.com/company/a",
            "source_url_or_note": "https://a.com",
            "confidence": "medium",
            "reason": "official site footer",
            "sampling_stratum": STRATUM_LINKEDIN,
            "why_external_source_needed": "AR missed LinkedIn",
        },
        {
            "Master Account ID": "MA-2",
            "company_name": "B",
            "primary_domain": "b.com",
            "classification": CLASS_PAID,
            "field_found": "",
            "value_found": "",
            "source_url_or_note": "",
            "confidence": "",
            "reason": "CR registry only",
            "sampling_stratum": STRATUM_PHONE,
            "why_external_source_needed": "no public phone",
        },
    ]
    patches = patch_rows_from_results(results)
    unresolved = unresolved_from_results(results)
    assert len(patches) == 1
    assert patches[0]["do_not_apply_to_master"] == "true"
    assert patches[0]["master_overwrite"] == "false"
    assert len(unresolved) == 1
    assert unresolved[0]["classification"] == CLASS_PAID


def test_scale_yield_is_naive() -> None:
    found = PILOT_SIZE // 4
    estimate = scale_yield(found)
    assert estimate["sample_found"] == found
    assert estimate["point_estimate"] == round(found / PILOT_SIZE * FULL_QUEUE_SIZE)


def test_write_outputs_refuses_prior_dirs(tmp_path: Path) -> None:
    queue = tmp_path / "q.csv"
    queue.write_text("Master Account ID\n", encoding="utf-8")
    with pytest.raises(ValueError, match="prior dir"):
        assert_safe_output_dir(tmp_path / FORBIDDEN_OUTPUT_MARKERS[2] / "x", queue)


def test_write_pilot_outputs_roundtrip(tmp_path: Path) -> None:
    sample = []
    results = []
    for index in range(PILOT_SIZE):
        account = f"MA-{index:07d}"
        sample.append(
            {
                **_row(account),
                "sampling_stratum": STRATUM_PHONE,
                "sampling_method": "stratified_by_gap_reason",
            }
        )
        results.append(
            {
                "Master Account ID": account,
                "company_name": "Acme",
                "tier": "CLASS A",
                "tier_bucket": "CLASS A",
                "primary_domain": "acme.com",
                "sampling_stratum": STRATUM_PHONE,
                "classification": CLASS_NONE if index else CLASS_DATA_FOUND,
                "field_found": "phone" if index == 0 else "",
                "value_found": "+966500000000" if index == 0 else "",
                "source_url_or_note": "https://acme.com/contact" if index == 0 else "",
                "confidence": "medium" if index == 0 else "",
                "reason": "public contact page" if index == 0 else "no public source",
                "why_external_source_needed": "AR no contact",
            }
        )
    output = tmp_path / "20260908T000000Z_external_source_pilot"
    shared = tmp_path / "EXTERNAL_SOURCE_PILOT_REPORT.md"
    stats = write_pilot_outputs(
        output_dir=output,
        shared_report=shared,
        sample_rows=sample,
        result_rows=results,
        sampling_method="stratified_by_gap_reason",
        sampling_note="unit test",
        tests_ruff="not run",
        risks=["small n"],
        recommend_expand=False,
    )
    assert stats["sample_size"] == PILOT_SIZE
    assert classification_counts(results)[CLASS_DATA_FOUND] == 1
    with (output / "external_source_pilot_sample.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        assert len(list(csv.DictReader(handle))) == PILOT_SIZE
    with (output / "external_source_pilot_review_only_patch.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        assert len(list(csv.DictReader(handle))) == 1
    assert "DO NOT EXPAND" in shared.read_text(encoding="utf-8")
    assert CLASS_MANUAL in stats["classification_counts"]


def test_merge_research_requires_every_sample_id() -> None:
    sample = [
        {
            **_row("MA-1"),
            "sampling_stratum": STRATUM_PHONE,
            "why_agent_reach_cannot_finish": "AR gap",
        }
    ]
    with pytest.raises(ValueError, match="missing research"):
        merge_research(sample, {})
    merged = merge_research(
        sample,
        {
            "MA-1": {
                "classification": CLASS_NONE,
                "reason": "no public source",
            }
        },
    )
    assert merged[0]["why_external_source_needed"] == "AR gap"
    assert merged[0]["classification"] == CLASS_NONE


def test_invalid_classification_rejected() -> None:
    from agent_reach_external_source_pilot import classify_result

    with pytest.raises(ValueError, match="invalid classification"):
        classify_result({"classification": "maybe"})
