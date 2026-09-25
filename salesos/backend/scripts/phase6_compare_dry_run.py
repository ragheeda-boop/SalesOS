"""Compare a Phase 6 dry-run changes CSV against the current salesos_test state.

Read-only: one READ ONLY transaction, no writes. Used to measure the effect of
PO decision G3-2 (report 104) before any real run.

    python scripts/phase6_compare_dry_run.py <changes.csv> <out.json>
"""

from __future__ import annotations

import ast
import asyncio
import collections
import csv
import json
import sys

import asyncpg

csv.field_size_limit(10**9)


def _payload(v: str) -> dict:
    try:
        return json.loads(v)
    except ValueError:
        return ast.literal_eval(v)


async def main(changes_csv: str, out_json: str, baseline: str = "OPTION_C_1") -> None:
    after_id: dict[str, dict] = {}
    after_cand: dict[str, set] = collections.defaultdict(set)
    with open(changes_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["table"] == "md_identity_classifications":
                after_id[r["entity_id"]] = _payload(r["payload"])
            elif r["table"] == "md_review_candidates":
                p = _payload(r["payload"])
                after_cand[r["entity_id"]].add((p["candidate_type"], p["reason"]))

    conn = await asyncpg.connect(host="localhost", port=5432, user="salesos",
                                 password="salesos_dev_password", database="salesos_test")
    try:
        assert await conn.fetchval("SELECT current_database()") == "salesos_test"
        async with conn.transaction(readonly=True):
            before = {
                str(r["global_entity_id"]): dict(r)
                for r in await conn.fetch(
                    "SELECT global_entity_id, identity_state, sales_readiness, review_priority, cr_class "
                    "FROM md_identity_classifications WHERE classification_version = $1", baseline)
            }
            cand_before: dict[str, set] = collections.defaultdict(set)
            for r in await conn.fetch(
                    "SELECT global_entity_id, candidate_type, reason FROM md_review_candidates "
                    "WHERE status <> 'superseded'"):
                cand_before[str(r["global_entity_id"])].add((r["candidate_type"], r["reason"]))
            ma = {str(r["global_entity_id"]): r["legacy_id"] for r in await conn.fetch(
                "SELECT legacy_id, global_entity_id FROM md_legacy_id_mappings "
                "WHERE legacy_id_type = 'LEGACY_MUHIDE_MA_ID'")}
    finally:
        await conn.close()

    def dist(d, k):
        return dict(collections.Counter(v[k] for v in d.values()).most_common())

    trans = collections.Counter()
    changed = []
    for gid, a in after_id.items():
        b = before.get(gid)
        if not b:
            trans[("MISSING_BEFORE",)] += 1
            continue
        key = tuple((f, b[f], a[f]) for f in ("sales_readiness", "review_priority", "identity_state")
                    if b[f] != a[f])
        if key:
            trans[key] += 1
            changed.append({"global_company_id": gid, "master_account_id": ma.get(gid),
                            **{f"{f}_before": b[f] for f in ("identity_state", "sales_readiness", "review_priority", "cr_class")},
                            **{f"{f}_after": a[f] for f in ("identity_state", "sales_readiness", "review_priority", "cr_class")}})

    cand_delta = collections.Counter()
    for gid in set(cand_before) | set(after_cand):
        for c in cand_before.get(gid, set()) - after_cand.get(gid, set()):
            cand_delta[("removed",) + c] += 1
        for c in after_cand.get(gid, set()) - cand_before.get(gid, set()):
            cand_delta[("added",) + c] += 1

    out = {
        "accounts_before": len(before),
        "accounts_after": len(after_id),
        "accounts_changed": len(changed),
        "before": {k: dist(before, k) for k in ("sales_readiness", "review_priority", "cr_class")},
        "after": {k: dist(after_id, k) for k in ("sales_readiness", "review_priority", "cr_class")},
        "transitions": [{"change": [list(x) for x in k], "count": v} for k, v in trans.most_common()],
        "review_candidate_delta": [{"change": list(k), "count": v} for k, v in cand_delta.most_common()],
        "changed_accounts": changed,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "changed_accounts"},
                     ensure_ascii=False, indent=1, default=str)[:6000])


if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:4]))
