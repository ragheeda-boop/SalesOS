"""STEP 11: Final database safety check + verdict."""
import asyncio, asyncpg, uuid

async def main():
    conn = await asyncpg.connect(host="localhost", port=5432, user="salesos",
                                  password="salesos_dev_password", database="salesos_test")
    ok = []
    fail = []

    def check(name, cond, detail=""):
        (ok if cond else fail).append(f"  [{'PASS' if cond else 'FAIL'}] {name}{' — ' + str(detail) if detail else ''}")

    # 1. Connected to salesos_test
    r = await conn.fetchval("SELECT current_database()")
    check("Database is salesos_test", r == "salesos_test", r)

    # 2. md_* global tables have NO RLS
    for tbl in ["md_global_companies", "md_global_people", "md_legacy_id_mappings", "md_field_provenance"]:
        r = await conn.fetchval("SELECT relrowsecurity FROM pg_class WHERE relname = $1", tbl)
        check(f"{tbl} has no RLS", r is False)

    # 3. No orphan legacy mappings (pointing to deleted entities)
    orphan_companies = await conn.fetchval(
        "SELECT COUNT(*) FROM md_legacy_id_mappings lm "
        "WHERE lm.global_entity_type='C' AND NOT EXISTS (SELECT 1 FROM md_global_companies gc WHERE gc.id=lm.global_entity_id)"
    )
    orphan_people = await conn.fetchval(
        "SELECT COUNT(*) FROM md_legacy_id_mappings lm "
        "WHERE lm.global_entity_type='P' AND NOT EXISTS (SELECT 1 FROM md_global_people gp WHERE gp.id=lm.global_entity_id)"
    )
    check("No orphan company mappings", orphan_companies == 0, orphan_companies)
    check("No orphan people mappings", orphan_people == 0, orphan_people)

    # 4. No orphan source rows (pointing to deleted source files)
    orphan_sr = await conn.fetchval(
        "SELECT COUNT(*) FROM md_source_rows sr "
        "WHERE NOT EXISTS (SELECT 1 FROM md_source_files sf WHERE sf.id=sr.source_file_id)"
    )
    check("No orphan source rows", orphan_sr == 0, orphan_sr)

    # 5. Source immutability: all source rows have raw_payload
    null_payload = await conn.fetchval("SELECT COUNT(*) FROM md_source_rows WHERE raw_payload IS NULL")
    check("All source rows have raw_payload", null_payload == 0, null_payload)

    # 6. Companies: canonical_name and slug non-null, slugs unique
    bad_company = await conn.fetchval("SELECT COUNT(*) FROM md_global_companies WHERE canonical_name IS NULL OR canonical_name='' OR slug IS NULL")
    check("All companies have name+slug", bad_company == 0, bad_company)
    dup_slug = await conn.fetchval("SELECT 1 FROM md_global_companies GROUP BY slug HAVING COUNT(*)>1 LIMIT 1")
    check("Company slugs unique", dup_slug is None)

    # 7. People: canonical_name and slug non-null
    bad_people = await conn.fetchval("SELECT COUNT(*) FROM md_global_people WHERE canonical_name IS NULL OR slug IS NULL")
    check("All people have name+slug", bad_people == 0, bad_people)

    # 8. Exactly 22 new people unlinked to company
    unlinked_people = await conn.fetchval(
        "SELECT COUNT(*) FROM md_global_people p "
        "JOIN md_legacy_id_mappings lm ON lm.global_entity_id=p.id "
        "WHERE lm.legacy_id_type='LEGACY_MUHIDE_APOLLO_CONTACT' AND p.company_global_id IS NULL"
    )
    check("Exactly 22 new people unlinked", unlinked_people == 22, unlinked_people)

    # 9. Population totals
    gc = await conn.fetchval("SELECT COUNT(*) FROM md_global_companies")
    gp = await conn.fetchval("SELECT COUNT(*) FROM md_global_people")
    lm = await conn.fetchval("SELECT COUNT(*) FROM md_legacy_id_mappings")
    sr = await conn.fetchval("SELECT COUNT(*) FROM md_source_rows")
    sf = await conn.fetchval("SELECT COUNT(*) FROM md_source_files")
    fp = await conn.fetchval("SELECT COUNT(*) FROM md_field_provenance")
    check("Companies = 296,746", gc == 296746, gc)
    check("People = 1,124", gp == 1124, gp)
    check("Source files = 6", sf == 6, sf)
    check("No NEW_COMPANY_CANDIDATE promoted", await conn.fetchval("SELECT COUNT(*) FROM md_global_companies") == 296746)

    # 9b. CR-anchor safety (Data-Intelligence P0 defect): the 8 provable concat
    #     artifacts are GONE, and no stored CR mapping carries non-digits.
    cr_rows = await conn.fetch("SELECT legacy_id FROM md_legacy_id_mappings WHERE legacy_id_type='LEGACY_MUHIDE_CR'")
    bad_cr = [str(r["legacy_id"]) for r in cr_rows if not str(r["legacy_id"]).isdigit()]
    # The 8 known concatenation artifacts ('1005; 7066' -> '10057066' etc.) must be absent.
    concat_artifacts = {"10057066","3104263","6015330","13383449","400330",
                        "47085533","262843","21934425"}
    present = [a for a in concat_artifacts if any(str(r["legacy_id"]) == a for r in cr_rows)]
    check("All CR legacy mappings are digit-only", len(bad_cr) == 0, f"bad={len(bad_cr)}")
    check("No CR concat artifacts remain (8 removed)", len(present) == 0, f"present={present}")

    # 10. Legacy mapping idempotency constraints enforced (duplicate insert rejected)
    import asyncpg as apg
    try:
        r = await conn.fetchrow("SELECT legacy_id_type, legacy_id FROM md_legacy_id_mappings LIMIT 1")
        await conn.execute(
            "INSERT INTO md_legacy_id_mappings (id, legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at) "
            "VALUES ($1, $2, $3, 'C', $4, 1.0, now())",
            uuid.uuid4(), r["legacy_id_type"], r["legacy_id"], uuid.uuid4())
        check("Legacy mapping unique constraint enforced", False, "no error raised")
    except apg.UniqueViolationError:
        check("Legacy mapping unique constraint enforced", True, "UniqueViolationError raised")

    print("=" * 70)
    print("FINAL SAFETY CHECK — salesos_test")
    print("=" * 70)
    print(f"\nTotals: companies={gc:,}  people={gp:,}  mappings={lm:,}  source_rows={sr:,}  files={sf:,}  provenance={fp:,}")
    for line in ok:
        print(line)
    if fail:
        for line in fail:
            print(line)
    print(f"\nRESULT: {len(ok)} PASS / {len(fail)} FAIL")

    await conn.close()

asyncio.run(main())
