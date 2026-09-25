#!/usr/bin/env python3
"""Produce a deterministic, non-mutating review manifest for 1,114 MA links.

The official v0.7 contacts file is compared with the 296,746-company Master
Accounts snapshot in ``salesos_test``.  The output is a review artifact only:
it never writes a Global Company ID into v0.7 and never changes the database.
Name+domain exact unique matches are proposed as deterministic candidates;
domain-only/name-only matches remain review items; ambiguous rows escalate.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.modules.master_data.phase7.review_queue import review_async_session

V07 = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.7.csv")
OUT = Path(r"D:\AISalesOS\project-audit\41_MA_UNRESOLVED_HUMAN_REVIEW_2026-09-22.csv")
REPORT = OUT.with_suffix(".md")


def norm(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"[^\w]+", "", value, flags=re.UNICODE)


async def main() -> int:
    if not V07.exists():
        raise FileNotFoundError(V07)
    v07_hash = hashlib.sha256(V07.read_bytes()).hexdigest()
    contacts = [r for r in csv.DictReader(V07.open(encoding="utf-8-sig", newline=""))
                if r.get("Linkage_Status", "").startswith("UNRESOLVED_MA_NOT_IN_MASTER")]
    if len(contacts) != 1114:
        raise RuntimeError(f"Expected 1,114 unresolved v0.7 rows; found {len(contacts)}")
    async with review_async_session() as session:
        if (await session.execute(text("SELECT current_database()"))).scalar() != "salesos_test":
            raise RuntimeError("Refusing MA review outside salesos_test")
        companies = [dict(r) for r in (await session.execute(text("""
            SELECT id::text AS global_company_id, canonical_name, domain
            FROM md_global_companies ORDER BY id
        """))).mappings().all()]
        if len(companies) != 296746:
            raise RuntimeError(f"Master population drift: {len(companies)}")
    by_domain: dict[str, list[dict]] = defaultdict(list)
    by_name: dict[str, list[dict]] = defaultdict(list)
    by_name_domain: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in companies:
        d = (c.get("domain") or "").strip().lower()
        n = norm(c.get("canonical_name"))
        if d: by_domain[d].append(c)
        if n: by_name[n].append(c)
        if n and d: by_name_domain[(n, d)].append(c)

    fields = ["global_person_id", "matched_master_account_id", "full_name", "organization_raw", "email",
              "candidate_status", "candidate_global_company_id", "candidate_name",
              "candidate_domain", "candidate_count", "review_reason"]
    rows: list[dict] = []
    status_counts: Counter[str] = Counter()
    for r in contacts:
        email_domain = r.get("email", "").split("@", 1)[-1].strip().lower() if "@" in r.get("email", "") else ""
        name_key = norm(r.get("organization_raw"))
        exact = by_name_domain.get((name_key, email_domain), []) if name_key and email_domain else []
        domain = by_domain.get(email_domain, []) if email_domain else []
        name = by_name.get(name_key, []) if name_key else []
        if len(exact) == 1:
            status, candidates, reason = "DETERMINISTIC_EXACT_NAME_DOMAIN", exact, "Exact normalized organization name + exact email domain, unique in Master."
        elif len(domain) == 1:
            status, candidates, reason = "REVIEW_UNIQUE_DOMAIN", domain, "Unique email domain in Master, but organization name is absent/different; do not auto-link."
        elif len(name) == 1:
            status, candidates, reason = "REVIEW_UNIQUE_NAME", name, "Unique normalized organization name without a corroborating exact domain; do not auto-link."
        elif len(domain) > 1:
            status, candidates, reason = "ESCALATE_DOMAIN_AMBIGUOUS", domain, "Email domain maps to multiple Master companies."
        elif len(name) > 1:
            status, candidates, reason = "ESCALATE_NAME_AMBIGUOUS", name, "Organization name maps to multiple Master companies."
        else:
            status, candidates, reason = "ESCALATE_NO_DETERMINISTIC_CANDIDATE", [], "No exact name/domain candidate in Master."
        status_counts[status] += 1
        candidate = candidates[0] if len(candidates) == 1 else {}
        rows.append({
            "global_person_id": r.get("global_person_id", ""),
            "matched_master_account_id": r.get("matched_master_account_id", ""),
            "full_name": r.get("full_name", ""), "organization_raw": r.get("organization_raw", ""),
            "email": r.get("email", ""), "candidate_status": status,
            "candidate_global_company_id": candidate.get("global_company_id", ""),
            "candidate_name": candidate.get("canonical_name", ""),
            "candidate_domain": candidate.get("domain", ""),
            "candidate_count": str(len(candidates)), "review_reason": reason,
        })
    # A stale MA key must be internally consistent across all its contact
    # rows. Fail closed when one legacy key points to multiple current Global
    # IDs; applying a row-level match would silently split that old account.
    candidate_gids_by_ma: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["candidate_global_company_id"]:
            candidate_gids_by_ma[row["matched_master_account_id"]].add(row["candidate_global_company_id"])
    conflicted_mas = {ma for ma, gids in candidate_gids_by_ma.items() if len(gids) > 1}
    for row in rows:
        if row["matched_master_account_id"] in conflicted_mas and row["candidate_global_company_id"]:
            row["candidate_status"] = "ESCALATE_MA_MULTI_CANDIDATE"
            row["review_reason"] = (
                "Legacy MA key maps to multiple current Global Company IDs across its contacts; "
                "split the source account before linking."
            )
    status_counts = Counter(row["candidate_status"] for row in rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    group_counts = Counter()
    for r in rows:
        group_counts[(r["matched_master_account_id"], r["candidate_status"], r["candidate_global_company_id"])] += 1
    REPORT.write_text("""# MA Unresolved Human Review — 2026-09-22

