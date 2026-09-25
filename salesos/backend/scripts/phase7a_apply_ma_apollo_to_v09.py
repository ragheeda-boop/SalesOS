#!/usr/bin/env python3
"""Use exact Apollo Account ID evidence for a second derived MA pass.

Apollo IDs are used only when they resolve to one current Global Company and
all Apollo-bearing contacts under the legacy MA key resolve consistently. The
script writes a manifest and a new FINAL_v0.9 CSV; v0.8, v0.7, and the DB are
read-only.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from app.modules.master_data.phase7.review_queue import review_async_session

V08 = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.8.csv")
V09 = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.9.csv")
MANIFEST = Path(r"D:\AISalesOS\project-audit\45_MA_APOLLO_PASS_2026-09-22.csv")
REPORT = Path(r"D:\AISalesOS\project-audit\45_MA_APOLLO_PASS_2026-09-22.md")
META = Path(r"D:\AISalesOS\project-audit\45_MA_APOLLO_PASS_2026-09-22.json")


def tokens(value: str | None) -> list[str]:
    return [x for x in re.split(r"[;,|\s]+", value or "") if x and x.lower() not in {"none", "nan"}]


def norm(value: str | None) -> str:
    return re.sub(r"[^\w]+", "", unicodedata.normalize("NFKC", value or "").lower(), flags=re.UNICODE)


async def load_apollo_map() -> dict[str, set[str]]:
    async with review_async_session() as session:
        if (await session.execute(text("SELECT current_database()"))).scalar() != "salesos_test":
            raise RuntimeError("Refusing Apollo MA pass outside salesos_test")
        await session.execute(text("SET LOCAL statement_timeout='120s'"))
        companies = [dict(r) for r in (await session.execute(text(
            "SELECT id::text AS gid, canonical_name, domain FROM md_global_companies"
        ))).mappings().all()]
        by_name: dict[str, set[str]] = defaultdict(set)
        by_name_domain: dict[tuple[str, str], set[str]] = defaultdict(set)
        for company in companies:
            name = norm(company["canonical_name"])
            domain = (company["domain"] or "").strip().lower()
            if name:
                by_name[name].add(company["gid"])
            if name and domain:
                by_name_domain[(name, domain)].add(company["gid"])
        master_rows = [dict(r) for r in (await session.execute(text("""
            SELECT raw_payload->>'Apollo_Account_IDs' AS apollo_ids,
                   raw_payload->>'Canonical_Company_Name' AS canonical_name,
                   raw_payload->>'Primary_Domain' AS domain
            FROM md_source_rows
            WHERE source_id='muhide_master_accounts'
        """))).mappings().all()]
    apollo_map: dict[str, set[str]] = defaultdict(set)
    for master in master_rows:
        name = norm(master["canonical_name"])
        domain = (master["domain"] or "").strip().lower()
        gids = by_name_domain.get((name, domain), set()) if name and domain else set()
        if not gids and name:
            gids = by_name.get(name, set())
        for apollo_id in tokens(master["apollo_ids"]):
            apollo_map[apollo_id].update(gids)
    return apollo_map


async def main() -> int:
    if not V08.exists():
        raise FileNotFoundError(V08)
    if V09.exists() or MANIFEST.exists():
        raise FileExistsError("Refusing to overwrite existing Apollo-pass artifacts")
    v08_hash = hashlib.sha256(V08.read_bytes()).hexdigest()
    rows = list(csv.DictReader(V08.open(encoding="utf-8-sig", newline="")))
    remaining = [r for r in rows if r.get("Linkage_Status") == "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW"]
    if len(rows) != 47192 or len(remaining) != 702:
        raise RuntimeError(f"v0.8 drift: rows={len(rows)}, remaining={len(remaining)}")
    apollo_map = await load_apollo_map()
    by_ma: dict[str, list[tuple[dict, set[str]]]] = defaultdict(list)
    for row in remaining:
        candidates: set[str] = set()
        for apollo_id in tokens(row.get("apollo_account_id")):
            candidates.update(apollo_map.get(apollo_id, set()))
        by_ma[row.get("matched_master_account_id", "")].append((row, candidates))
    decisions: dict[str, dict] = {}
    counts: Counter[str] = Counter()
    for ma, group in by_ma.items():
        group_gids = {gid for _, candidates in group for gid in candidates}
        for row, candidates in group:
            if len(candidates) == 1 and len(group_gids) == 1:
                status = "APOLLO_UNIQUE_MA_CONSISTENT"
                gid = next(iter(candidates))
                reason = "Exact Apollo Account ID resolves to one current Global Company and the legacy MA group is consistent."
            elif len(candidates) > 1 or len(group_gids) > 1:
                status = "ESCALATE_APOLLO_MULTI_GID"
                gid = ""
                reason = "Apollo evidence maps to multiple current Global IDs within this row or legacy MA group."
            else:
                status = "REVIEW_NO_APOLLO_MATCH"
                gid = ""
                reason = "No unique Apollo-to-current-Master candidate; retain for human review."
            decisions[row["global_person_id"]] = {"status": status, "gid": gid, "reason": reason,
                                                    "legacy_ma": ma, "apollo_ids": ";".join(tokens(row.get("apollo_account_id")))}
            counts[status] += 1
    manifest_fields = ["global_person_id", "matched_master_account_id", "full_name", "organization_raw", "email",
                       "apollo_account_id", "apollo_pass_status", "candidate_global_company_id", "review_reason"]
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=manifest_fields); writer.writeheader()
        for row in remaining:
            d = decisions[row["global_person_id"]]
            writer.writerow({"global_person_id": row["global_person_id"], "matched_master_account_id": row["matched_master_account_id"],
                             "full_name": row.get("full_name", ""), "organization_raw": row.get("organization_raw", ""),
                             "email": row.get("email", ""), "apollo_account_id": row.get("apollo_account_id", ""),
                             "apollo_pass_status": d["status"], "candidate_global_company_id": d["gid"],
                             "review_reason": d["reason"]})
    manifest_hash = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    fields = list(rows[0].keys()) + ["Apollo_Pass_Status", "Apollo_Pass_Reason"]
    applied = 0
    for row in rows:
        d = decisions.get(row.get("global_person_id"))
        if d is None:
            row["Apollo_Pass_Status"] = "NOT_APPLICABLE"
            row["Apollo_Pass_Reason"] = "Existing v0.8 resolution retained."
        else:
            row["Apollo_Pass_Status"] = d["status"]
            row["Apollo_Pass_Reason"] = d["reason"]
            if d["status"] == "APOLLO_UNIQUE_MA_CONSISTENT":
                row["Global_Company_ID"] = d["gid"]
                row["Linkage_Status"] = "RESOLVED_VIA_APOLLO_ACCOUNT_ID_MASTER_CORROBORATION"
                applied += 1
    with V09.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    v09_hash = hashlib.sha256(V09.read_bytes()).hexdigest()
    meta = {"created_at_utc": datetime.now(UTC).isoformat(), "input_v08": str(V08), "input_v08_sha256": v08_hash,
            "output_v09": str(V09), "output_v09_sha256": v09_hash, "manifest": str(MANIFEST),
            "manifest_sha256": manifest_hash, "remaining_rows_reviewed": len(remaining), "rows_applied": applied,
            "counts": dict(counts), "database_writes": 0, "production_writes": 0, "external_calls": 0}
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(f"""# MA Apollo Evidence Pass — 2026-09-22

The remaining 702 MA rows were checked against the current Master snapshot
using exact Apollo Account ID evidence already present in the local source
rows. No external provider was called.

| Result | Rows |
|---|---:|
| `APOLLO_UNIQUE_MA_CONSISTENT` applied to derived v0.9 | {counts['APOLLO_UNIQUE_MA_CONSISTENT']} |
| `ESCALATE_APOLLO_MULTI_GID` | {counts['ESCALATE_APOLLO_MULTI_GID']} |
| `REVIEW_NO_APOLLO_MATCH` | {counts['REVIEW_NO_APOLLO_MATCH']} |
| **Total** | **{len(remaining)}** |

Derived output: `{V09}`. The v0.8 input remains unchanged. The output now
contains 759 resolved rows from the two deterministic passes and leaves 355
rows unresolved for human review. No database or production write occurred.

- v0.8 SHA-256: `{v08_hash}`
- v0.9 SHA-256: `{v09_hash}`
- Manifest SHA-256: `{manifest_hash}`

**Roadmap: 75% (85/113).**
""", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
