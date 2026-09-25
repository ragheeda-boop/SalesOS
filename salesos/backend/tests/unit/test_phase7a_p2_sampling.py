"""Pure tests for deterministic Phase 7 P2 sampling."""

from __future__ import annotations

import pytest

from app.modules.master_data.phase7.sampling import (
    deterministic_p2_sample,
    sample_size,
)

SALES_READY_SAMPLE_SIZE = 1_119
ENRICHMENT_SAMPLE_SIZE = 94
SMALL_STRATUM_SAMPLE_SIZE = 2
THREE_PERCENT_OF_100 = 3
ONE_PERCENT_SAMPLE_SIZE = 1


def _rows(sales_readiness: str, count: int, offset: int = 0):
    return [
        {
            "global_company_id": f"company-{offset + index:04d}",
            "sales_readiness": sales_readiness,
        }
        for index in range(count)
    ]


def test_sample_sizes_round_to_nearest_integer_half_up():
    assert sample_size(37_312, 0.03) == SALES_READY_SAMPLE_SIZE
    assert sample_size(9_424, 0.01) == ENRICHMENT_SAMPLE_SIZE
    assert sample_size(50, 0.03) == SMALL_STRATUM_SAMPLE_SIZE


def test_stratified_sample_is_deterministic_and_independent_of_input_order():
    rows = _rows("SALES_READY_WITH_REVIEW", 100) + _rows("ENRICHMENT_REQUIRED", 100, 100)

    first = deterministic_p2_sample(rows, seed="stable-test-seed")
    second = deterministic_p2_sample(list(reversed(rows)), seed="stable-test-seed")

    assert [(row["global_company_id"], row["sample_sha256"]) for row in first] == [
        (row["global_company_id"], row["sample_sha256"]) for row in second
    ]
    assert (
        sum(row["sampling_stratum"] == "SALES_READY_WITH_REVIEW" for row in first)
        == THREE_PERCENT_OF_100
    )
    assert (
        sum(row["sampling_stratum"] == "ENRICHMENT_REQUIRED" for row in first)
        == ONE_PERCENT_SAMPLE_SIZE
    )
    assert all("sample_rank" in row and "sampling_rate" in row for row in first)


def test_missing_seed_duplicate_ids_and_unknown_strata_fail_closed():
    with pytest.raises(ValueError, match="seed is required"):
        deterministic_p2_sample([], seed=" ")

    duplicate = _rows("SALES_READY_WITH_REVIEW", 1) * 2
    with pytest.raises(ValueError, match="duplicate P2 global company ID"):
        deterministic_p2_sample(duplicate, seed="stable-test-seed")

    with pytest.raises(ValueError, match="unsupported P2 sampling stratum"):
        deterministic_p2_sample(
            [{"global_company_id": "company-1", "sales_readiness": "SALES_READY"}],
            seed="stable-test-seed",
        )