## Decision

The 1,114 unresolved v0.7 contact links were checked against the official
Master Accounts snapshot (296,746 companies). This is a deterministic review
manifest only. No `Global_Company_ID` was written to v0.7, no source row was
changed, and no production database was touched.

| Result | Rows |
|---|---:|
| `DETERMINISTIC_EXACT_NAME_DOMAIN` — exact normalized organization name + exact email domain, with no MA-level conflict | %d |
| `REVIEW_UNIQUE_DOMAIN` — domain is unique but name does not corroborate | %d |
| `REVIEW_UNIQUE_NAME` — name is unique without exact domain corroboration | %d |
| `ESCALATE_DOMAIN_AMBIGUOUS` | %d |
| `ESCALATE_NAME_AMBIGUOUS` | %d |
| `ESCALATE_NO_DETERMINISTIC_CANDIDATE` | %d |
| `ESCALATE_MA_MULTI_CANDIDATE` — one legacy MA key maps to multiple current Global IDs | %d |
| **Total** | **%d** |

The **%d exact name+domain rows** are the only rows with a deterministic
candidate and no MA-level conflict in this pass. A further **%d rows across
%d legacy MA keys** were deliberately escalated because the same stale MA key
points to multiple current Global IDs. They must be split before any mapping
is applied. All candidates remain proposals until a data-owner disposition is
recorded; the manifest does not apply them. Domain-only and name-only matches
remain review items because group domains and repeated names can identify
different legal entities.

## Evidence

- v0.7 input: `%s`
- v0.7 SHA-256: `%s`
- Master snapshot: `salesos_test.md_global_companies` from `01_Master_Accounts.csv`
- Master population checked: 296,746
- Output SHA-256: `%s`
- Output: `%s`

**Safety:** no database writes; no external calls; no guessed mappings; no
Global ID stability risk. Roadmap: **75%% (85/113)**.
""" % (status_counts["DETERMINISTIC_EXACT_NAME_DOMAIN"], status_counts["REVIEW_UNIQUE_DOMAIN"],
       status_counts["REVIEW_UNIQUE_NAME"], status_counts["ESCALATE_DOMAIN_AMBIGUOUS"],
       status_counts["ESCALATE_NAME_AMBIGUOUS"], status_counts["ESCALATE_NO_DETERMINISTIC_CANDIDATE"],
       status_counts["ESCALATE_MA_MULTI_CANDIDATE"], len(rows),
       status_counts["DETERMINISTIC_EXACT_NAME_DOMAIN"], status_counts["ESCALATE_MA_MULTI_CANDIDATE"],
       len(conflicted_mas), str(V07), v07_hash, digest, str(OUT)), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "status_counts": status_counts, "v07_sha256": v07_hash,
                      "output_sha256": digest, "database_writes": 0}, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
