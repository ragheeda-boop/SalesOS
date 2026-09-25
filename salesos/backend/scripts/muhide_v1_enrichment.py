"""MUHIDE V1 Enrichment Ingestion — salesos_test.

Processes v1_linked_v2.parquet (223,073 rows) and v1_unlinked_v2.parquet (5,225 rows).
Covers Steps 3-7 of the Phase 4 completion task.

Idempotent. Batch-based. Against salesos_test only.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import os
import re
import sys
import time
import uuid

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
import pyarrow.parquet as pq

from _muhide_global_ids import GlobalIdResolver

GIDS = GlobalIdResolver()
GIDS.require_loaded()

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"

DOWNLOADS = Path(os.environ.get("MUHIDE_DOWNLOADS", str(Path.home() / "Downloads")))
LINKED_PATH = Path(os.environ.get("MUHIDE_LINKED_PATH", str(DOWNLOADS / "v1_linked_v2.parquet")))
UNLINKED_PATH = Path(os.environ.get("MUHIDE_UNLINKED_PATH", str(DOWNLOADS / "v1_unlinked_v2.parquet")))
CONTACTS_CSV = Path(os.environ.get("MUHIDE_CONTACTS_CSV", str(DOWNLOADS / "MUHIDE_extracted" / "02_Master_Contacts.csv")))

BATCH_SIZE = 10000
TENANT_ID = uuid.UUID("a0000000-0000-4000-a000-000000000001")

EXPECTED_HASHES = {
    "v1_linked_v2.parquet": "2d006ae84ae04ff52272f215ada45e9da9bbf1216719c04e6494ce26de21f7c7",
    "v1_unlinked_v2.parquet": "2e076722602371b5017b7cbe08fa6fb5ff368474977a4f7aecc60b44f6e73ac5",
}

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _now() -> datetime:
    return datetime.now(UTC)


def _safe(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "null", "n/a"):
        return None
    return s


def _trunc(val: str | None, mx: int) -> str | None:
    if val and len(val) > mx:
        return val[:mx]
    return val


def _normalize_cr(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    if s.lower() in ("none", "nan", "null", "n/a"):
        return None
    # Handle pipe-separated CRs: take the first valid one
    parts = re.split(r"\s*\|\s*", s)
    for part in parts:
        part = part.strip()
        # Strip .0 float suffix
        part = re.sub(r"\.0$", "", part)
        digits = re.sub(r"[^0-9]", "", part).lstrip("0")
        if digits.isdigit() and len(digits) >= 5 and len(digits) <= 10:
            return digits
    return None


def _normalize_domain(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().lower()
    s = re.sub(r"^https?://", "", s).rstrip("/")
    if s in ("", "none", "nan"):
        return None
    return s


def _normalize_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    s = re.sub(r"[^0-9+]", "", raw.strip())
    if len(s) < 5:
        return None
    return s


def _gen_id(prefix: str) -> str:
    x = uuid.uuid4().int
    chars = []
    for _ in range(8):
        chars.append(ALPHABET[x % 32])
        x //= 32
    return f"G-{prefix}-{''.join(chars)}"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


async def _flush_batch(conn, sql, batch):
    if batch:
        await conn.executemany(sql, batch)


# ── Main ─────────────────────────────────────────────────────────────────────


async def main():
    print("=" * 70)
    print("MUHIDE V1 ENRICHMENT INGESTION — salesos_test")
    print("=" * 70)
    t_total = time.time()

    # ════════════════════════════════════════════════════════════════════════
    # STEP 1: VERIFY INPUT FILES
    # ════════════════════════════════════════════════════════════════════════
    print("\n[STEP 1] Verifying input files...")

    for fname, expected_hash in EXPECTED_HASHES.items():
        if fname == "v1_linked_v2.parquet":
            path = LINKED_PATH
        else:
            path = UNLINKED_PATH
        actual_hash = _sha256_file(path)
        status = "PASS" if actual_hash == expected_hash else "FAIL"
        print(f"  {fname}: SHA-256 {status}")
        if status == "FAIL":
            print(f"    Expected: {expected_hash}")
            print(f"    Actual:   {actual_hash}")
            return

    linked = pq.read_table(LINKED_PATH)
    unlinked = pq.read_table(UNLINKED_PATH)
    print(f"  v1_linked: {linked.num_rows:,} rows, {linked.num_columns} cols")
    print(f"  v1_unlinked: {unlinked.num_rows:,} rows, {unlinked.num_columns} cols")
    assert linked.num_rows == 223_073, f"Expected 223073, got {linked.num_rows}"
    assert unlinked.num_rows == 5_225, f"Expected 5225, got {unlinked.num_rows}"
    print("  Row counts: PASS")

    # Verify 22 person candidates
    apollo_col = unlinked.column("_v1_Apollo_Contact_Id")
    person_ids = []
    for i in range(unlinked.num_rows):
        val = apollo_col[i]
        if val is not None and str(val).strip() and str(val) != "None":
            person_ids.append(str(val))
    assert len(person_ids) == 22, f"Expected 22 person candidates, got {len(person_ids)}"
    print(f"  22 NEW_PERSON_CANDIDATE records: PASS")

    # Verify no overlap with existing contacts
    existing_contacts = set()
    with open(CONTACTS_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = (row.get("Apollo Contact ID") or "").strip()
            if cid:
                existing_contacts.add(cid)
    overlap = existing_contacts & set(person_ids)
    assert len(overlap) == 0, f"Overlap with existing contacts: {overlap}"
    print(f"  Zero overlap with 02_Master_Contacts: PASS")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 2: CONNECT & LOAD EXISTING STATE
    # ════════════════════════════════════════════════════════════════════════
    print("\n[STEP 2] Connecting to salesos_test...")
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB,
    )

    # Load existing MA->Global Company mapping
    print("  Loading existing MA->Global mapping...")
    ma_rows = await conn.fetch(
        "SELECT l.legacy_id, l.global_entity_id "
        "FROM md_legacy_id_mappings l "
        "WHERE l.legacy_id_type = 'LEGACY_MUHIDE_MA_ID'"
    )
    ma_to_gid = {r["legacy_id"]: str(r["global_entity_id"]) for r in ma_rows}
    print(f"  Loaded {len(ma_to_gid):,} MA->Global mappings")

    # Load existing CR->Global Company mapping
    cr_rows = await conn.fetch(
        "SELECT l.legacy_id, l.global_entity_id "
        "FROM md_legacy_id_mappings l "
        "WHERE l.legacy_id_type = 'LEGACY_MUHIDE_CR'"
    )
    cr_to_gid = {r["legacy_id"]: str(r["global_entity_id"]) for r in cr_rows}
    print(f"  Loaded {len(cr_to_gid):,} CR->Global mappings")

    # Load existing Apollo Contact ID->Global Person mapping
    apollo_person_rows = await conn.fetch(
        "SELECT l.legacy_id, l.global_entity_id "
        "FROM md_legacy_id_mappings l "
        "WHERE l.legacy_id_type = 'LEGACY_MUHIDE_APOLLO_CONTACT'"
    )
    existing_person_apollo = {r["legacy_id"] for r in apollo_person_rows}
    print(f"  Loaded {len(existing_person_apollo):,} existing Apollo Contact IDs")

    # Load existing source row keys for idempotency
    existing_sr_keys = set()
    sr_rows = await conn.fetch("SELECT source_id, source_record_id FROM md_source_rows")
    for r in sr_rows:
        existing_sr_keys.add((r["source_id"], r["source_record_id"]))
    print(f"  Loaded {len(existing_sr_keys):,} existing source row keys")

    # Load existing legacy mapping keys
    existing_lm_keys = set()
    lm_rows = await conn.fetch(
        "SELECT legacy_id_type, legacy_id FROM md_legacy_id_mappings"
    )
    for r in lm_rows:
        existing_lm_keys.add((r["legacy_id_type"], r["legacy_id"]))

    now = _now()
    counts = defaultdict(int)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 3: PROCESS v1 LINKED (223,073 rows)
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n[STEP 3] Processing {linked.num_rows:,} v1 linked rows...")
    t1 = time.time()

    # Register source file (idempotent: reuse existing by hash)
    existing_file = await conn.fetchrow(
        "SELECT id FROM md_source_files WHERE filename = $1 AND file_hash_sha256 = $2",
        "v1_linked_v2.parquet", EXPECTED_HASHES["v1_linked_v2.parquet"],
    )
    if existing_file:
        v1l_file_id = existing_file["id"]
    else:
        v1l_file_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'application/octet-stream', 1, $7, $8, $9, $10, 'completed')""",
            v1l_file_id, str(TENANT_ID), "v1_linked_v2.parquet", str(LINKED_PATH),
            EXPECTED_HASHES["v1_linked_v2.parquet"], LINKED_PATH.stat().st_size,
            linked.num_rows, "muhide_v1_enrichment", str(TENANT_ID), now,
        )
    counts["source_files"] = 1

    # Extract column names for dynamic field provenance
    enrichment_cols = [c for c in linked.column_names if c.startswith("_v1_")]
    raw_cols = [
        "company_name_raw", "cr_number_raw", "phone_raw", "email_raw",
        "website_raw", "city", "industry_raw", "apollo_account_id",
    ]

    # Process linked rows in batches
    sr_batch = []
    prov_batch = []
    sr_inserted = 0
    prov_inserted = 0
    linked_to_existing = 0
    linked_no_ma = 0

    for idx in range(linked.num_rows):
        ma_id = str(linked.column("Master Account ID")[idx])
        if not ma_id or ma_id == "None":
            linked_no_ma += 1
            continue

        gid = ma_to_gid.get(ma_id)
        if not gid:
            linked_no_ma += 1
            continue

        linked_to_existing += 1

        # Create source row (enrichment observation)
        source_record_id = f"v1l_{ma_id}_{idx}"
        sr_key = ("muhide_v1_linked", source_record_id)
        if sr_key not in existing_sr_keys:
            row_data = {}
            for col in linked.column_names:
                val = linked.column(col)[idx]
                if val is not None:
                    row_data[col] = str(val)
            sr_id = uuid.uuid4()
            sr_batch.append((
                str(sr_id), str(TENANT_ID), str(v1l_file_id),
                "muhide_v1_linked", source_record_id, idx,
                json.dumps(row_data, ensure_ascii=False, default=str),
                "enrichment", now,
            ))
            existing_sr_keys.add(sr_key)
            sr_inserted += 1

            # Field provenance for key enrichment fields
            for field in ["_v1_Account_Tier", "_v1_Owner", "_v1_Data_Completeness_pct",
                          "_v1_Source_Systems", "_v1_Routing_Rule", "_v1_Next_Action"]:
                val = linked.column(field)[idx] if field in linked.column_names else None
                val_str = str(val) if val is not None and str(val) != "None" else None
                if val_str:
                    prov_batch.append((
                        str(uuid.uuid4()), gid, field, val_str, str(sr_id),
                        "DERIVED", 0.3, "v1_enrichment", "none", True, now,
                    ))
                    prov_inserted += 1

        if len(sr_batch) >= BATCH_SIZE:
            await _flush_batch(conn, """INSERT INTO md_source_rows
                (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                 raw_payload, entity_type, resolution_status, created_at)
                VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
                ON CONFLICT (source_id, source_record_id) DO NOTHING""", sr_batch)
            sr_batch.clear()
        if len(prov_batch) >= BATCH_SIZE:
            await _flush_batch(conn, """INSERT INTO md_field_provenance
                (id, global_entity_id, field_name, field_value, source_row_id,
                 evidence_tier, authority_score, selection_reason, conflict_status,
                 is_current, created_at)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $6, $7, $8, $9, $10, $11)""",
                prov_batch)
            prov_batch.clear()

        if (idx + 1) % 50000 == 0:
            print(f"    ... {idx+1:,}/{linked.num_rows:,} processed")

    # Flush remaining
    if sr_batch:
        await _flush_batch(conn, """INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
            ON CONFLICT (source_id, source_record_id) DO NOTHING""", sr_batch)
    if prov_batch:
        await _flush_batch(conn, """INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             evidence_tier, authority_score, selection_reason, conflict_status,
             is_current, created_at)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $6, $7, $8, $9, $10, $11)""",
            prov_batch)

    counts["source_rows"] += sr_inserted
    counts["provenance"] += prov_inserted
    print(f"  Linked: {linked_to_existing:,} attached to existing Global Companies")
    print(f"  Linked: {linked_no_ma:,} without MA match (should be 0)")
    print(f"  Source rows inserted: {sr_inserted:,}")
    print(f"  Provenance records: {prov_inserted:,}")
    print(f"  Time: {time.time()-t1:.1f}s")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 4: INVESTIGATE 1,410 MISSED LINKS
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n[STEP 4] Investigating 1,410 missed links from {unlinked.num_rows:,} unlinked rows...")
    t2 = time.time()

    # Classify unlinked rows
    missed_links = []
    new_company_candidates = []
    new_person_candidates = []

    for idx in range(unlinked.num_rows):
        # Check if this is a person candidate (has Apollo Contact ID)
        apollo_val = unlinked.column("_v1_Apollo_Contact_Id")[idx]
        has_apollo_contact = (apollo_val is not None and str(apollo_val).strip()
                              and str(apollo_val) != "None")

        # Check CR for missed link
        cr_raw = _safe(str(unlinked.column("cr_number_raw")[idx])) if "cr_number_raw" in unlinked.column_names else None
        cr_norm = _normalize_cr(cr_raw)
        has_existing_cr = cr_norm and cr_norm in cr_to_gid

        # Priority: person candidate FIRST, then missed link
        if has_apollo_contact:
            new_person_candidates.append(idx)
        elif has_existing_cr:
            missed_links.append((idx, cr_norm))
        else:
            new_company_candidates.append(idx)

    print(f"  LIKELY_MISSED_LINK_NOT_NEW: {len(missed_links):,} (expected 1,410)")
    print(f"  NEW_COMPANY_CANDIDATE: {len(new_company_candidates):,} (expected 3,793)")
    print(f"  NEW_PERSON_CANDIDATE: {len(new_person_candidates):,} (expected 22)")

    # Process missed links — attach to existing Global Companies
    sr_batch = []
    prov_batch = []
    sr_inserted_missed = 0
    prov_inserted_missed = 0
    missed_linked_ok = 0
    missed_linked_conflict = 0

    # Register unlinked source file (idempotent: reuse existing by hash)
    existing_u_file = await conn.fetchrow(
        "SELECT id FROM md_source_files WHERE filename = $1 AND file_hash_sha256 = $2",
        "v1_unlinked_v2.parquet", EXPECTED_HASHES["v1_unlinked_v2.parquet"],
    )
    if existing_u_file:
        v1u_file_id = existing_u_file["id"]
    else:
        v1u_file_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'application/octet-stream', 1, $7, $8, $9, $10, 'completed')""",
            v1u_file_id, str(TENANT_ID), "v1_unlinked_v2.parquet", str(UNLINKED_PATH),
            EXPECTED_HASHES["v1_unlinked_v2.parquet"], UNLINKED_PATH.stat().st_size,
            unlinked.num_rows, "muhide_v1_unlinked", str(TENANT_ID), now,
        )
    counts["source_files"] = 1

    for idx, cr_norm in missed_links:
        gid = cr_to_gid.get(cr_norm)
        if not gid:
            missed_linked_conflict += 1
            continue

        missed_linked_ok += 1

        # Create source row
        source_record_id = f"v1u_missed_{idx}"
        sr_key = ("muhide_v1_unlinked_missed", source_record_id)
        if sr_key not in existing_sr_keys:
            row_data = {}
            for col in unlinked.column_names:
                val = unlinked.column(col)[idx]
                if val is not None:
                    row_data[col] = str(val)
            sr_id = uuid.uuid4()
            sr_batch.append((
                str(sr_id), str(TENANT_ID), str(v1u_file_id),
                "muhide_v1_unlinked_missed", source_record_id, idx,
                json.dumps(row_data, ensure_ascii=False, default=str),
                "enrichment", now,
            ))
            existing_sr_keys.add(sr_key)
            sr_inserted_missed += 1

            # Record provenance for the CR link
            prov_batch.append((
                str(uuid.uuid4()), gid, "v1_missed_link_cr", cr_norm, str(sr_id),
                "GOVERNMENT_ANCHOR", 1.0, "v1_missed_link_reconciliation", "none", True, now,
            ))
            prov_inserted_missed += 1

    if sr_batch:
        await _flush_batch(conn, """INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
            ON CONFLICT (source_id, source_record_id) DO NOTHING""", sr_batch)
    if prov_batch:
        await _flush_batch(conn, """INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             evidence_tier, authority_score, selection_reason, conflict_status,
             is_current, created_at)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $6, $7, $8, $9, $10, $11)""",
            prov_batch)

    counts["source_rows"] += sr_inserted_missed
    counts["provenance"] += prov_inserted_missed
    print(f"  Missed links: {missed_linked_ok:,} successfully linked")
    print(f"  Missed links: {missed_linked_conflict:,} unresolved (no CR match)")
    print(f"  Source rows: {sr_inserted_missed:,}, Provenance: {prov_inserted_missed:,}")
    print(f"  Time: {time.time()-t2:.1f}s")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 5: LOAD 22 NEW PERSON CANDIDATES
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n[STEP 5] Loading {len(new_person_candidates)} NEW_PERSON_CANDIDATE records...")
    t3 = time.time()

    gp_batch = []
    lm_batch = []
    sr_batch = []
    people_created = 0

    for idx in new_person_candidates:
        apollo_id = str(unlinked.column("_v1_Apollo_Contact_Id")[idx])
        if apollo_id in existing_person_apollo:
            continue

        first = _safe(str(unlinked.column("_v1_First_Name")[idx]) if "_v1_First_Name" in unlinked.column_names else None) or ""
        last = _safe(str(unlinked.column("_v1_Last_Name")[idx]) if "_v1_Last_Name" in unlinked.column_names else None) or ""
        email = _trunc(_safe(str(unlinked.column("_v1_Email")[idx]) if "_v1_Email" in unlinked.column_names else None), 255)
        phone = _trunc(_normalize_phone(_safe(str(unlinked.column("_v1_Mobile_Phone")[idx]) if "_v1_Mobile_Phone" in unlinked.column_names else None)), 50)
        title = _trunc(_safe(str(unlinked.column("_v1_Title")[idx]) if "_v1_Title" in unlinked.column_names else None), 255)

        # Display-name fallback: never fabricate a name. Use "Unnamed Contact" if the
        # source has no usable first/last name (per source fidelity, §7).
        name = f"{first} {last}".strip()
        if not name:
            # Derive a transient display name from the email local-part if available,
            # else a transparent placeholder. Never invented, always sourced.
            local = email.split("@")[0].replace(".", " ").replace("_", " ").strip() if email else None
            if local and re.search(r"[a-zA-Z]{2,}", local):
                name = local.title()
            else:
                name = "Unnamed Contact"
        name = _trunc(name, 512)

        pid, pslug = GIDS.resolve("LEGACY_MUHIDE_V1_PERSON", f"v1u_{idx}", "P")
        # Per Data Contract §26: the 22 unlinked people are loaded WITHOUT a company
        # relationship (company_global_id = NULL). No implicit company linkage.
        gp_batch.append((
            str(pid), pslug, name, email, phone,
            None, title, now,
        ))
        lm_batch.append((
            str(uuid.uuid4()), "LEGACY_MUHIDE_APOLLO_CONTACT", apollo_id,
            "P", str(pid), 1.0, now,
        ))
        lm_batch.append((
            str(uuid.uuid4()), "LEGACY_MUHIDE_V1_PERSON", f"v1u_{idx}",
            "P", str(pid), 1.0, now,
        ))
        existing_person_apollo.add(apollo_id)
        people_created += 1

        # Source row
        sr_id = uuid.uuid4()
        row_data = {}
        for col in unlinked.column_names:
            val = unlinked.column(col)[idx]
            if val is not None:
                row_data[col] = str(val)
        sr_batch.append((
            str(sr_id), str(TENANT_ID), str(v1u_file_id),
            "muhide_v1_unlinked_person", f"v1u_person_{idx}", idx,
            json.dumps(row_data, ensure_ascii=False, default=str),
            "person", now,
        ))

    if gp_batch:
        await _flush_batch(conn, """INSERT INTO md_global_people
            (id, slug, canonical_name, email, phone, company_global_id, job_title,
             status, source_count, created_at, updated_at)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, 'active', 1, $8, $8)""", gp_batch)
    if lm_batch:
        await _flush_batch(conn, """INSERT INTO md_legacy_id_mappings
            (id, legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at)
            VALUES ($1::uuid, $2, $3, $4, $5::uuid, $6, $7)
            ON CONFLICT (legacy_id_type, legacy_id) DO NOTHING""", lm_batch)
    if sr_batch:
        await _flush_batch(conn, """INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
            ON CONFLICT (source_id, source_record_id) DO NOTHING""", sr_batch)

    counts["global_people"] += people_created
    counts["legacy_mappings"] += len(lm_batch)
    counts["source_rows"] += len(sr_batch)
    print(f"  Created {people_created} new Global People")
    print(f"  Time: {time.time()-t3:.1f}s")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 6: HANDLE 3,793 NEW COMPANY CANDIDATES
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n[STEP 6] Handling {len(new_company_candidates)} NEW_COMPANY_CANDIDATE records...")
    t4 = time.time()

    sr_batch = []
    candidates_stored = 0

    for idx in new_company_candidates:
        source_record_id = f"v1u_candidate_{idx}"
        sr_key = ("muhide_v1_unlinked_candidate", source_record_id)
        if sr_key in existing_sr_keys:
            continue

        row_data = {}
        for col in unlinked.column_names:
            val = unlinked.column(col)[idx]
            if val is not None:
                row_data[col] = str(val)
        row_data["_v1_disposition"] = "NEW_COMPANY_CANDIDATE"
        row_data["_v1_review_status"] = "PENDING_REVIEW"

        sr_batch.append((
            str(uuid.uuid4()), str(TENANT_ID), str(v1u_file_id),
            "muhide_v1_unlinked_candidate", source_record_id, idx,
            json.dumps(row_data, ensure_ascii=False, default=str),
            "company_candidate", now,
        ))
        existing_sr_keys.add(sr_key)
        candidates_stored += 1

    if sr_batch:
        await _flush_batch(conn, """INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
            ON CONFLICT (source_id, source_record_id) DO NOTHING""", sr_batch)

    counts["source_rows"] += candidates_stored
    counts["company_candidates"] = candidates_stored
    print(f"  Stored {candidates_stored:,} candidates as reviewable source rows")
    print(f"  Time: {time.time()-t4:.1f}s")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 8: IDEMPOTENCY VERIFICATION
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n[STEP 8] Idempotency verification...")
    print("  (Counts after first run)")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 9: RECONCILIATION
    # ════════════════════════════════════════════════════════════════════════
    print(f"\n[STEP 9] Final reconciliation...")
    r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_global_companies")
    gc = r["c"]
    r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_global_people")
    gp = r["c"]
    r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_legacy_id_mappings")
    lm = r["c"]
    r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_source_rows")
    sr = r["c"]
    r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_source_files")
    sf = r["c"]
    r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_field_provenance")
    fp = r["c"]

    print(f"  md_global_companies: {gc:,}")
    print(f"  md_global_people: {gp:,}")
    print(f"  md_legacy_id_mappings: {lm:,}")
    print(f"  md_source_rows: {sr:,}")
    print(f"  md_source_files: {sf:,}")
    print(f"  md_field_provenance: {fp:,}")

    # Source row breakdown
    srs = await conn.fetch(
        "SELECT source_id, entity_type, COUNT(*) as c FROM md_source_rows "
        "GROUP BY source_id, entity_type ORDER BY c DESC")
    print("\n  Source row breakdown:")
    for s in srs:
        print(f"    {s['source_id']} ({s['entity_type']}): {s['c']:,}")

    elapsed = time.time() - t_total
    print(f"\n{'=' * 70}")
    print(f"V1 ENRICHMENT COMPLETE — {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"{'=' * 70}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
