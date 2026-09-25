"""Map every MUHIDE master account to an identity state + sales readiness (deterministic)."""
import asyncio, asyncpg, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.entity_resolution.resolution_policy import (
    assess_identity, IdentityState, SalesReadiness, classify_cr, _is_strong_domain,
)

async def main():
    c = await asyncpg.connect(host="localhost", port=5432, user="salesos",
                               password="salesos_dev_password", database="salesos_test")

    rows = await c.fetch("""
        SELECT raw_payload->>'Master Account ID' AS ma,
               raw_payload->>'CR_Numbers' AS crs,
               raw_payload->>'ICF_CR' AS vat,
               raw_payload->>'Primary_Domain' AS domain,
               raw_payload->>'Source_Systems' AS src_systems,
               raw_payload->>'Distinct_Source_System_Count' AS src_count,
               raw_payload->>'Has_Email' AS has_email,
               raw_payload->>'Has_Phone' AS has_phone,
               raw_payload->>'Primary_Email' AS email
        FROM md_source_rows WHERE source_id='muhide_master_accounts'
    """)
    print(f"Total master accounts: {len(rows):,}")

    from collections import Counter
    id_state = Counter()
    sales = Counter()
    cr_class = Counter()
    review = Counter()

    for r in rows:
        # source_count: Distinct_Source_System_Count (a real source-system count)
        try:
            src_count = int(r["src_count"]) if r["src_count"] else 1
        except (ValueError, TypeError):
            src_count = 1
        # independent: genuinely independent source identity; use source-system count
        indep = src_count

        a = assess_identity(
            cr_number=r["crs"],
            vat_number=None,
            domain=r["domain"],
            source_count=src_count,
            independent_source_count=indep,
            has_contactable_email=bool(r["has_email"]) and str(r["has_email"]).lower() == "true",
            has_phone=bool(r["has_phone"]) and str(r["has_phone"]).lower() == "true",
        )
        id_state[a.identity_state.value] += 1
        sales[a.sales_readiness.value] += 1
        review[a.review_priority] += 1
        cr_class[a.cr_class] += 1

    print("\n=== IDENTITY STATE (deterministic) ===")
    for k, v in id_state.most_common():
        print(f"  {k:<32} {v:>8,}  ({v/len(rows)*100:.2f}%)")

    print("\n=== SALES READINESS ===")
    for k, v in sales.most_common():
        print(f"  {k:<32} {v:>8,}  ({v/len(rows)*100:.2f}%)")

    print("\n=== REVIEW PRIORITY ===")
    for k, v in sorted(review.items()):
        print(f"  {k}  {v:>8,}")

    print("\n=== CR CLASS ===")
    for k, v in cr_class.most_common():
        print(f"  {k:<20} {v:>8,}")

    # Compare to Data Intelligence baseline
    print("\n=== DATA INTELLIGENCE BASELINE (dial-across only) ===")
    print("  REVIEW_REQUIRED 198,157 (66.78%) | WEAK_IDENTITY 78,282 (26.38%)")
    print("  DETERMINISTIC_SINGLE_SOURCE 12,267 (4.13%) | STRONG_MULTI_SOURCE 4,187 (1.41%)")
    print("  GOVERNMENT_ANCHORED 3,381 (1.14%) | CONFLICTING_IDENTITY 344 (0.12%) | NO_VERIFIABLE_IDENTITY 128 (0.04%)")

    await c.close()

asyncio.run(main())
