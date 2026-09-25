"""Real Phase 6 run with the NCNP CR rule on salesos_test (PO decisions, reports 104/106).

Writes a NEW classification version (OPTION_C_1+EXCL_NCNP); OPTION_C_1 rows stay
as history. Pending, undecided review candidates the new version no longer
produces are marked status='superseded' (never deleted), with the superseding
version and time recorded in their evidence. Everything runs in one
transaction: any failure rolls the whole run back.

    python scripts/phase6_apply_ncnp_rule.py            # refuses without --apply
    python scripts/phase6_apply_ncnp_rule.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.master_data.phase6.pipeline import Phase6Pipeline  # noqa: E402

EXCLUDED = frozenset({"NCNP"})


async def supersede_candidates(conn, produced: set[tuple[str, str, str]], version: str) -> int:
    await conn.execute(
        "CREATE TEMP TABLE _produced (gid uuid, ctype varchar(4), reason varchar(255)) ON COMMIT DROP"
    )
    await conn.copy_records_to_table(
        "_produced", records=[(uuid.UUID(g), t, r) for g, t, r in produced]
    )
    return int((await conn.execute(
        """UPDATE md_review_candidates rc
              SET status = 'superseded',
                  evidence = rc.evidence || jsonb_build_object(
                      'superseded_by_version', $1::text, 'superseded_at', now()::text,
                      'superseded_reason', 'Phase 6 rule change (reports 104/106/108)')
            WHERE rc.status = 'pending' AND rc.decision IS NULL
              AND NOT EXISTS (SELECT 1 FROM _produced p
                               WHERE p.gid = rc.global_entity_id
                                 AND p.ctype = rc.candidate_type AND p.reason = rc.reason)""",
        version,
    )).split()[-1])


async def main(apply: bool, shared_domain_threshold: int | None = None) -> int:
    if not apply:
        print("Refusing: pass --apply (use scripts/phase6_dry_run.py to preview).")
        return 2
    conn = await asyncpg.connect(host="localhost", port=5432, user="salesos",
                                 password="salesos_dev_password", database="salesos_test")
    try:
        assert await conn.fetchval("SELECT current_database()") == "salesos_test"
        async with conn.transaction():
            pipeline = Phase6Pipeline(
                conn, dry_run=False, cr_excluded_sources=EXCLUDED,
                shared_domain_threshold=shared_domain_threshold,
            )
            result = await pipeline.run()
            produced = {
                (str(pipeline._to_uuid(c["entity_key"])), c["candidate_type"], c["reason"])
                for c in pipeline._candidate_rows
            }
            superseded = await supersede_candidates(conn, produced, pipeline.version)
            counts = {
                "version": pipeline.version,
                "identity_rows_new_version": await conn.fetchval(
                    "SELECT COUNT(*) FROM md_identity_classifications WHERE classification_version=$1",
                    pipeline.version),
                "candidates_produced": len(produced),
                "candidates_superseded": superseded,
                "summary": {k: v for k, v in result.get("summary", {}).items()},
                "safety": dict(result.get("safety", {})),
            }
        print(json.dumps(counts, ensure_ascii=False, indent=1, default=str))
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--shared-domain-threshold", type=int)
    a = ap.parse_args()
    sys.exit(asyncio.run(main(a.apply, a.shared_domain_threshold)))
