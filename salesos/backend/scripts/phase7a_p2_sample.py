#!/usr/bin/env python3
"""Create a deterministic, local-only roster for the authorized Phase 7 P2 sample.

The database transaction is asserted READ ONLY and restricted to salesos_test.
This script never writes review dispositions or changes any database row.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.modules.master_data.phase7.review_queue import review_async_session
from app.modules.master_data.phase7.sampling import (
    P2_SAMPLE_POLICY,
    deterministic_p2_sample,
)

# v5: population under OPTION_C_1+NCNP+DS5+LV+CR+ED (report 111); same population as v4 (report 110). The v1 sample
# (seed ...2026-09-20-v1, population 46,736) predates the NCNP CR rule.
SEED = "PHASE7A-P2-2026-09-25-v5-NCNP-DS5-LV-CR-ED"
EXPECTED_POPULATION = 33_654
EXPECTED_STRATA = {
    "SALES_READY_WITH_REVIEW": 15_746,
    "ENRICHMENT_REQUIRED": 17_908,
}
CSV_FIELDS = (
    "sample_rank",
    "sampling_stratum",
    "sampling_rate",
    "global_company_id",
    "candidate_type",
    "reason",
    "priority_score",
    "identity_state",
    "sales_readiness",
    "readiness_calc_version",
    "candidate_evidence_json",
    "source_ids_json",
    "readiness_basis_json",
    "status_before_sample",
    "decision_before_sample",
    "sample_sha256",
)

P2_QUERY = text(
    """
    WITH latest_readiness AS (
        SELECT DISTINCT ON (global_entity_id)
            global_entity_id, sales_readiness, calc_version, basis, computed_at
        FROM md_sales_readiness_history
        WHERE calc_version = :version
        ORDER BY global_entity_id, computed_at DESC, id DESC
    ), latest_identity AS (
        SELECT DISTINCT ON (global_entity_id)
            global_entity_id, identity_state
        FROM md_identity_classifications
        WHERE classification_version = :version
        ORDER BY global_entity_id, computed_at DESC, classification_version DESC
    )
    SELECT
        rc.global_entity_id::text AS global_company_id,
        rc.candidate_type,
        rc.reason,
        rc.priority_score,
        rc.evidence AS candidate_evidence,
        rc.source_ids,
        rc.status AS status_before_sample,
        rc.decision AS decision_before_sample,
        ic.identity_state,
        lr.sales_readiness,
        lr.calc_version AS readiness_calc_version,
        lr.basis AS readiness_basis
    FROM md_review_candidates rc
    JOIN latest_readiness lr ON lr.global_entity_id = rc.global_entity_id
    LEFT JOIN latest_identity ic ON ic.global_entity_id = rc.global_entity_id
    WHERE rc.candidate_type = 'P2'
      AND rc.reason = 'PRIORITIZATION_PP2'
      AND rc.status <> 'superseded'
    ORDER BY rc.global_entity_id
    """
)


def _json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _safe_cell(value: Any) -> str:
    if value is None:
        return ""
    cell = str(value)
    if cell.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + cell
    return cell


async def _read_population() -> list[dict[str, Any]]:
    async with review_async_session() as session, session.begin():
        await session.execute(text("SET TRANSACTION READ ONLY"))
        # The latest-readiness/identity CTE scans the 296k-company derived
        # history tables. Keep the transaction read-only but allow a bounded
        # analytical read to finish instead of inheriting the short driver
        # timeout used by ordinary API requests.
        await session.execute(text("SET LOCAL statement_timeout = '120s'"))
        database = (await session.execute(text("SELECT current_database()"))).scalar()
        read_only = (await session.execute(text("SHOW transaction_read_only"))).scalar()
        if database != "salesos_test":
            raise RuntimeError(f"Refusing Phase 7 sample read from database {database!r}")
        if str(read_only).lower() not in {"on", "true", "1"}:
            raise RuntimeError("Refusing Phase 7 sample: database transaction is not read-only")
        from app.modules.master_data.phase6.pipeline import ACTIVE_CLASSIFICATION_VERSION

        result = await session.execute(P2_QUERY, {"version": ACTIVE_CLASSIFICATION_VERSION})
        return [dict(row) for row in result.mappings().all()]


def _validate_population(rows: list[dict[str, Any]]) -> dict[str, int]:
    if len(rows) != EXPECTED_POPULATION:
        raise RuntimeError(
            f"P2 population drift: expected {EXPECTED_POPULATION}, received {len(rows)}; "
            "no sample file was written"
        )
    counts: dict[str, int] = {}
    ids: set[str] = set()
    for row in rows:
        company_id = str(row.get("global_company_id") or "")
        if not company_id or company_id in ids:
            raise RuntimeError("P2 population contains a missing or duplicate Global Company ID")
        ids.add(company_id)
        if row.get("candidate_type") != "P2" or row.get("reason") != "PRIORITIZATION_PP2":
            raise RuntimeError(
                "Unexpected candidate outside the approved P2 review-priority bucket"
            )
        if (
            row.get("status_before_sample") != "pending"
            or row.get("decision_before_sample") is not None
        ):
            raise RuntimeError("P2 candidate review state drifted; no sample file was written")
        stratum = str(row.get("sales_readiness") or "")
        if stratum not in P2_SAMPLE_POLICY:
            raise RuntimeError(
                f"Unsupported P2 readiness stratum {stratum!r}; no sample file was written"
            )
        counts[stratum] = counts.get(stratum, 0) + 1
    if counts != EXPECTED_STRATA:
        raise RuntimeError(
            f"P2 readiness strata drift: expected {EXPECTED_STRATA}, received {counts}; "
            "no sample file was written"
        )
    return counts


def _write_outputs(
    *,
    rows: list[dict[str, Any]],
    output_dir: Path,
    strata_counts: dict[str, int],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "PHASE7A_P2_SAMPLE_20260920.csv"
    manifest_path = output_dir / "PHASE7A_P2_SAMPLE_20260920.json"
    if csv_path.exists() or manifest_path.exists():
        raise FileExistsError("Refusing to overwrite an existing Phase 7 P2 sample artifact")

    sampled = deterministic_p2_sample(rows, seed=SEED)
    digest = hashlib.sha256()
    population_ids = "\n".join(sorted(str(row["global_company_id"]) for row in rows))
    population_digest = hashlib.sha256(population_ids.encode("utf-8")).hexdigest()

    temp_csv = csv_path.with_suffix(".csv.tmp")
    with temp_csv.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in sampled:
            data = {
                **row,
                "candidate_evidence_json": _json_cell(row.get("candidate_evidence")),
                "source_ids_json": _json_cell(row.get("source_ids")),
                "readiness_basis_json": _json_cell(row.get("readiness_basis")),
            }
            writer.writerow({field: _safe_cell(data.get(field)) for field in CSV_FIELDS})
    digest.update(temp_csv.read_bytes())

    sample_counts: dict[str, int] = {}
    for row in sampled:
        stratum = str(row["sampling_stratum"])
        sample_counts[stratum] = sample_counts.get(stratum, 0) + 1
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "database": "salesos_test",
        "transaction_mode": "READ ONLY",
        "database_writes": 0,
        "review_dispositions_recorded": 0,
        "sample_review_status": "NOT_REVIEWED_PENDING_HUMAN_REVIEW",
        "authorization": (
            "Current PO instruction in Codex on 2026-09-20: proceed with the Master Data/Phase 7 "
            "gate; "
            "local sample generation only. No DB disposition write, Phase 7-B merge, Phase 7-C CR "
            "promotion, or production action is authorized by this artifact."
        ),
        "prior_p2_sampling_policy": "PHASE7A_HUMAN_REVIEW_OPERATIONS_DECISION.md §3",
        "sampling_seed": SEED,
        "sampling_method": (
            "simple random per readiness stratum by ascending "
            "SHA-256(seed + separator + global_company_id)"
        ),
        "sample_size_rounding": "nearest integer, half up",
        "rates": P2_SAMPLE_POLICY,
        "population_count": len(rows),
        "population_stratum_counts": strata_counts,
        "sample_count": len(sampled),
        "sample_stratum_counts": sample_counts,
        "population_global_id_sha256": population_digest,
        "sample_csv_sha256": digest.hexdigest(),
        "sample_csv": csv_path.name,
        "material_error_threshold_percent": 2,
        "acceptance": (
            "PO must review each sampled record and accept the stratum result; if a stratum "
            "exceeds 2% material error, expand review and keep it blocked."
        ),
        "data_scope": (
            "P2 review-priority candidates only; Global Company IDs, classifier evidence, "
            "source IDs, and readiness basis. No contact names, emails, or phone numbers."
        ),
    }
    temp_manifest = manifest_path.with_suffix(".json.tmp")
    temp_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_csv.replace(csv_path)
    temp_manifest.replace(manifest_path)
    return manifest


async def main(output_dir: Path) -> int:
    rows = await _read_population()
    strata_counts = _validate_population(rows)
    manifest = _write_outputs(
        rows=rows,
        output_dir=output_dir,
        strata_counts=strata_counts,
    )
    print(
        json.dumps(
            {
                "database": manifest["database"],
                "transaction_mode": manifest["transaction_mode"],
                "population_count": manifest["population_count"],
                "population_stratum_counts": manifest["population_stratum_counts"],
                "sample_count": manifest["sample_count"],
                "sample_stratum_counts": manifest["sample_stratum_counts"],
                "database_writes": manifest["database_writes"],
                "csv": manifest["sample_csv"],
                "csv_sha256": manifest["sample_csv_sha256"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    default_output = project_root / "docs" / "data" / "phase7" / "p2_sample_20260920"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.output_dir)))
