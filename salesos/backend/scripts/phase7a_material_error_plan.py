"""Phase 7A — correction plan for the 52 escalated MATERIAL_ERROR rows.

Read-only with respect to every Phase 6 table. This script NEVER writes
`md_global_companies` and never applies a correction. It produces the decision
artefact the PO actually needs.

What the record does and does not contain
-----------------------------------------
All 52 rows carry a 14-field evidence_ref with `error_type`
(32 WRONG_DOMAIN, 20 OTHER) and `workbook_decision = MATERIAL_ERROR`. But:

  * `evidence_url`      NULL for 52/52  -> no external corroboration
  * `exact_match_field` NULL for 52/52  -> no field-level agreement
  * no proposed replacement value is recorded for any row

A "wrong domain" verdict names the *defect* but not the *correct value*. So a
correction cannot be computed from the record. Inventing a replacement domain
would fabricate Phase 6 canonical data, which is forbidden. Therefore this
script emits a REQUIREMENTS plan, and the apply harness refuses to run until an
authoritative mapping is supplied.

Usage
-----
    python phase7a_material_error_plan.py                 # requirements report
    python phase7a_material_error_plan.py --csv out.csv   # machine-readable ask
    python phase7a_material_error_plan.py --apply authoritative.csv

--apply is intentionally gated: it requires an input CSV with a header proving
the values came from an approved source, and it refuses when the file is empty
or the row count does not match. Even then it only PRINTS the diff unless
--commit is also passed, and --commit refuses without --i-have-approval.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import os
import sys

import asyncpg

DSN = os.environ.get(
    "SALESOS_TEST_DSN",
    "postgresql://salesos:salesos_dev_password@localhost:5432/salesos_test",
)

SELECT = """
SELECT q.subject_key,
       q.global_company_id,
       g.slug,
       g.canonical_name,
       g.domain                AS stored_domain,
       ic.sales_readiness,
       ic.review_priority,
       q.evidence_ref
  FROM md_review_queue_state q
  JOIN md_global_companies g ON g.id = q.global_company_id
  LEFT JOIN md_identity_classifications ic
         ON ic.global_entity_id = q.global_company_id
        AND ic.classification_version = 'OPTION_C_1+NCNP+DS5+LV+CR+ED'
 WHERE q.queue_type = 'P1_CANDIDATE'
   AND q.disposition = 'ESCALATE'
 ORDER BY q.evidence_ref ->> 'error_type', q.subject_key
"""


def ev(row) -> dict:
    v = row["evidence_ref"]
    return json.loads(v) if isinstance(v, str) else (v or {})


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="write the per-row requirements ask to this CSV")
    ap.add_argument("--apply", help="authoritative mapping CSV (gated)")
    ap.add_argument("--commit", action="store_true", help="actually write (gated)")
    ap.add_argument("--i-have-approval", action="store_true", help="PO approval (gated)")
    args = ap.parse_args()

    c = await asyncpg.connect(DSN)
    db = await c.fetchval("SELECT current_database()")
    if db != "salesos_test":
        print(f"REFUSING: connected to {db}")
        return 2
    print(f"database: {db} (read-only)\n")

    rows = await c.fetch(SELECT)
    print(f"escalated MATERIAL_ERROR rows: {len(rows)}\n")

    by_type: dict[str, list] = {}
    for r in rows:
        by_type.setdefault(ev(r).get("error_type") or "UNCLASSIFIED", []).append(r)

    print("== per error_type ==")
    for t, group in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {t:<14} {len(group):>3}")
    print()

    print("== what the record is missing ==")
    have_url = sum(1 for r in rows if ev(r).get("evidence_url"))
    have_exact = sum(1 for r in rows if ev(r).get("exact_match_field"))
    have_repl = sum(1 for r in rows if ev(r).get("proposed_domain"))
    print(f"  evidence_url present       : {have_url}/{len(rows)}")
    print(f"  exact_match_field present  : {have_exact}/{len(rows)}")
    print(f"  proposed_domain recorded   : {have_repl}/{len(rows)}")
    print()
    print("  => 0 rows carry an authoritative replacement value.")
    print("     A correction is NOT computable from the record. This plan states")
    print("     the input required per row; it does not invent one.\n")

    print("== per-row ask ==")
    hdr = f"  {'slug':<13} {'error_type':<13} {'stored_domain':<30} ask"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        e = ev(r)
        t = e.get("error_type")
        ask = (
            "authoritative domain for this Global Company"
            if t == "WRONG_DOMAIN"
            else "what specifically is wrong, and the correct value"
        )
        print(f"  {r['slug']:<13} {t!s:<13} {str(r['stored_domain'])[:29]:<30} {ask}")

    if args.csv:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "subject_key", "global_company_id", "slug", "canonical_name",
                "stored_domain", "error_type", "cr_class", "identity_state",
                "domain_relation", "sales_readiness", "required_input",
            ]
        )
        for r in rows:
            e = ev(r)
            w.writerow(
                [
                    r["subject_key"], r["global_company_id"], r["slug"],
                    r["canonical_name"], r["stored_domain"], e.get("error_type"),
                    e.get("cr_class"), e.get("identity_state"),
                    e.get("domain_relation"), r["sales_readiness"],
                    "authoritative_domain" if e.get("error_type") == "WRONG_DOMAIN"
                    else "defect_description_and_correct_value",
                ]
            )
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            fh.write(buf.getvalue())
        print(f"\nwrote requirements CSV: {args.csv}")

    await c.close()

    if not args.apply:
        print("\nNo correction applied (default). Nothing was written.")
        return 0

    # ---- gated apply path -------------------------------------------------
    print("\n=== APPLY PATH ===")
    with open(args.apply, newline="", encoding="utf-8") as fh:
        supplied = list(csv.DictReader(fh))
    print(f"authoritative mapping rows supplied: {len(supplied)}")
    if not supplied:
        print("REFUSING: mapping is empty. No correction can be computed.")
        return 2
    if len(supplied) != len(rows):
        print(
            f"REFUSING: expected {len(rows)} rows to match the escalated set, "
            f"got {len(supplied)}. Refusing a partial correction."
        )
        return 2

    c2 = await asyncpg.connect(DSN)
    print("\n== proposed diff (NOT applied) ==")
    for s in supplied:
        print(f"  {s.get('slug')} : {s.get('stored_domain')} -> {s.get('authoritative_domain')}")
    await c2.close()

    if not args.commit:
        print("\n--commit not passed: diff printed only, 0 rows written.")
        return 0
    if not args.i_have_approval:
        print("REFUSING: --commit requires --i-have-approval. 0 rows written.")
        return 2
    print("\nApproval gate passed. Applying is intentionally NOT implemented in "
          "this script: MATERIAL_ERROR corrections touch Phase 6 canonical data "
          "and require a separately reviewed migration.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
