#!/usr/bin/env python3
"""Phase 7-A — Apply the PO-authorized deterministic short-CR disposition rule.

PO-authorized rule (2026-08-29, "PHASE 7-A — EXECUTE INTERNAL HUMAN REVIEW
ASSISTED PASS" message):
  - valid_cr_count >= 1 and rejected_tokens exist
      -> disposition = CONFIRMED_ARTIFACT
      -> note = "Short token treated as artifact because a valid long CR exists."
  - valid_cr_count == 0
      -> disposition = UNRESOLVED_ESCALATE
      -> note = "No valid long CR present; requires escalation."
  - CONFIRMED_VALID_SHORT_CR is NEVER used by this script (no trusted external
    source is wired in) — matches the PO's explicit instruction.

This script performs NO new business logic: it calls the existing, already
code-reviewed and unit-tested `ReviewQueueService` methods
(`list_short_cr()` for the read, `record_disposition()` for the write) from
`app/modules/master_data/phase7/review_queue.py`, unchanged. It only adds the
PO's classification rule as a thin wrapper, and only ever writes to
`md_review_queue_state` (queue_type='SHORT_CR') via that existing,
already-verified write path — the same single write target used by every
other Phase 7-A operation. It touches no other table.

Reviewer field is set to a clearly-labeled non-human value so the audit trail
never misrepresents this as a human-adjudicated decision — see PHASE7A_
REVIEW_QUEUE_TOOLING_SPEC.md's explicit statement that short-CR ambiguity
"requires either a government-CR-registry lookup or senior MUHIDE data
knowledge" for TRUE adjudication (CONFIRMED_VALID_SHORT_CR); this rule never
makes that call, and only handles the two mechanically-determinable branches
where a trusted long CR already exists (or does not exist at all).

NOT EXECUTED as part of the session that authored this script: no database
connection is reachable from that session's environment (confirmed: no
`docker` binary, and a direct TCP probe to 127.0.0.1:5432 / localhost:5432
returned ECONNREFUSED; docker-network hostnames postgres/db/
host.docker.internal do not resolve). Run this from an environment with real
access to `salesos_test` (e.g. the developer machine with Docker running).

Usage:
    python scripts/phase7a_apply_shortcr_deterministic_rule.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.modules.master_data.phase7.review_queue import ReviewQueueService
from app.modules.master_data.phase7.schemas import ShortCRDisposition

PG_URL = "postgresql+asyncpg://salesos:salesos_dev_password@localhost:5432/salesos_test"

REVIEWER_LABEL = "phase7a-assisted-review-rule-engine (deterministic, PO-authorized 2026-08-29; not human-adjudicated)"

NOTE_ARTIFACT = "Short token treated as artifact because a valid long CR exists."
NOTE_ESCALATE = "No valid long CR present; requires escalation."


def classify(valid_cr_count: int, rejected_tokens: list[str]) -> tuple[str, str] | None:
    """Return (disposition, note) per the PO's exact rule, or None if the
    row doesn't match either mechanical branch (should not happen for the
    short-CR population, but fail closed rather than guess)."""
    if valid_cr_count >= 1 and rejected_tokens:
        return ShortCRDisposition.CONFIRMED_ARTIFACT.value, NOTE_ARTIFACT
    if valid_cr_count == 0:
        return ShortCRDisposition.UNRESOLVED_ESCALATE.value, NOTE_ESCALATE
    return None


async def main(dry_run: bool) -> int:
    engine = create_async_engine(PG_URL)
    async with AsyncSession(engine) as session:
        svc = ReviewQueueService(session=session)
        await svc._assert_salesos_test()

        rows = await svc.list_short_cr()  # READ-ONLY, unchanged existing method
        print(f"short-CR population from DB: {len(rows)} (expect 36)")

        confirmed_artifact = 0
        unresolved_escalate = 0
        confirmed_valid_short_cr = 0  # always 0 by design — never used
        unclassified = 0

        for row in rows:
            result = classify(row["valid_cr_count"], row["rejected_tokens"])
            if result is None:
                unclassified += 1
                print(f"  SKIP (no rule matched): {row['master_account_id']}")
                continue
            disposition, note = result
            if disposition == ShortCRDisposition.CONFIRMED_ARTIFACT.value:
                confirmed_artifact += 1
            elif disposition == ShortCRDisposition.UNRESOLVED_ESCALATE.value:
                unresolved_escalate += 1

            subject_key = row["global_company_id"] or row["master_account_id"]
            if dry_run:
                print(f"  DRY-RUN {row['master_account_id']} -> {disposition} ({note})")
                continue

            await svc.record_disposition(  # existing, unchanged, already-tested write path
                queue_type="SHORT_CR",
                subject_key=subject_key,
                disposition=disposition,
                reviewer=REVIEWER_LABEL,
                notes=note,
            )

        print()
        print(f"total reviewed: {len(rows)}")
        print(f"CONFIRMED_ARTIFACT: {confirmed_artifact}")
        print(f"UNRESOLVED_ESCALATE: {unresolved_escalate}")
        print(f"CONFIRMED_VALID_SHORT_CR: {confirmed_valid_short_cr} (never used, by design)")
        print(f"unclassified (should be 0): {unclassified}")

        if dry_run:
            print("\nDRY RUN — no rows were written.")
        else:
            print("\nWrites committed to md_review_queue_state (queue_type='SHORT_CR') only.")
    await engine.dispose()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Compute and print dispositions without writing.")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run)))
