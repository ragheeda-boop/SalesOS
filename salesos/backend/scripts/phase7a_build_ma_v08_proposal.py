#!/usr/bin/env python3
"""Build a derived v0.8 contact file from the reviewed MA manifest.

The official v0.7 file is never overwritten. Only the 412 rows marked
``DETERMINISTIC_EXACT_NAME_DOMAIN`` and free of MA-level conflicts receive a
proposed Global Company ID. Every other row is carried forward with an
explicit non-applied status and review reason.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

V07 = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.7.csv")
MANIFEST = Path(r"D:\AISalesOS\project-audit\41_MA_UNRESOLVED_HUMAN_REVIEW_2026-09-22.csv")
OUT = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_PROPOSED_v0.8.csv")
META = Path(r"D:\AISalesOS\project-audit\43_MA_V08_PROPOSAL_BUILD_2026-09-22.json")

NEW_COLUMNS = [
    "Proposed_Global_Company_ID",
    "Proposed_Linkage_Status",
    "Proposed_Linkage_Reason",
    "Proposal_Manifest_SHA256",
]


def main() -> int:
    if not V07.exists() or not MANIFEST.exists():
        raise FileNotFoundError("v0.7 or MA review manifest is missing")
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing proposal: {OUT}")
    v07_bytes = V07.read_bytes()
    manifest_bytes = MANIFEST.read_bytes()
    v07_hash = hashlib.sha256(v07_bytes).hexdigest()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig", newline="")))
    by_person: dict[str, dict] = {}
    for row in manifest_rows:
        person_id = row.get("global_person_id", "").strip()
        if not person_id or person_id in by_person:
            raise RuntimeError("Manifest has a missing or duplicate global_person_id")
        by_person[person_id] = row

    with V07.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        for column in NEW_COLUMNS:
            if column in fieldnames:
                raise RuntimeError(f"v0.7 already contains proposal column {column}")
            fieldnames.append(column)
        rows = list(reader)
    unresolved = 0
    proposed = 0
    statuses: Counter[str] = Counter()
    for row in rows:
        person_id = row.get("global_person_id", "").strip()
        review = by_person.get(person_id)
        if review is None:
            existing = row.get("Linkage_Status", "")
            status = "UNCHANGED_EXISTING_LINK" if existing == "RESOLVED_VIA_MA_TO_GCID_MAP" else "NOT_APPLICABLE_NO_ACCOUNT_LINK"
            row.update({
                "Proposed_Global_Company_ID": "",
                "Proposed_Linkage_Status": status,
                "Proposed_Linkage_Reason": "Existing v0.7 disposition retained; no MA-unresolved proposal.",
                "Proposal_Manifest_SHA256": manifest_hash,
            })
            statuses[status] += 1
            continue
        unresolved += 1
        status = review["candidate_status"]
        if status == "DETERMINISTIC_EXACT_NAME_DOMAIN":
            proposed += 1
            proposed_status = "PROPOSED_EXACT_NAME_DOMAIN_NO_MA_CONFLICT"
            gid = review["candidate_global_company_id"]
            reason = review["review_reason"]
        else:
            proposed_status = f"NOT_APPLIED_{status}"
            gid = ""
            reason = review["review_reason"]
        row.update({
            "Proposed_Global_Company_ID": gid,
            "Proposed_Linkage_Status": proposed_status,
            "Proposed_Linkage_Reason": reason,
            "Proposal_Manifest_SHA256": manifest_hash,
        })
        statuses[proposed_status] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    out_hash = hashlib.sha256(OUT.read_bytes()).hexdigest()
    meta = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "database_writes": 0,
        "official_input": str(V07),
        "official_input_sha256": v07_hash,
        "review_manifest": str(MANIFEST),
        "review_manifest_sha256": manifest_hash,
        "proposal_output": str(OUT),
        "proposal_output_sha256": out_hash,
        "input_rows": len(rows),
        "unresolved_rows_reviewed": unresolved,
        "proposed_exact_rows": proposed,
        "statuses": dict(statuses),
        "apply_status": "PROPOSAL_ONLY_NOT_APPLIED",
        "safety": [
            "v0.7 was read only and not overwritten",
            "no database or production write",
            "only exact name+domain rows with no MA-level conflict received a proposed ID",
            "all other unresolved rows retain an explicit non-applied status",
        ],
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
