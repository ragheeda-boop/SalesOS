#!/usr/bin/env python3
"""Phase 6 — Dry Run Harness (salesos_test only).

Runs the Phase 6 pipeline in dry-run mode (no writes), produces:
  - phase6_dry_run_results.json  (structured summary + safety counters)
  - phase6_dry_run_changes.csv   (every staged change row)
  - docs/data/phase6/implementation/PHASE6_DRY_RUN_REPORT.md  (human-readable)

Safety invariants: all safety counters MUST be 0 in dry-run.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import UTC, datetime

import asyncpg

# Ensure backend is on path for module imports.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.modules.master_data.phase6.pipeline import Phase6Pipeline

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"

OUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docs", "data", "phase6", "implementation"
)


def write_human_report(report_path, result, changes, max_accounts):
    safety = result.get("safety", {})
    summary = result.get("summary", {})
    staged = result.get("staged", {})
    required_safety = [
        "source_rows_modified",
        "raw_payload_modified",
        "global_ids_changed",
        "existing_entities_deleted",
        "fuzzy_auto_merges",
        "government_id_vetoes_bypassed",
        "apollo_calls",
        "external_api_calls",
        "production_writes",
    ]
    all_zero = (
        not any(safety.values())
        and all(safety.get(counter, 0) == 0 for counter in required_safety)
    )
    sample_note = (
        "**This is a bounded sample, not a full-dataset readiness result.**"
        if max_accounts is not None
        else ""
    )
    if not all_zero:
        verdict = "DO NOT PROCEED - safety invariants violated."
    elif max_accounts is not None:
        verdict = "Sample safety passed; run the full dataset before any full-dataset gate."
    else:
        verdict = (
            "Dry-run safety passed; do not write until the candidate review, DI P1/P2 "
            "methodology confirmation, and Product/PO sign-off are complete."
        )

    with open(report_path, "w", encoding="utf-8") as report:
        report.write(f"""# Phase 6 Dry Run Report

**Generated:** {datetime.now(UTC).isoformat()}
**Database:** salesos_test (dry-run - no writes)
**Database transaction:** read-only enforced by PostgreSQL
**Pipeline version:** {result.get('version', 'unknown')}
**Sampled run:** {summary.get('sampled_run', False)}
**Account limit:** {summary.get('sample_limit', 0) or 'none (full source)'}

{sample_note}

---

## Safety Counters (MUST ALL BE 0 in dry-run)

| Counter | Value | Status |
|---------|-------|--------|
""")
        all_safety_counters = list(required_safety) + sorted(
            set(safety) - set(required_safety)
        )
        for counter in all_safety_counters:
            value = safety.get(counter, 0)
            status = "PASS" if value == 0 else "FAIL"
            report.write(f"| {counter} | {value} | {status} |\n")

        report.write(f"""
---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Master Accounts processed | {summary.get('master_accounts_loaded', 0):,} |
| Identity classifications staged | {staged.get('identity_classifications', 0):,} |
| Review candidates (P0-P3) staged | {staged.get('review_candidates', 0):,} |
| Industry normalizations staged | {staged.get('industry_normalizations', 0):,} |
| Quality score history entries staged | {staged.get('quality_history', 0):,} |
| Sales readiness history entries staged | {staged.get('sales_readiness_history', 0):,} |
| Contact relationships staged | {summary.get('contact_relationships_staged', 0):,} |

---

## Identity State Distribution

| Identity State | Count |
|----------------|-------|
""")
        for state, count in sorted(summary.get("identity_states", {}).items()):
            report.write(f"| {state} | {count:,} |\n")

        report.write("""
---

## CR Class Distribution

| CR Class | Count |
|----------|-------|
""")
        for cr_class, count in sorted(summary.get("cr_classes", {}).items()):
            report.write(f"| {cr_class} | {count:,} |\n")

        report.write("""
---

## Review Priority Distribution

| Priority | Count |
|----------|-------|
""")
        for priority, count in sorted(summary.get("priorities", {}).items()):
            report.write(f"| {priority} | {count:,} |\n")

        report.write(f"""
---

## Change Log (sample first 20 of {result.get('change_count', 0)})

| Op | Entity ID | Table | Key |
|----|-----------|-------|-----|
""")
        for change in changes[:20]:
            report.write(
                f"| {change['op']} | {change['entity_id'] or ''} | "
                f"{change['table']} | {change['key'] or ''} |\n"
            )

        report.write(f"""
---

## Verdict

**Dry-run safety: {'ALL COUNTERS ZERO' if all_zero else 'NON-ZERO SAFETY COUNTERS'}**

{verdict}

---

