"""Record HUMAN decisions from the filled gate workbooks (reports 106/107).

Only what a named reviewer wrote is recorded. A row is skipped (and reported)
unless it has a decision, a reviewer and a reviewed_at date. The machine
suggestion column is never read as a decision. Default is a dry run; pass
--apply to write. Writes go only to md_review_queue_state in salesos_test via
ReviewQueueService.record_disposition (record-only: no merge, no CR change).

G5 spot-check rows have no per-row queue: this script reports the material
error rate per the 2% threshold; stratum acceptance stays a PO signature.

    python scripts/phase7a_capture_gate_workbooks.py            # dry run
    python scripts/phase7a_capture_gate_workbooks.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.master_data.phase7.review_queue import (  # noqa: E402
    QUEUE_P1,
    QUEUE_SHORT_CR,
    ReviewQueueService,
    review_async_session,
)

WB = Path(__file__).resolve().parents[3] / "docs" / "data" / "phase7" / "gate_review_20260925"
G3_MAP = {
    "CONFIRMED_VALID_CR": "CONFIRMED_VALID_SHORT_CR",
    "NOT_A_CR": "CONFIRMED_ARTIFACT",
    "UNRESOLVED_ESCALATE": "UNRESOLVED_ESCALATE",
}
G4_MAP = {"CORRECT": "CONFIRM", "MATERIAL_ERROR": "ESCALATE", "CANNOT_VERIFY": "REVIEW"}
G4_FILES = (
    "G4_P1_FIELD_CONFLICT_FULL.csv",
    "G4_P1_WEAK_IDENTITY_FULL.csv",
    "G4_P1_CORROBORATION_SAMPLE_5PCT.csv",
)


def _rows(name: str) -> list[dict[str, str]]:
    with open(WB / name, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _col(row: dict[str, str], prefix: str) -> str:
    return next((v for k, v in row.items() if k and k.startswith(prefix)), "").strip()


def _human(row: dict[str, str]) -> tuple[str, str, str] | None:
    decision, reviewer, when = _col(row, "decision").upper(), _col(row, "reviewer"), _col(row, "reviewed_at")
    return (decision, reviewer, when) if decision and reviewer and when else None


def plan() -> tuple[list[dict], dict]:
    writes: list[dict] = []
    report: dict = {"skipped_incomplete": {}, "invalid": [], "g5": {}}
    for row in _rows("G3_HUMAN_REVIEW_5_ACCOUNTS.csv"):
        h = _human(row)
        if not h:
            report["skipped_incomplete"]["G3"] = report["skipped_incomplete"].get("G3", 0) + 1
            continue
        if h[0] not in G3_MAP:
            report["invalid"].append(("G3", row["ma_id"], h[0]))
            continue
        writes.append({"queue_type": QUEUE_SHORT_CR, "subject_key": row["ma_id"],
                       "disposition": G3_MAP[h[0]], "reviewer": h[1],
                       "notes": f"G3 workbook {h[2]}: {h[0]}. {_col(row, 'notes')}"})
    for name in G4_FILES:
        for row in _rows(name):
            h = _human(row)
            if not h:
                report["skipped_incomplete"][name] = report["skipped_incomplete"].get(name, 0) + 1
                continue
            if h[0] not in G4_MAP:
                report["invalid"].append((name, row["ma_id"], h[0]))
                continue
            writes.append({"queue_type": QUEUE_P1, "subject_key": row["global_company_id"],
                           "disposition": G4_MAP[h[0]], "reviewer": h[1],
                           "notes": f"{name} {h[2]}: {h[0]} {_col(row, 'error_type')}. {_col(row, 'notes')}"})
    g5 = [r for r in _rows("G5_SRWR_REAL_WORLD_SPOT_CHECK.csv") if _human(r)]
    errors = sum(1 for r in g5 if _human(r)[0] == "MATERIAL_ERROR")
    unverified = sum(1 for r in g5 if _human(r)[0] == "CANNOT_VERIFY")
    report["g5"] = {
        "reviewed": len(g5), "material_errors": errors, "cannot_verify": unverified,
        "error_rate_pct": round(100 * errors / len(g5), 2) if g5 else None,
        "within_2pct_threshold": (errors / len(g5) <= 0.02) if g5 else None,
    }
    return writes, report


async def apply(writes: list[dict]) -> int:
    async with review_async_session() as session:
        db = (await session.execute(text("SELECT current_database()"))).scalar()
        if db != "salesos_test":
            raise RuntimeError(f"Refusing to write to {db!r}")
        svc = ReviewQueueService(session)
        for w in writes:
            await svc.record_disposition(**w)
        await session.commit()
    return len(writes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    writes, report = plan()
    report["to_record"] = len(writes)
    if report["invalid"]:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        print("Refusing: invalid decision values present.")
        return 2
    if args.apply and writes:
        report["recorded"] = asyncio.run(apply(writes))
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
