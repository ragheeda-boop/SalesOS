"""Deterministic, read-only sampling helpers for Phase 7 P2 review."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

P2_SAMPLE_POLICY = {
    "SALES_READY_WITH_REVIEW": 0.03,
    "ENRICHMENT_REQUIRED": 0.01,
}


def sample_size(population: int, rate: float) -> int:
    """Round the planned sample to the nearest whole record, half up."""
    if population < 0 or not 0 <= rate <= 1:
        raise ValueError("population and rate are outside valid bounds")
    return int(population * rate + 0.5)


def deterministic_p2_sample(
    rows: list[dict[str, Any]],
    *,
    seed: str,
) -> list[dict[str, Any]]:
    """Return a reproducible simple-random sample inside each readiness stratum.

    Hash ordering makes selection independent of SQL row order and avoids the
    process-randomized Python ``hash()`` function. Inputs are never modified.
    """
    if not seed.strip():
        raise ValueError("sampling seed is required")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for row in rows:
        company_id = str(row.get("global_company_id") or "").strip()
        stratum = str(row.get("sales_readiness") or "").strip()
        if not company_id:
            raise ValueError("P2 sampling row is missing global_company_id")
        if company_id in seen_ids:
            raise ValueError(f"duplicate P2 global company ID: {company_id}")
        seen_ids.add(company_id)
        if stratum not in P2_SAMPLE_POLICY:
            raise ValueError(f"unsupported P2 sampling stratum: {stratum or '<blank>'}")
        grouped[stratum].append(row)

    selected: list[dict[str, Any]] = []
    for stratum, rate in P2_SAMPLE_POLICY.items():
        population = grouped.get(stratum, [])
        ranked = sorted(
            [
                (
                    hashlib.sha256(
                        f"{seed}\x1f{row['global_company_id']}".encode()
                    ).hexdigest(),
                    row,
                )
                for row in population
            ],
            key=lambda item: (item[0], str(item[1]["global_company_id"])),
        )
        count = sample_size(len(population), rate)
        for rank, (digest, row) in enumerate(ranked[:count], start=1):
            selected.append(
                {
                    **row,
                    "sampling_stratum": stratum,
                    "sampling_rate": rate,
                    "sample_rank": rank,
                    "sample_sha256": digest,
                }
            )
    return selected
