#!/usr/bin/env python3
"""Apply only Apollo + exact name/domain corroborated MA rows to v1.0."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict, Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from app.modules.master_data.phase7.review_queue import review_async_session

V09 = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.9.csv")
V10 = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v1.0.csv")
APOLLO_MANIFEST = Path(r"D:\AISalesOS\project-audit\45_MA_APOLLO_PASS_2026-09-22.csv")
MANIFEST = Path(r"D:\AISalesOS\project-audit\46_MA_CROSS_EVIDENCE_PASS_2026-09-22.csv")
REPORT = Path(r"D:\AISalesOS\project-audit\46_MA_CROSS_EVIDENCE_PASS_2026-09-22.md")
META = Path(r"D:\AISalesOS\project-audit\46_MA_CROSS_EVIDENCE_PASS_2026-09-22.json")


def tokens(value: str | None) -> list[str]:
    return [x for x in re.split(r"[;,|\s]+", value or "") if x and x.lower() not in {"none", "nan"}]


def norm(value: str | None) -> str:
    return re.sub(r"[^\w]+", "", unicodedata.normalize("NFKC", value or "").lower(), flags=re.UNICODE)


async def load_maps() -> tuple[dict[tuple[str, str], set[str]], dict[str, set[str]]]:
    async with review_async_session() as session:
        if (await session.execute(text("SELECT current_database()"))).scalar() != "salesos_test":
            raise RuntimeError("Refusing cross-evidence pass outside salesos_test")
        await session.execute(text("SET LOCAL statement_timeout='120s'"))
        companies = [dict(r) for r in (await session.execute(text(
            "SELECT id::text AS gid, canonical_name, domain FROM md_global_companies"
        ))).mappings().all()]
        by_name: dict[str, set[str]] = defaultdict(set)
        by_name_domain: dict[tuple[str, str], set[str]] = defaultdict(set)
        for c in companies:
            n = norm(c["canonical_name"]); d = (c["domain"] or "").strip().lower()
            if n: by_name[n].add(c["gid"])
            if n and d: by_name_domain[(n, d)].add(c["gid"])
        masters = [dict(r) for r in (await session.execute(text("""
            SELECT raw_payload->>'Apollo_Account_IDs' AS apollo_ids,
                   raw_payload->>'Canonical_Company_Name' AS canonical_name,
                   raw_payload->>'Primary_Domain' AS domain
            FROM md_source_rows WHERE source_id='muhide_master_accounts'
        """))).mappings().all()]
    apollo: dict[str, set[str]] = defaultdict(set)
    for m in masters:
        n = norm(m["canonical_name"]); d = (m["domain"] or "").strip().lower()
        gids = by_name_domain.get((n, d), set()) if n and d else set()
        if not gids and n: gids = by_name.get(n, set())
        for aid in tokens(m["apollo_ids"]): apollo[aid].update(gids)
    return by_name_domain, apollo


async def main() -> int:
    if V10.exists() or MANIFEST.exists():
        raise FileExistsError("Refusing to overwrite cross-evidence artifacts")
    v09_hash = hashlib.sha256(V09.read_bytes()).hexdigest()
    rows = list(csv.DictReader(V09.open(encoding="utf-8-sig", newline="")))
    pending = [r for r in rows if r.get("Linkage_Status") == "UNRESOLVED_MA_NOT_IN_MASTER_V10_NEEDS_REVIEW"]
    if len(rows) != 47192 or len(pending) != 355:
        raise RuntimeError(f"v0.9 drift: rows={len(rows)}, pending={len(pending)}")
    apollo_manifest = {r["global_person_id"]: r for r in csv.DictReader(APOLLO_MANIFEST.open(encoding="utf-8-sig", newline=""))}
    by_nd, apollo = await load_maps()
    decisions = {}; counts: Counter[str] = Counter()
    for row in pending:
        aid_candidates = set()
        for aid in tokens(row.get("apollo_account_id")): aid_candidates.update(apollo.get(aid, set()))
        domain = row.get("email", "").split("@", 1)[-1].strip().lower() if "@" in row.get("email", "") else ""
        exact_candidates = by_nd.get((norm(row.get("organization_raw")), domain), set()) if domain and row.get("organization_raw") else set()
        if len(exact_candidates) == 1 and exact_candidates.issubset(aid_candidates):
            status = "APOLLO_AND_EXACT_NAME_DOMAIN_CORROBORATED"
            gid = next(iter(exact_candidates))
            reason = "Apollo Account ID and exact normalized organization name/domain select the same current Global Company."
        elif len(aid_candidates) > 1 and len(exact_candidates) == 1:
            status = "REVIEW_CROSS_EVIDENCE_CONFLICT"
            gid = ""
            reason = "Exact name/domain selects a candidate but Apollo evidence contains multiple candidates."
        else:
            status = "ESCALATE_CROSS_EVIDENCE_UNRESOLVED"
            gid = ""
            reason = "Apollo and exact name/domain do not provide a single corroborated candidate."
        decisions[row["global_person_id"]] = (status, gid, reason)
        counts[status] += 1
    fields = ["global_person_id", "matched_master_account_id", "full_name", "organization_raw", "email",
              "apollo_account_id", "cross_evidence_status", "candidate_global_company_id", "review_reason"]
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        for row in pending:
            st, gid, reason = decisions[row["global_person_id"]]
            writer.writerow({"global_person_id": row["global_person_id"], "matched_master_account_id": row["matched_master_account_id"],
                             "full_name": row.get("full_name", ""), "organization_raw": row.get("organization_raw", ""),
                             "email": row.get("email", ""), "apollo_account_id": row.get("apollo_account_id", ""),
                             "cross_evidence_status": st, "candidate_global_company_id": gid, "review_reason": reason})
    manifest_hash = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    fields_v10 = list(rows[0].keys()) + ["Cross_Evidence_Status", "Cross_Evidence_Reason"]
    applied = 0
    for row in rows:
        decision = decisions.get(row.get("global_person_id"))
        if decision is None:
            row["Cross_Evidence_Status"] = "NOT_APPLICABLE"
            row["Cross_Evidence_Reason"] = "Existing v0.9 resolution retained."
        else:
            st, gid, reason = decision
            row["Cross_Evidence_Status"] = st; row["Cross_Evidence_Reason"] = reason
            if st == "APOLLO_AND_EXACT_NAME_DOMAIN_CORROBORATED":
                row["Global_Company_ID"] = gid
                row["Linkage_Status"] = "RESOLVED_VIA_APOLLO_AND_EXACT_NAME_DOMAIN"
                applied += 1
    with V10.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields_v10); writer.writeheader(); writer.writerows(rows)
    v10_hash = hashlib.sha256(V10.read_bytes()).hexdigest()
    meta = {"created_at_utc": datetime.now(UTC).isoformat(), "input_v09_sha256": v09_hash,
            "output_v10_sha256": v10_hash, "manifest_sha256": manifest_hash,
            "pending_reviewed": len(pending), "rows_applied": applied, "counts": dict(counts),
            "database_writes": 0, "production_writes": 0, "external_calls": 0}
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(f"""# MA Cross-Evidence Pass — 2026-09-22

The 355 rows remaining after exact name/domain and Apollo passes were checked
using two independent local signals: an exact Apollo Account ID candidate and
an exact normalized organization name plus email domain candidate.

| Result | Rows |
|---|---:|
| `APOLLO_AND_EXACT_NAME_DOMAIN_CORROBORATED` applied to v1.0 | {counts['APOLLO_AND_EXACT_NAME_DOMAIN_CORROBORATED']} |
| `REVIEW_CROSS_EVIDENCE_CONFLICT` | {counts['REVIEW_CROSS_EVIDENCE_CONFLICT']} |
| `ESCALATE_CROSS_EVIDENCE_UNRESOLVED` | {counts['ESCALATE_CROSS_EVIDENCE_UNRESOLVED']} |
| **Total** | **{len(pending)}** |

Derived v1.0 contains the previous 759 resolutions plus the newly applied
cross-evidence rows. No database, official v0.7, production, or external
provider write occurred.

- v0.9 SHA-256: `{v09_hash}`
- v1.0 SHA-256: `{v10_hash}`
- Manifest SHA-256: `{manifest_hash}`

**Roadmap: 75% (85/113).**
""", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
