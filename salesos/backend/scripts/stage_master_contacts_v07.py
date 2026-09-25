"""Stage the reviewed MUHIDE v0.7 contacts file in salesos_test only.

This creates source-file/source-row records only. It does not create people,
legacy ID mappings, company relationships, or update any canonical entity.
Raw CSV cells are preserved verbatim in raw_payload; no PII is printed.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import gzip
import hashlib
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

import asyncpg

from scripts.phase6_schema_gate import PG_DB, PG_HOST, PG_PASS, PG_PORT, PG_USER

EXPECTED_ACCOUNTS_SHA256 = "1cb60fe7a83fc8fef510ddd00b62c3ffdc3f65e8c6fa4ad525cb75821585316c"
EXPECTED_CONTACTS_SHA256 = "9772be62111ff40d664678de497449d7134e4def7e01057494bcddae88b5c9ec"
EXPECTED_ACCOUNT_ROWS = 296_746
EXPECTED_CONTACT_ROWS = 47_192
SOURCE_ID = "muhide_contacts_v07"
LINKAGE_COUNTS = {
    "RESOLVED_VIA_MA_TO_GCID_MAP": 44_974,
    "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW": 1_114,
    "NO_ACCOUNT_LINK": 1_104,
}
NAMESPACE = uuid.UUID("70bb528f-c3d7-4c72-a271-6db9b216229e")
DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "business" / "data" / "output" / "bulk"
DEFAULT_CONTACTS = DEFAULT_ROOT / "03_Master_Contacts_FINAL_v0.7.csv"
DEFAULT_ACCOUNTS = DEFAULT_ROOT / "01_Master_Accounts_TRUE_FINAL_v10.csv.gz"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_company_crosswalk(
    path: Path, expected_sha256: str = EXPECTED_ACCOUNTS_SHA256
) -> dict[str, str]:
    if sha256_file(path) != expected_sha256:
        raise ValueError("The v10 accounts file hash does not match the reviewed source")
    mapping: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"Master Account ID", "Global_Company_ID"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("The v10 accounts file is missing required crosswalk columns")
        for row in reader:
            ma_id = (row.get("Master Account ID") or "").strip()
            gcid = (row.get("Global_Company_ID") or "").strip()
            if not ma_id or not gcid or ma_id in mapping:
                raise ValueError("The v10 company crosswalk has a blank or duplicate key")
            mapping[ma_id] = gcid
    if len(mapping) != EXPECTED_ACCOUNT_ROWS:
        raise ValueError(f"Unexpected v10 company count: {len(mapping)}")
    return mapping


def load_contacts(
    path: Path,
    company_crosswalk: dict[str, str],
    expected_sha256: str = EXPECTED_CONTACTS_SHA256,
) -> list[dict[str, str]]:
    if sha256_file(path) != expected_sha256:
        raise ValueError("The v0.7 contacts file hash does not match the reviewed source")
    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    linkage_counts: Counter[str] = Counter()
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {
            "global_person_id",
            "Linkage_Status",
            "matched_master_account_id",
            "Global_Company_ID",
        }
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("The v0.7 contacts file is missing required linkage columns")
        for line_number, raw in enumerate(reader, start=2):
            row = {key: (value if value is not None else "") for key, value in raw.items()}
            person_id = row["global_person_id"].strip()
            status = row["Linkage_Status"].strip()
            ma_id = row["matched_master_account_id"].strip()
            gcid = row["Global_Company_ID"].strip()
            if not person_id or person_id in seen_ids:
                raise ValueError(f"Blank or duplicate person source ID at CSV line {line_number}")
            if status not in LINKAGE_COUNTS:
                raise ValueError(f"Unexpected linkage state at CSV line {line_number}")
            if status == "RESOLVED_VIA_MA_TO_GCID_MAP":
                if not ma_id or not gcid or company_crosswalk.get(ma_id) != gcid:
                    raise ValueError(
                        f"Resolved company link failed v10 crosswalk at CSV line {line_number}"
                    )
            elif gcid:
                raise ValueError(
                    f"Unresolved/unlinked person has a company ID at CSV line {line_number}"
                )
            seen_ids.add(person_id)
            linkage_counts[status] += 1
            rows.append(row)
    if len(rows) != EXPECTED_CONTACT_ROWS or dict(linkage_counts) != LINKAGE_COUNTS:
        raise ValueError(
            "The contacts row count or linkage distribution differs from reviewed v0.7"
        )
    return rows


def deterministic_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, name)


async def stage_rows(contacts_path: Path, rows: list[dict[str, str]]) -> dict[str, int | bool]:
    file_hash = EXPECTED_CONTACTS_SHA256
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    try:
        db_name = await conn.fetchval("SELECT current_database()")
        if db_name != "salesos_test":
            raise RuntimeError(
                f"Refusing writes outside salesos_test (connected database: {db_name})"
            )

        source_state = await conn.fetch(
            "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname = ANY($1::text[])",
            ["md_source_files", "md_source_rows", "md_source_values"],
        )
        if {
            r["relname"]: (r["relrowsecurity"], r["relforcerowsecurity"]) for r in source_state
        } != {
            "md_source_files": (True, True),
            "md_source_rows": (True, True),
            "md_source_values": (True, True),
        }:
            raise RuntimeError("Tenant source tables must have ENABLE + FORCE RLS before staging")
        role = await conn.fetchrow(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname='salesos_app'"
        )
        if not role or role["rolsuper"] or role["rolbypassrls"]:
            raise RuntimeError("salesos_app must exist and must not bypass row security")
        for table, privilege in (
            ("md_source_files", "SELECT"),
            ("md_source_files", "INSERT"),
            ("md_source_rows", "SELECT"),
            ("md_source_rows", "INSERT"),
            ("md_source_values", "SELECT"),
            ("md_source_values", "INSERT"),
        ):
            if not await conn.fetchval(
                "SELECT has_table_privilege('salesos_app', $1, $2)",
                f"public.{table}",
                privilege,
            ):
                raise RuntimeError(f"salesos_app lacks {privilege} on {table}")

        async with conn.transaction():
            source_owner = await conn.fetchrow(
                "SELECT tenant_id, uploaded_by FROM md_source_files "
                "ORDER BY uploaded_at, id LIMIT 1"
            )
            if not source_owner:
                raise RuntimeError(
                    "No existing source owner context in salesos_test; refusing to invent one"
                )
            tenant_id = source_owner["tenant_id"]
            uploaded_by = source_owner["uploaded_by"]
            tenant_count = await conn.fetchval(
                "SELECT count(DISTINCT tenant_id) FROM md_source_files"
            )
            if tenant_count != 1:
                raise RuntimeError(
                    "Test source files span multiple tenants; select an owner before staging"
                )
            await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_id))

            existing_files = await conn.fetch(
                "SELECT id, tenant_id, total_rows, status FROM md_source_files "
                "WHERE filename=$1 AND file_hash_sha256=$2",
                contacts_path.name,
                file_hash,
            )
            if len(existing_files) > 1:
                raise RuntimeError(
                    "Duplicate source file registrations found for the reviewed v0.7 file"
                )
            if existing_files:
                file_id = existing_files[0]["id"]
                if existing_files[0]["tenant_id"] != tenant_id or existing_files[0][
                    "total_rows"
                ] != len(rows):
                    raise RuntimeError(
                        "Existing v0.7 source file registration conflicts with reviewed staging"
                    )
                if existing_files[0]["status"] != "completed":
                    await conn.execute(
                        "UPDATE md_source_files SET status='completed' WHERE id=$1",
                        file_id,
                    )
                created_file = False
            else:
                file_id = deterministic_uuid(f"file:{tenant_id}:{file_hash}")
                await conn.execute(
                    """INSERT INTO md_source_files
                       (id, tenant_id, filename, storage_path, file_hash_sha256,
                        file_size_bytes, mime_type, sheet_count, total_rows,
                        source_system, schema_mapping, uploaded_by, status)
                       VALUES ($1,$2,$3,$4,$5,$6,'text/csv',1,$7,$8,$9::jsonb,$10,'completed')""",
                    file_id,
                    tenant_id,
                    contacts_path.name,
                    str(contacts_path.resolve()),
                    file_hash,
                    contacts_path.stat().st_size,
                    len(rows),
                    "muhide_v0_7",
                    json.dumps(
                        {"columns": list(rows[0]), "raw_payload": "verbatim CSV cell strings"}
                    ),
                    uploaded_by,
                )
                created_file = True

            existing = await conn.fetch(
                "SELECT source_record_id, source_file_id, raw_payload "
                "FROM md_source_rows WHERE source_id=$1",
                SOURCE_ID,
            )
            input_by_id = {row["global_person_id"]: row for row in rows}
            for record in existing:
                expected = input_by_id.get(record["source_record_id"])
                stored_payload = record["raw_payload"]
                if isinstance(stored_payload, str):
                    stored_payload = json.loads(stored_payload)
                if (
                    record["source_file_id"] != file_id
                    or expected is None
                    or stored_payload != expected
                ):
                    raise RuntimeError(
                        "Existing v0.7 source row conflicts with the immutable input"
                    )

            inserted_before = len(existing)
            batch: list[tuple] = []
            for line_number, row in enumerate(rows, start=2):
                batch.append(
                    (
                        deterministic_uuid(f"row:{SOURCE_ID}:{row['global_person_id']}"),
                        tenant_id,
                        file_id,
                        SOURCE_ID,
                        row["global_person_id"],
                        line_number,
                        json.dumps(row, ensure_ascii=False),
                        "person",
                    )
                )
                if len(batch) >= 1_000:
                    await _insert_batch(conn, batch)
                    batch.clear()
            if batch:
                await _insert_batch(conn, batch)
            inserted_after = await conn.fetchval(
                "SELECT count(*) FROM md_source_rows WHERE source_id=$1", SOURCE_ID
            )
            if inserted_after != len(rows):
                raise RuntimeError(
                    f"Staged row count mismatch: expected {len(rows)}, found {inserted_after}"
                )

        # Prove the application role can see the staged rows for the bound
        # tenant and sees none after the tenant context changes.
        async with conn.transaction():
            await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant_id))
            await conn.execute("SET LOCAL ROLE salesos_app")
            visible_own = await conn.fetchval(
                "SELECT count(*) FROM md_source_rows WHERE source_id=$1", SOURCE_ID
            )
            await conn.execute(
                "SELECT set_config('app.tenant_id', $1, true)",
                "00000000-0000-0000-0000-000000000001",
            )
            visible_other = await conn.fetchval(
                "SELECT count(*) FROM md_source_rows WHERE source_id=$1", SOURCE_ID
            )
            if visible_own != len(rows) or visible_other != 0:
                raise RuntimeError("salesos_app tenant isolation verification failed")
        return {
            "source_file_created": created_file,
            "source_rows_before": inserted_before,
            "source_rows_after": inserted_after,
            "new_rows": inserted_after - inserted_before,
            "salesos_app_own_tenant_visible": visible_own,
            "salesos_app_other_tenant_visible": visible_other,
        }
    finally:
        await conn.close()


async def _insert_batch(conn: asyncpg.Connection, batch: list[tuple]) -> None:
    await conn.executemany(
        """INSERT INTO md_source_rows
           (id, tenant_id, source_file_id, source_id, source_record_id,
            row_number, raw_payload, entity_type)
           VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8)
           ON CONFLICT (source_id, source_record_id) DO NOTHING""",
        batch,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contacts", type=Path, default=DEFAULT_CONTACTS)
    parser.add_argument("--accounts", type=Path, default=DEFAULT_ACCOUNTS)
    parser.add_argument(
        "--apply", action="store_true", help="Write source file/rows to salesos_test"
    )
    args = parser.parse_args()
    try:
        crosswalk = load_company_crosswalk(args.accounts)
        rows = load_contacts(args.contacts, crosswalk)
        print(f"Input validation: PASS ({len(rows):,} contact source rows; no PII displayed)")
        print("Company links: PASS (every resolved MA to GC-ID pair matches v10)")
        if not args.apply:
            print("Dry run only. Pass --apply to stage rows in salesos_test.")
            return 0
        result = asyncio.run(stage_rows(args.contacts, rows))
        print("salesos_test staging: PASS")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print("Canonical people/mappings/relationships changed: 0 (source staging only)")
        return 0
    except (OSError, ValueError, RuntimeError, asyncpg.PostgresError) as exc:
        print(f"Staging halted safely: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
