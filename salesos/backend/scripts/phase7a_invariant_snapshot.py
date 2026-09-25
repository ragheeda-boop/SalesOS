"""W0 baseline: invariant snapshot of the Phase 6 / Phase 7 tables.

Read-only. Prints a fingerprint that later waves re-check to prove nothing moved.
"""

import asyncio
import json

import asyncpg

PHASE6_TABLES = (
    "md_source_rows", "md_global_companies", "md_global_people",
    "md_identity_classifications", "md_review_candidates", "md_contact_relationships",
    "md_industry_normalization", "md_quality_score_history", "md_sales_readiness_history",
    "md_p0_dispositions", "md_entity_merge_history", "md_entity_conflicts",
    "md_legacy_id_mappings", "md_field_provenance", "md_audit_events",
)
PHASE7_TABLE = "md_review_queue_state"


async def main() -> None:
    c = await asyncpg.connect(
        "postgresql://salesos:salesos_dev_password@localhost:5432/salesos_test"
    )
    print(f"database: {await c.fetchval('SELECT current_database()')}\n")

    print("== Phase 6 row counts ==")
    fp = {}
    for t in PHASE6_TABLES:
        try:
            fp[t] = await c.fetchval(f"SELECT count(*) FROM {t}")
            print(f"  {t:<34} {fp[t]:>10,}")
        except Exception as exc:
            print(f"  {t:<34} ERROR {exc}")

    print("\n== Phase 7 queue ==")
    fp[PHASE7_TABLE] = await c.fetchval(f"SELECT count(*) FROM {PHASE7_TABLE}")
    print(f"  {PHASE7_TABLE:<34} {fp[PHASE7_TABLE]:>10,}")
    for r in await c.fetch(
        f"SELECT queue_type, count(*) AS n, count(global_company_id) AS linked, "
        f"count(*) FILTER (WHERE evidence_ref ? 'linkage_status') AS labelled "
        f"FROM {PHASE7_TABLE} GROUP BY 1 ORDER BY 1"
    ):
        print(f"    {r['queue_type']:<20} n={r['n']:<6} linked={r['linked']:<6} "
              f"labelled={r['labelled']}")

    print("\n== integrity probes ==")
    dangling = await c.fetchval(
        f"SELECT count(*) FROM {PHASE7_TABLE} q "
        f"WHERE q.global_company_id IS NOT NULL "
        f"AND NOT EXISTS (SELECT 1 FROM md_global_companies g WHERE g.id = q.global_company_id)"
    )
    dangling_b = await c.fetchval(
        f"SELECT count(*) FROM {PHASE7_TABLE} q "
        f"WHERE q.global_company_id_b IS NOT NULL "
        f"AND NOT EXISTS (SELECT 1 FROM md_global_companies g WHERE g.id = q.global_company_id_b)"
    )
    bad_json = await c.fetchval(
        f"SELECT count(*) FROM {PHASE7_TABLE} WHERE evidence_ref IS NULL"
    )
    print(f"  dangling global_company_id    : {dangling}")
    print(f"  dangling global_company_id_b  : {dangling_b}")
    print(f"  NULL evidence_ref             : {bad_json}")

    print("\n== dispositions ==")
    for r in await c.fetch(
        f"SELECT queue_type, disposition, count(*) AS n FROM {PHASE7_TABLE} "
        f"GROUP BY 1,2 ORDER BY 1,2"
    ):
        print(f"  {r['queue_type']:<20} {r['disposition']!s:<16} {r['n']:>6}")

    print("\n== fingerprint ==")
    print(json.dumps(fp, indent=1, sort_keys=True))
    await c.close()


asyncio.run(main())
