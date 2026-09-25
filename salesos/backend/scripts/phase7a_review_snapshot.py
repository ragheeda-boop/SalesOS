#!/usr/bin/env python3
"""Create a read-only Phase 7-A human-review snapshot.

The snapshot is an operational handoff, not a disposition writer. It is
restricted to salesos_test, uses a READ ONLY transaction, and exports queue
counts plus the 36 short-CR records for human review.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.modules.master_data.phase7.review_queue import ReviewQueueService, review_async_session


async def read_snapshot() -> dict:
    async with review_async_session() as session, session.begin():
        await session.execute(text("SET TRANSACTION READ ONLY"))
        await session.execute(text("SET LOCAL statement_timeout = '120s'"))
        database = (await session.execute(text("SELECT current_database()"))).scalar()
        read_only = (await session.execute(text("SHOW transaction_read_only"))).scalar()
        if database != "salesos_test":
            raise RuntimeError(f"Refusing snapshot from database {database!r}")
        if str(read_only).lower() not in {"on", "true", "1"}:
            raise RuntimeError("Refusing snapshot: transaction is not READ ONLY")

        counts_result = await session.execute(
            text(
                "SELECT candidate_type, reason, status, decision, COUNT(*) AS count "
                "FROM md_review_candidates "
                "GROUP BY candidate_type, reason, status, decision "
                "ORDER BY candidate_type, reason, status, decision"
            )
        )
        candidate_counts = [dict(row) for row in counts_result.mappings().all()]

        state_result = await session.execute(
            text(
                "SELECT queue_type, status, disposition, COUNT(*) AS count "
                "FROM md_review_queue_state "
                "GROUP BY queue_type, status, disposition "
                "ORDER BY queue_type, status, disposition"
            )
        )
        state_counts = [dict(row) for row in state_result.mappings().all()]

        svc = ReviewQueueService(session=session)
        short_cr = await svc.list_short_cr()

        return {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "database": database,
            "transaction_mode": "READ ONLY",
            "database_writes": 0,
            "candidate_counts": candidate_counts,
            "queue_state_counts": state_counts,
            "short_cr_count": len(short_cr),
            "short_cr": short_cr,
            "review_status": "PENDING_HUMAN_REVIEW",
            "production_approved": False,
        }


def write_outputs(snapshot: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "PHASE7A_REVIEW_SNAPSHOT_20260922.json"
    csv_path = output_dir / "PHASE7A_SHORT_CR_REVIEW_20260922.csv"
    md_path = output_dir / "PHASE7A_REVIEW_SNAPSHOT_20260922.md"

    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    fields = ["master_account_id", "global_company_id", "cr_number_raw", "valid_cr_count", "rejected_tokens"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in snapshot["short_cr"]:
            writer.writerow({key: row.get(key, "") for key in fields})

    lines = [
        "# Phase 7-A Review Snapshot — 2026-09-22",
        "",
        f"- Database: `{snapshot['database']}`",
        f"- Transaction: `{snapshot['transaction_mode']}`",
        f"- Database writes: `{snapshot['database_writes']}`",
        f"- Short-CR records: `{snapshot['short_cr_count']}`",
        "- Review status: **PENDING_HUMAN_REVIEW**",
        "- Production approval: **NO**",
        "",
        "## Candidate counts",
        "",
        "| Type | Reason | Status | Decision | Count |",
        "|---|---|---|---|---:|",
    ]
    for row in snapshot["candidate_counts"]:
        lines.append(
            f"| {row['candidate_type']} | {row['reason']} | {row['status']} | "
            f"{row['decision'] or ''} | {row['count']} |"
        )
    lines += [
        "",
        "## Review rules",
        "",
        "- This package is read-only and records no disposition.",
        "- Human/PO/DI acceptance is required before any Phase 7 promotion.",
        "- No provider, production database, merge, CR promotion, or CRM write is allowed from this artifact.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def main(output_dir: Path) -> int:
    snapshot = await read_snapshot()
    write_outputs(snapshot, output_dir)
    print(json.dumps({
        "database": snapshot["database"],
        "transaction_mode": snapshot["transaction_mode"],
        "database_writes": snapshot["database_writes"],
        "short_cr_count": snapshot["short_cr_count"],
        "output_dir": str(output_dir),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    raise SystemExit(asyncio.run(main(parser.parse_args().output_dir)))
