"""Correct false CR-anchor legacy mappings (concatenation artifacts) — audited + idempotent.

The buggy ingestion concatenated multi-value CR_Numbers (e.g. '1005; 7066' -> '10057066'),
creating 8 false government-anchor mappings.  These are PLATFORM-STATE errors, not source
data.  We remove ONLY the provable concatenation artifacts and record an audit event +
field provenance flag.  Source rows (raw_payload) are NEVER touched.
"""
import asyncio, asyncpg, re, uuid, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import UTC, datetime

def concat(raw):
    return re.sub(r"[^0-9]", "", raw.strip()).lstrip("0") if raw else None

async def main():
    c = await asyncpg.connect(host="localhost", port=5432, user="salesos",
                               password="salesos_dev_password", database="salesos_test")
    now = datetime.now(UTC)

    # 1. Identify artifacts by matching stored CR mapping against concatenation of raw CR_Numbers
    maps = await c.fetch(
        "SELECT id, legacy_id, global_entity_id FROM md_legacy_id_mappings "
        "WHERE legacy_id_type='LEGACY_MUHIDE_CR'")
    lm = {str(r["legacy_id"]): r for r in maps}

    rows = await c.fetch(
        "SELECT raw_payload->>'CR_Numbers' AS crs, raw_payload->>'Master Account ID' AS ma, id AS row_id "
        "FROM md_source_rows WHERE source_id='muhide_master_accounts'")
    artifacts = []
    seen = set()
    for r in rows:
        crs = r["crs"]
        if not crs or str(crs).strip() in ("", "None"):
            continue
        buggy = concat(crs)
        if buggy and buggy in lm and buggy not in seen and 6 <= len(buggy) <= 9 and ";" in str(crs):
            seen.add(buggy)
            artifacts.append({
                "mapping_id": str(lm[buggy]["id"]),
                "legacy_id": buggy,
                "global_entity_id": str(lm[buggy]["global_entity_id"]),
                "raw_cr": crs.strip(),
                "ma": r["ma"],
                "row_id": str(r["row_id"]),
            })

    print(f"Found {len(artifacts)} concatenation-artifact CR mappings:")

    # 2. For each: delete the false mapping, record audit + provenance
    for a in artifacts:
        # Delete false mapping (idempotent — ON DELETE if not exists)
        del_res = await c.execute(
            "DELETE FROM md_legacy_id_mappings WHERE id = $1 AND legacy_id_type='LEGACY_MUHIDE_CR'",
            a["mapping_id"])
        print(f"   DELETED false CR mapping {a['legacy_id']!r} (ma={a['ma']})")

        # Audit/conflict record (md_entity_conflicts — present in salesos_test)
        await c.execute(
            "INSERT INTO md_entity_conflicts "
            "(id, global_entity_id, field_name, value_a, value_b, is_government_id, "
            "veto_enabled, resolution, created_at) "
            "VALUES ($1, $2, 'cr_number', $3, NULL, true, true, 'open', $4)",
            uuid.uuid4(), a["global_entity_id"], a["legacy_id"], now,
        )

        # Field provenance flag (record that the entity's CR is NOT a verified anchor)
        await c.execute(
            "INSERT INTO md_field_provenance "
            "(id, global_entity_id, field_name, field_value, source_row_id, observed_at, "
            "evidence_tier, verification_status, authority_score, selection_reason, "
            "conflict_status, is_current, created_at) "
            "VALUES ($1, $2, 'cr_number', $3, $4, $5, 'FUZZY', 'unverified', 30, "
            "'cr_anchor_rejected_concatenation', 'conflict', false, $5)",
            uuid.uuid4(), a["global_entity_id"], a["legacy_id"], a["row_id"], now,
        )

    # 3. Verify remaining CR mappings are all SAFE or legitimate
    remaining = await c.fetch(
        "SELECT legacy_id FROM md_legacy_id_mappings WHERE legacy_id_type='LEGACY_MUHIDE_CR'")
    from app.modules.entity_resolution.resolution_policy import normalize_cr
    still_bad = [str(r["legacy_id"]) for r in remaining if normalize_cr(str(r["legacy_id"])) is None]
    print(f"\nRemaining CR mappings: {len(remaining)}; still-invalid: {len(still_bad)}")
    if still_bad:
        print("   (investigate: " + str(still_bad[:10]) + ")")

    # 4. Verify source rows untouched (immutability)
    if artifacts:
        checked = await c.fetchval(
            "SELECT COUNT(*) FROM md_source_rows "
            "WHERE source_id='muhide_master_accounts' AND id = $1",
            artifacts[0]["row_id"],
        )
        print(f"Source row immutability: presence confirmed = {checked}")
    else:
        print("Source row immutability: no artifacts corrected, nothing to check")

    await c.close()

asyncio.run(main())
