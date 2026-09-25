#!/usr/bin/env python3
"""Apply only the approved exact MA proposals to a new derived v0.8 file.

The official v0.7 file is immutable. This creates FINAL_v0.8 from the
proposal copy and changes only rows explicitly marked
PROPOSED_EXACT_NAME_DOMAIN_NO_MA_CONFLICT.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

INPUT = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_PROPOSED_v0.8.csv")
OFFICIAL = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.7.csv")
OUTPUT = Path(r"C:\Users\raghe\Documents\Muhide\Claude outputs\03_Master_Contacts_FINAL_v0.8.csv")
REPORT = Path(r"D:\AISalesOS\project-audit\44_MA_V08_EXACT_APPLY_2026-09-22.md")
META = Path(r"D:\AISalesOS\project-audit\44_MA_V08_EXACT_APPLY_2026-09-22.json")

APPROVED_STATUS = "PROPOSED_EXACT_NAME_DOMAIN_NO_MA_CONFLICT"
FINAL_STATUS = "RESOLVED_VIA_EXACT_NAME_DOMAIN_MASTER_V10"


def main() -> int:
    if not INPUT.exists() or not OFFICIAL.exists():
        raise FileNotFoundError("proposal or official v0.7 file is missing")
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing derived file: {OUTPUT}")
    official_hash_before = hashlib.sha256(OFFICIAL.read_bytes()).hexdigest()
    input_hash = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if len(rows) != 47192:
        raise RuntimeError(f"Proposal row count drift: {len(rows)}")
    approved = [r for r in rows if r.get("Proposed_Linkage_Status") == APPROVED_STATUS]
    if len(approved) != 412:
        raise RuntimeError(f"Expected exactly 412 approved exact proposals; found {len(approved)}")
    ids = set()
    for row in approved:
        gid = (row.get("Proposed_Global_Company_ID") or "").strip()
        if not gid:
            raise RuntimeError("Approved proposal has missing candidate Global ID")
        ids.add(gid)
        row["Global_Company_ID"] = gid
        row["Linkage_Status"] = FINAL_STATUS
        row["Notes_HumanReviewResolution"] = (
            (row.get("Notes_HumanReviewResolution") or "").strip()
            + " | Applied to derived v0.8: exact normalized organization name + exact domain; no MA-level conflict."
        ).strip(" |")
    # Ensure canonical columns exist and all non-approved rows are untouched in
    # their original linkage fields.
    for name in ("Global_Company_ID", "Linkage_Status"):
        if name not in fields:
            raise RuntimeError(f"Missing canonical v0.7 column: {name}")
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    output_hash = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    if hashlib.sha256(OFFICIAL.read_bytes()).hexdigest() != official_hash_before:
        raise RuntimeError("Official v0.7 changed during derived build")
    statuses = Counter(r.get("Linkage_Status", "") for r in rows)
    meta = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "official_v07": str(OFFICIAL),
        "official_v07_sha256_unchanged": official_hash_before,
        "proposal_input": str(INPUT),
        "proposal_input_sha256": input_hash,
        "derived_final_v08": str(OUTPUT),
        "derived_final_v08_sha256": output_hash,
        "rows": len(rows),
        "exact_rows_applied": len(approved),
        "status_counts": dict(statuses),
        "database_writes": 0,
        "production_writes": 0,
        "external_calls": 0,
        "official_v07_modified": False,
        "remaining_unresolved_legacy_rows": 702,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(f"""# MA v0.8 Exact Apply — 2026-09-22

## Result

Created the derived final file:

`{OUTPUT}`

Applied **412** exact name+domain proposals from the reviewed v0.8 proposal
file. The official v0.7 file was not overwritten and its SHA-256 remained
`{official_hash_before}`.

| Check | Result |
|---|---:|
| Rows preserved | 47,192 / 47,192 |
| Exact proposals applied | 412 |
| Remaining unresolved/review rows | 702 |
| Official v0.7 modified | No |
| Database writes | 0 |
| Production writes | 0 |
| External calls | 0 |

Applied rows use `Linkage_Status={FINAL_STATUS}`. All other unresolved rows
retain blank `Global_Company_ID` and their explicit non-applied status.

- Proposal input SHA-256: `{input_hash}`
- Derived v0.8 SHA-256: `{output_hash}`
- Machine-readable evidence: `44_MA_V08_EXACT_APPLY_2026-09-22.json`

This derived file is ready for a separate data-quality check; it is not a
production ingestion or database migration.

**Roadmap: 75% (85/113).**
""", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
