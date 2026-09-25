"""MUHIDE v2 Real Data Ingestion — salesos_test (BULK version).

Uses bulk executemany for all entity creation. Processes 296K accounts
in batches instead of row-by-row.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import asyncpg

from _muhide_global_ids import GlobalIdResolver

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"

DOWNLOADS = Path(os.environ.get("MUHIDE_DOWNLOADS", str(Path.home() / "Downloads")))
EXTRACT_DIR = Path(os.environ.get("MUHIDE_EXTRACT_DIR", str(DOWNLOADS / "MUHIDE_extracted")))
CANDIDATES_CSV = Path(os.environ.get("MUHIDE_CANDIDATES_CSV", str(DOWNLOADS / "MUHIDE_resolution_candidates.csv")))
REVIEW_CSV = Path(os.environ.get("MUHIDE_REVIEW_CSV", str(DOWNLOADS / "04_ER_Review" / "04_Entity_Resolution_Review.csv")))

BATCH_SIZE = 10000
TENANT_ID = uuid.UUID("a0000000-0000-4000-a000-000000000001")

PHASE0_DDL = """
CREATE TABLE IF NOT EXISTS md_global_companies (
    id UUID PRIMARY KEY, slug VARCHAR(64) NOT NULL, canonical_name VARCHAR(512) NOT NULL,
    canonical_name_ar VARCHAR(512), canonical_name_en VARCHAR(512), cr_number VARCHAR(50),
    vat_number VARCHAR(50), unified_national_number VARCHAR(50), domain VARCHAR(255),
    website VARCHAR(512), city VARCHAR(100), region VARCHAR(100), country VARCHAR(100) NOT NULL DEFAULT 'Saudi Arabia',
    industry VARCHAR(255), legal_entity_type VARCHAR(32) NOT NULL DEFAULT 'company',
    status VARCHAR(32) NOT NULL DEFAULT 'active', confidence_score FLOAT NOT NULL DEFAULT 0.0,
    source_count INT NOT NULL DEFAULT 1, phone VARCHAR(50), email VARCHAR(255),
    address TEXT, latitude FLOAT, longitude FLOAT, metadata JSONB NOT NULL DEFAULT '{}',
    merged_from_ids JSONB, merged_at TIMESTAMPTZ, split_from_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_companies_slug ON md_global_companies (slug);

CREATE TABLE IF NOT EXISTS md_global_people (
    id UUID PRIMARY KEY, slug VARCHAR(64) NOT NULL, canonical_name VARCHAR(512) NOT NULL,
    email VARCHAR(255), phone VARCHAR(50), company_global_id UUID,
    job_title VARCHAR(255), linkedin_url VARCHAR(512),
    confidence_score FLOAT NOT NULL DEFAULT 0.0, source_count INT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'active', metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_people_slug ON md_global_people (slug);

CREATE TABLE IF NOT EXISTS md_legacy_id_mappings (
    id UUID PRIMARY KEY, legacy_id_type VARCHAR(32) NOT NULL, legacy_id VARCHAR(255) NOT NULL,
    global_entity_type VARCHAR(32) NOT NULL, global_entity_id UUID NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_legacy_id_lookup ON md_legacy_id_mappings (legacy_id_type, legacy_id);

CREATE TABLE IF NOT EXISTS md_source_files (
    id UUID PRIMARY KEY, tenant_id UUID NOT NULL, filename VARCHAR(512) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL, file_hash_sha256 VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT NOT NULL, mime_type VARCHAR(128) NOT NULL,
    sheet_count INT NOT NULL, total_rows INT NOT NULL, source_system VARCHAR(64) NOT NULL,
    schema_mapping JSONB, uploaded_by UUID NOT NULL, uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded', deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS md_source_rows (
    id UUID PRIMARY KEY, tenant_id UUID NOT NULL, source_file_id UUID NOT NULL,
    source_id VARCHAR(64) NOT NULL, source_record_id VARCHAR(255) NOT NULL,
    row_number INT NOT NULL, sheet_name VARCHAR(255), raw_payload JSONB NOT NULL,
    normalized_payload JSONB, entity_type VARCHAR(32) NOT NULL DEFAULT 'company',
    global_entity_id UUID, resolution_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    resolution_confidence FLOAT, resolution_method VARCHAR(64), import_batch_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_source_rows_source ON md_source_rows (source_id, source_record_id);

CREATE TABLE IF NOT EXISTS md_entity_matches (
    id UUID PRIMARY KEY, global_entity_id UUID, source_a_id VARCHAR(255) NOT NULL,
    source_b_id VARCHAR(255) NOT NULL, match_score FLOAT NOT NULL DEFAULT 0.0,
    match_method VARCHAR(64) NOT NULL, match_signals JSONB NOT NULL DEFAULT '[]',
    match_status VARCHAR(32) NOT NULL DEFAULT 'pending_review',
    reviewed_by UUID, reviewed_at TIMESTAMPTZ, review_decision VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_entity_matches_pair ON md_entity_matches (source_a_id, source_b_id);

CREATE TABLE IF NOT EXISTS md_entity_conflicts (
    id UUID PRIMARY KEY, global_entity_id UUID, field_name VARCHAR(128) NOT NULL,
    value_a TEXT, source_a_id VARCHAR(255), source_a_priority INT DEFAULT 0,
    value_b TEXT, source_b_id VARCHAR(255), source_b_priority INT DEFAULT 0,
    is_government_id BOOLEAN NOT NULL DEFAULT false, veto_enabled BOOLEAN NOT NULL DEFAULT false,
    resolution VARCHAR(32) NOT NULL DEFAULT 'open', resolved_value TEXT,
    resolved_by UUID, resolved_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS md_entity_merge_history (
    id UUID PRIMARY KEY, operation VARCHAR(32) NOT NULL, target_entity_id UUID NOT NULL,
    source_entity_ids JSONB NOT NULL DEFAULT '[]', match_score FLOAT, match_method VARCHAR(64),
    performed_by UUID, performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    rollback_available BOOLEAN NOT NULL DEFAULT true, rolled_back_at TIMESTAMPTZ,
    details JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS md_field_provenance (
    id UUID PRIMARY KEY, global_entity_id UUID NOT NULL, field_name VARCHAR(128) NOT NULL,
    field_value TEXT NOT NULL, source_row_id UUID, source_file_id UUID,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(), evidence_tier VARCHAR(64) NOT NULL,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'unverified',
    verified_by UUID, verified_at TIMESTAMPTZ, authority_score FLOAT NOT NULL DEFAULT 0.0,
    selection_reason VARCHAR(128), conflict_status VARCHAR(32) NOT NULL DEFAULT 'none',
    is_current BOOLEAN NOT NULL DEFAULT true, superseded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_md_field_provenance_entity ON md_field_provenance (global_entity_id, field_name);

CREATE TABLE IF NOT EXISTS md_quality_scores (
    id UUID PRIMARY KEY, global_entity_id UUID NOT NULL,
    completeness_score FLOAT NOT NULL DEFAULT 0.0, accuracy_score FLOAT NOT NULL DEFAULT 0.0,
    consistency_score FLOAT NOT NULL DEFAULT 0.0, freshness_score FLOAT NOT NULL DEFAULT 0.0,
    provenance_score FLOAT NOT NULL DEFAULT 0.0, overall_score FLOAT NOT NULL DEFAULT 0.0,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT now(), details JSONB NOT NULL DEFAULT '{}'
);
"""


def _now() -> datetime:
    return datetime.now(UTC)

def _safe(val) -> str | None:
    if val is None: return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "null", "n/a"): return None
    return s

def _trunc(val: str | None, mx: int) -> str | None:
    if val and len(val) > mx: return val[:mx]
    return val

def _normalize_cr(raw: str | None) -> str | None:
    # Delegate to the canonical safe normalizer (separator-aware, reject concat/ambiguous).
    from app.modules.entity_resolution.resolution_policy import normalize_cr
    return normalize_cr(raw)

def _normalize_domain(raw: str | None) -> str | None:
    if not raw: return None
    s = raw.strip().lower()
    s = re.sub(r'^https?://', '', s).rstrip('/')
    if s in ('', 'none', 'nan'): return None
    return s

def _normalize_phone(raw: str | None) -> str | None:
    if not raw: return None
    s = re.sub(r'[^0-9+]', '', raw.strip())
    if len(s) < 5: return None
    return s

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

def _gen_id(prefix: str) -> str:
    x = uuid.uuid4().int
    chars = []
    for _ in range(8):
        chars.append(ALPHABET[x % 32])
        x //= 32
    return f"G-{prefix}-{''.join(chars)}"


async def main():
    print("MUHIDE v2 BULK Ingestion — salesos_test")
    print("=" * 60)
    t_total = time.time()

    # Must be resolved before the TRUNCATE below: a restore without pins would
    # re-key every existing account (report 94).
    GIDS = GlobalIdResolver()
    GIDS.require_loaded()
    print(f"Global ID pins: {len(GIDS.pins):,} from {GIDS.pins_path}")

    conn = await asyncpg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB)
    try:
        await conn.execute(PHASE0_DDL)

        # Clear the dedicated test database between deterministic restore runs.
        # Source evidence is append-only at the row level, so DELETE is
        # deliberately rejected by the database guard.  This script is
        # hard-wired to salesos_test; TRUNCATE is the explicit test reset and
        # leaves production/source immutability untouched.
        reset_tables = [
            'md_field_provenance','md_quality_scores','md_entity_merge_history',
            'md_entity_conflicts','md_entity_matches','md_source_rows','md_source_files',
            'md_legacy_id_mappings','md_global_people','md_global_companies',
        ]
        await conn.execute(
            'TRUNCATE TABLE ' + ', '.join(reset_tables) + ' RESTART IDENTITY CASCADE'
        )
        print("Tables cleared.")

        now = _now()
        counts = defaultdict(int)
        ma_to_gid = {}  # MA-xxx → UUID (as string)
        ma_to_sr = {}   # MA-xxx → source_row_id (UUID)

        # ═══════════════════════════════════════════════════════════════
        # FILE 1: 01_Master_Accounts.csv (296,746 rows)
        # ═══════════════════════════════════════════════════════════════
        print("\n[1/4] 01_Master_Accounts.csv")
        t1 = time.time()
        accts_path = EXTRACT_DIR / "01_Master_Accounts.csv"
        with open(accts_path, "r", encoding="utf-8") as f:
            acct_rows = list(csv.DictReader(f))
        print(f"  Read {len(acct_rows)} rows in {time.time()-t1:.1f}s")

        # Register source file
        acct_file_id = uuid.uuid4()
        acct_file_size = accts_path.stat().st_size
        await conn.execute(
            """INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'text/csv', 1, $7, $8, $9, $10, 'completed')""",
            acct_file_id, str(TENANT_ID), "01_Master_Accounts.csv", str(accts_path),
            "bulk_ingest", acct_file_size, len(acct_rows), "muhide_master_accounts",
            str(TENANT_ID), now,
        )
        counts["source_files"] = 1

        # Phase A: Bulk insert source rows (10K batches)
        print("  Phase A: Bulk source rows...")
        t2 = time.time()
        sr_batch = []
        sr_inserted = 0
        for idx, row in enumerate(acct_rows):
            ma_id = _safe(row.get("Master Account ID"))
            if not ma_id: continue
            sr_id = uuid.uuid4()
            ma_to_sr[ma_id] = sr_id
            sr_batch.append((str(sr_id), str(TENANT_ID), str(acct_file_id),
                             "muhide_master_accounts", ma_id, idx,
                             json.dumps(dict(row), ensure_ascii=False, default=str),
                             "company", now))
            if len(sr_batch) >= BATCH_SIZE:
                await conn.executemany(
                    """INSERT INTO md_source_rows
                    (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                     raw_payload, entity_type, resolution_status, created_at)
                    VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
                    ON CONFLICT (source_id, source_record_id) DO NOTHING""",
                    sr_batch)
                sr_inserted += len(sr_batch)
                sr_batch.clear()
        if sr_batch:
            await conn.executemany(
                """INSERT INTO md_source_rows
                (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                 raw_payload, entity_type, resolution_status, created_at)
                VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
                ON CONFLICT (source_id, source_record_id) DO NOTHING""",
                sr_batch)
            sr_inserted += len(sr_batch)
        counts["source_rows"] += sr_inserted
        print(f"  Phase A: {sr_inserted:,} source rows in {time.time()-t2:.1f}s")

        # Phase B: Bulk create Global Companies + legacy mappings
        print("  Phase B: Bulk global companies + legacy mappings...")
        t3 = time.time()
        gc_batch = []     # (id, slug, name, cr, city, domain, phone, email, industry, source_count, meta, now)
        lm_batch = []     # (id, type, legacy_id, entity_type, entity_id, confidence, now)
        prov_batch = []   # (id, entity_id, field, value, src_row_id, tier, authority, reason, conflict, is_current, now)

        for idx, row in enumerate(acct_rows):
            ma_id = _safe(row.get("Master Account ID"))
            if not ma_id: continue

            row_id, slug = GIDS.resolve("LEGACY_MUHIDE_MA_ID", ma_id, "C")
            ma_to_gid[ma_id] = str(row_id)
            canonical = _trunc(_safe(row.get("Canonical_Company_Name")) or f"Unknown-{ma_id}", 512)
            cr = _normalize_cr(_safe(row.get("CR_Numbers")))
            city = _trunc(_safe(row.get("City")), 100)
            domain = _trunc(_normalize_domain(_safe(row.get("Primary_Domain"))), 255)
            phone = _trunc(_normalize_phone(_safe(row.get("Primary_Phone"))), 50)
            email = _trunc(_safe(row.get("Primary_Email")), 255)
            industry = _trunc(_safe(row.get("Industry_Raw_Values")), 255)
            sc_str = _safe(row.get("Source_Count")) or _safe(row.get("Distinct_Source_System_Count"))
            sc = int(sc_str) if sc_str and sc_str.isdigit() else 1
            meta = json.dumps({"muhide_ma_id": ma_id})

            gc_batch.append((str(row_id), slug, canonical, cr, city, domain,
                             phone, email, industry, sc, meta, now))
            lm_batch.append((str(uuid.uuid4()), "LEGACY_MUHIDE_MA_ID", ma_id, "C",
                             str(row_id), 1.0, now))
            if cr:
                lm_batch.append((str(uuid.uuid4()), "LEGACY_MUHIDE_CR", cr, "C",
                                 str(row_id), 1.0, now))

            # Provenance for key fields
            sr_id = str(ma_to_sr.get(ma_id, uuid.uuid4()))
            if cr:
                prov_batch.append((str(uuid.uuid4()), str(row_id), "cr_number", cr, sr_id,
                                   "GOVERNMENT_ANCHOR", 1.0, "ingested", "none", True, now))
            if city:
                prov_batch.append((str(uuid.uuid4()), str(row_id), "city", city, sr_id,
                                   "STRONG_DETERMINISTIC", 0.7, "ingested", "none", True, now))
            if domain:
                prov_batch.append((str(uuid.uuid4()), str(row_id), "domain", domain, sr_id,
                                   "STRONG_DETERMINISTIC", 0.8, "ingested", "none", True, now))
            if phone:
                prov_batch.append((str(uuid.uuid4()), str(row_id), "phone", phone, sr_id,
                                   "WEAK_DETERMINISTIC", 0.4, "ingested", "none", True, now))
            if email:
                prov_batch.append((str(uuid.uuid4()), str(row_id), "email", email, sr_id,
                                   "WEAK_DETERMINISTIC", 0.4, "ingested", "none", True, now))
            if industry:
                prov_batch.append((str(uuid.uuid4()), str(row_id), "industry", industry, sr_id,
                                   "NORMALIZED_EXACT", 0.5, "ingested", "none", True, now))

            if len(gc_batch) >= BATCH_SIZE:
                await _flush_gc(conn, gc_batch)
                await _flush_lm(conn, lm_batch)
                await _flush_prov(conn, prov_batch)
                counts["global_companies"] += len(gc_batch)
                counts["legacy_mappings"] += len(lm_batch)
                counts["provenance_records"] += len(prov_batch)
                gc_batch.clear(); lm_batch.clear(); prov_batch.clear()
                if counts["global_companies"] % 50000 == 0:
                    print(f"    ... {counts['global_companies']:,} companies created")

        if gc_batch:
            await _flush_gc(conn, gc_batch)
            await _flush_lm(conn, lm_batch)
            await _flush_prov(conn, prov_batch)
            counts["global_companies"] += len(gc_batch)
            counts["legacy_mappings"] += len(lm_batch)
            counts["provenance_records"] += len(prov_batch)

        print(f"  Phase B: {counts['global_companies']:,} companies + {counts['legacy_mappings']:,} mappings + {counts['provenance_records']:,} provenance in {time.time()-t3:.1f}s")
        print(f"  [1/4] Total: {time.time()-t1:.1f}s")

        # ═══════════════════════════════════════════════════════════════
        # FILE 2: 03_Source_Map.csv (340,186 rows)
        # ═══════════════════════════════════════════════════════════════
        print("\n[2/4] 03_Source_Map.csv")
        t2 = time.time()
        sm_path = EXTRACT_DIR / "03_Source_Map.csv"
        with open(sm_path, "r", encoding="utf-8") as f:
            sm_rows = list(csv.DictReader(f))
        print(f"  Read {len(sm_rows)} rows in {time.time()-t2:.1f}s")

        sm_file_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'text/csv', 1, $7, $8, $9, $10, 'completed')""",
            sm_file_id, str(TENANT_ID), "03_Source_Map.csv", str(sm_path),
            "bulk_ingest", sm_path.stat().st_size, len(sm_rows), "muhide_source_map",
            str(TENANT_ID), now,
        )
        counts["source_files"] += 1

        # Bulk source rows
        sr_batch = []
        sr_inserted = 0
        for idx, row in enumerate(sm_rows):
            ma_id = _safe(row.get("Master Account ID")) or f"UNK-{idx}"
            src_sys = _safe(row.get("Source System")) or "unknown"
            src_rec = _safe(row.get("Source Record ID")) or f"REC-{idx}"
            comp_key = f"{ma_id}|{src_sys}|{src_rec}"
            sr_batch.append((str(uuid.uuid4()), str(TENANT_ID), str(sm_file_id),
                             "muhide_source_map", comp_key, idx,
                             json.dumps(dict(row), ensure_ascii=False, default=str),
                             "source_record", now))
            if len(sr_batch) >= BATCH_SIZE:
                await conn.executemany(
                    """INSERT INTO md_source_rows
                    (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                     raw_payload, entity_type, resolution_status, created_at)
                    VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
                    ON CONFLICT (source_id, source_record_id) DO NOTHING""",
                    sr_batch)
                sr_inserted += len(sr_batch)
                sr_batch.clear()
        if sr_batch:
            await conn.executemany(
                """INSERT INTO md_source_rows
                (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                 raw_payload, entity_type, resolution_status, created_at)
                VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
                ON CONFLICT (source_id, source_record_id) DO NOTHING""",
                sr_batch)
            sr_inserted += len(sr_batch)
        counts["source_rows"] += sr_inserted
        print(f"  {sr_inserted:,} source rows in {time.time()-t2:.1f}s")

        # Source-record legacy mappings are optional metadata — skip if type > 32 chars
        # The critical MA→Global mappings are already created above
        print(f"  Source map done. (Source-record legacy mappings deferred — type>32 chars)")

        # ═══════════════════════════════════════════════════════════════
        # FILE 3: 02_Master_Contacts.csv (1,102 rows)
        # ═══════════════════════════════════════════════════════════════
        print("\n[3/4] 02_Master_Contacts.csv")
        t3 = time.time()
        ct_path = EXTRACT_DIR / "02_Master_Contacts.csv"
        with open(ct_path, "r", encoding="utf-8") as f:
            ct_rows = list(csv.DictReader(f))
        print(f"  Read {len(ct_rows)} rows")

        ct_file_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'text/csv', 1, $7, $8, $9, $10, 'completed')""",
            ct_file_id, str(TENANT_ID), "02_Master_Contacts.csv", str(ct_path),
            "bulk_ingest", ct_path.stat().st_size, len(ct_rows), "muhide_contacts",
            str(TENANT_ID), now,
        )
        counts["source_files"] += 1

        # Source rows
        sr_batch = []
        for idx, row in enumerate(ct_rows):
            cid = _safe(row.get("Contact ID")) or f"CID-{idx}"
            sr_batch.append((str(uuid.uuid4()), str(TENANT_ID), str(ct_file_id),
                             "muhide_contacts", cid, idx,
                             json.dumps(dict(row), ensure_ascii=False, default=str),
                             "person", now))
        if sr_batch:
            await conn.executemany(
                """INSERT INTO md_source_rows
                (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                 raw_payload, entity_type, resolution_status, created_at)
                VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
                ON CONFLICT (source_id, source_record_id) DO NOTHING""",
                sr_batch)
            counts["source_rows"] += len(sr_batch)

        # Global People
        gp_batch = []
        lm_batch = []
        for row in ct_rows:
            cid = _safe(row.get("Contact ID"))
            if not cid: continue
            first = _safe(row.get("First Name")) or ""
            last = _safe(row.get("Last Name")) or ""
            name = _trunc(f"{first} {last}".strip() or f"Contact-{cid}", 512)
            email = _trunc(_safe(row.get("Email")), 255)
            phone = _trunc(_normalize_phone(_safe(row.get("Work Phone")) or _safe(row.get("Mobile Phone"))), 50)
            title = _trunc(_safe(row.get("Title")), 255)
            ma_id = _safe(row.get("Master Account ID"))
            comp_gid = uuid.UUID(ma_to_gid[ma_id]) if ma_id and ma_id in ma_to_gid else None

            pid, pslug = GIDS.resolve("LEGACY_MUHIDE_CONTACT_ID", cid, "P")
            gp_batch.append((str(pid), pslug, name, email, phone, comp_gid, title, now))
            lm_batch.append((str(uuid.uuid4()), "LEGACY_MUHIDE_CONTACT_ID", cid, "P", str(pid), 1.0, now))
            apollo = _safe(row.get("Apollo Contact ID"))
            if apollo:
                lm_batch.append((str(uuid.uuid4()), "LEGACY_MUHIDE_APOLLO_CONTACT", apollo, "P", str(pid), 1.0, now))

        if gp_batch:
            await conn.executemany(
                """INSERT INTO md_global_people
                (id, slug, canonical_name, email, phone, company_global_id, job_title,
                 status, source_count, created_at, updated_at)
                VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, 'active', 1, $8, $8)""",
                gp_batch)
            counts["global_people"] += len(gp_batch)
        if lm_batch:
            await _flush_lm(conn, lm_batch)
            counts["legacy_mappings"] += len(lm_batch)
        print(f"  {len(gp_batch)} people + mappings in {time.time()-t3:.1f}s")

        # ═══════════════════════════════════════════════════════════════
        # FILE 4: 04_Entity_Resolution_Review.csv (565 rows)
        # ═══════════════════════════════════════════════════════════════
        print("\n[4/4] 04_Entity_Resolution_Review.csv")
        t4 = time.time()
        try:
            with open(REVIEW_CSV, "r", encoding="utf-8") as f:
                rv_rows = list(csv.DictReader(f))
        except UnicodeDecodeError:
            with open(REVIEW_CSV, "r", encoding="utf-8-sig") as f:
                rv_rows = list(csv.DictReader(f))
        print(f"  Read {len(rv_rows)} rows")

        rv_file_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'text/csv', 1, $7, $8, $9, $10, 'completed')""",
            rv_file_id, str(TENANT_ID), "04_Entity_Resolution_Review.csv", str(REVIEW_CSV),
            "bulk_ingest", REVIEW_CSV.stat().st_size, len(rv_rows), "muhide_review_cluster",
            str(TENANT_ID), now,
        )
        counts["source_files"] += 1

        sr_batch = []
        for idx, row in enumerate(rv_rows):
            old_ma = _safe(row.get("Old Master Account ID")) or f"CLUSTER-{idx}"
            sr_batch.append((str(uuid.uuid4()), str(TENANT_ID), str(rv_file_id),
                             "muhide_review_cluster", old_ma, idx,
                             json.dumps(dict(row), ensure_ascii=False, default=str),
                             "review_cluster", now))
        if sr_batch:
            await conn.executemany(
                """INSERT INTO md_source_rows
                (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                 raw_payload, entity_type, resolution_status, created_at)
                VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'historical', $9)
                ON CONFLICT (source_id, source_record_id) DO NOTHING""",
                sr_batch)
            counts["source_rows"] += len(sr_batch)
            counts["review_clusters"] = len(sr_batch)
        print(f"  {len(sr_batch)} review clusters in {time.time()-t4:.1f}s")

        # ═══════════════════════════════════════════════════════════════
        # VALIDATION QUERIES
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "=" * 60)
        print("INGESTION COMPLETE — VALIDATION QUERIES")
        print("=" * 60)

        r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_global_companies")
        print(f"  md_global_companies: {r['c']:,}")
        r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_global_people")
        print(f"  md_global_people: {r['c']:,}")
        r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_legacy_id_mappings")
        print(f"  md_legacy_id_mappings: {r['c']:,}")
        r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_source_rows")
        print(f"  md_source_rows: {r['c']:,}")
        r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_source_files")
        print(f"  md_source_files: {r['c']:,}")
        r = await conn.fetchrow("SELECT COUNT(*) as c FROM md_field_provenance")
        print(f"  md_field_provenance: {r['c']:,}")

        # Legacy mapping breakdown
        lms = await conn.fetch(
            "SELECT legacy_id_type, COUNT(*) as c FROM md_legacy_id_mappings GROUP BY legacy_id_type ORDER BY c DESC")
        print("\n  Legacy mapping breakdown:")
        for lm in lms:
            print(f"    {lm['legacy_id_type']}: {lm['c']:,}")

        # CR stats
        crs = await conn.fetch(
            "SELECT COUNT(*) as total, COUNT(cr_number) as has_cr FROM md_global_companies")
        print(f"\n  Companies with CR: {crs[0]['has_cr']:,} / {crs[0]['total']:,}")

        # Source row breakdown
        srs = await conn.fetch(
            "SELECT source_id, entity_type, COUNT(*) as c FROM md_source_rows GROUP BY source_id, entity_type ORDER BY c DESC")
        print("\n  Source row breakdown:")
        for sr in srs:
            print(f"    {sr['source_id']} ({sr['entity_type']}): {sr['c']:,}")

        print(f"\n  Global IDs: pinned={GIDS.pinned_hits:,} derived={GIDS.derived_hits:,}")

        elapsed = time.time() - t_total
        print(f"\n{'=' * 60}")
        print(f"TOTAL TIME: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"{'=' * 60}")

    finally:
        await conn.close()


async def _flush_gc(conn, batch):
    await conn.executemany(
        """INSERT INTO md_global_companies
        (id, slug, canonical_name, cr_number, city, domain, phone, email,
         industry, source_count, metadata, created_at, updated_at)
        VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, CAST($11 AS JSONB), $12, $12)
        ON CONFLICT (slug) DO NOTHING""",
        batch)

async def _flush_lm(conn, batch):
    await conn.executemany(
        """INSERT INTO md_legacy_id_mappings
        (id, legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at)
        VALUES ($1::uuid, $2, $3, $4, $5::uuid, $6, $7)
        ON CONFLICT (legacy_id_type, legacy_id) DO NOTHING""",
        batch)

async def _flush_prov(conn, batch):
    await conn.executemany(
        """INSERT INTO md_field_provenance
        (id, global_entity_id, field_name, field_value, source_row_id,
         evidence_tier, authority_score, selection_reason, conflict_status,
         is_current, created_at)
        VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $6, $7, $8, $9, $10, $11)""",
        batch)


if __name__ == "__main__":
    asyncio.run(main())