*Report generated by Phase 6 Dry Run Harness. No data was written to salesos_test.*
""")
    return all_zero


def reconcile_streamed_result(result, table_counts):
    table_to_staged_key = {
        "md_identity_classifications": "identity_classifications",
        "md_review_candidates": "review_candidates",
        "md_industry_normalization": "industry_normalizations",
        "md_quality_score_history": "quality_history",
        "md_sales_readiness_history": "sales_readiness_history",
        "md_contact_relationships": "contact_relationships",
    }
    unknown_tables = set(table_counts) - set(table_to_staged_key)
    streamed_count = sum(table_counts.values())
    if unknown_tables or streamed_count != result["change_count"]:
        raise RuntimeError(
            "Streamed change artifact does not reconcile with pipeline output: "
            f"unknown_tables={sorted(unknown_tables)}, "
            f"table_rows={streamed_count}, "
            f"pipeline_changes={result['change_count']}"
        )
    result["staged"] = {
        staged_key: table_counts.get(table, 0)
        for table, staged_key in table_to_staged_key.items()
    }
    result["database_transaction"] = "READ ONLY"


async def main(
    max_accounts: int | None = None,
    output_suffix: str | None = None,
    exclude_cr_sources: frozenset[str] = frozenset(),
    shared_domain_threshold: int | None = None,
) -> int:
    if max_accounts is not None and max_accounts < 1:
        raise ValueError("--max-accounts must be a positive integer")
    if output_suffix and not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", output_suffix):
        raise ValueError(
            "--output-suffix may contain only letters, numbers, underscores, and hyphens"
        )

    report_suffix = f"_sample_{max_accounts}" if max_accounts is not None else ""
    if output_suffix:
        report_suffix += f"_{output_suffix}"
    results_json = os.path.join(OUT_DIR, f"phase6_dry_run{report_suffix}_results.json")
    changes_csv = os.path.join(OUT_DIR, f"phase6_dry_run{report_suffix}_changes.csv")
    report_md = os.path.join(OUT_DIR, f"PHASE6_DRY_RUN{report_suffix.upper()}_REPORT.md")

    # Safety: refuse if not salesos_test
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    try:
        db = await conn.fetchval("SELECT current_database()")
        assert db == "salesos_test", f"REFUSING: connected to {db}, not salesos_test"
        print(f"Connected to {db} (dry-run safe).")

        os.makedirs(OUT_DIR, exist_ok=True)
        # Stream full change details directly to disk; keep only a small sample in memory.
        with open(changes_csv, "w", encoding="utf-8", newline="") as changes_file:
            writer = csv.writer(changes_file)
            writer.writerow(["op", "entity_id", "table", "key", "payload"])
            table_counts = Counter()

            def write_change(change):
                table_counts[change["table"]] += 1
                writer.writerow([
                    change["op"], change["entity_id"] or "", change["table"],
                    change["key"] or "", change["payload"],
                ])

            async with conn.transaction(readonly=True):
                pipeline = Phase6Pipeline(
                    conn, dry_run=True, change_sink=write_change,
                    cr_excluded_sources=exclude_cr_sources,
                    shared_domain_threshold=shared_domain_threshold,
                )
                result = await pipeline.run(max_accounts=max_accounts)
        reconcile_streamed_result(result, table_counts)

        # Write structured JSON results after the streamed run completes.
        with open(results_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"Wrote {results_json}")
        print(f"Wrote {changes_csv}")

        summary = result.get("summary", {})
        safety = result.get("safety", {})
        all_zero = write_human_report(report_md, result, pipeline.changes, max_accounts)
        print(f"Wrote {report_md}")

        # Final verdict.
        print("\n=== DRY RUN SUMMARY ===")
        print(f"  Master accounts: {summary.get('master_accounts_loaded', 0):,}")
        print(f"  Identity states: {dict(summary.get('identity_states', {}))}")
        print(f"  CR classes: {dict(summary.get('cr_classes', {}))}")
        print(f"  Priorities: {dict(summary.get('priorities', {}))}")
        print(f"  Contact relationships: {summary.get('contact_relationships_staged', 0):,}")
        print(f"  Staged changes: {result.get('change_count', 0):,}")
        print(f"  Safety counters: {dict(safety)}")
        print(f"  ALL ZERO: {all_zero}")

        return 0 if all_zero else 1

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-accounts",
        type=int,
        help="Run a bounded dry-run sample and write separate sample report files",
    )
    parser.add_argument(
        "--output-suffix",
        help="Write versioned report files without replacing previous dry-run artifacts",
    )
    parser.add_argument(
        "--exclude-cr-source",
        action="append",
        default=[],
        help="Source system whose CR tokens are never anchors (PO decision G3-2, report 104)",
    )
    parser.add_argument(
        "--shared-domain-threshold",
        type=int,
        help="Ignore domains used by >= N distinct Master Accounts as identity (report 107)",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(
        args.max_accounts, args.output_suffix, frozenset(args.exclude_cr_source),
        args.shared_domain_threshold,
    )))
