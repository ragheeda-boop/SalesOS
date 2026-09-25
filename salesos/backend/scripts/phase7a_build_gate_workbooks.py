"""Build the G3/G4/G5 human-review workbooks from the ACTIVE Phase 6 version.

Read-only against salesos_test (one READ ONLY transaction) plus the local MUHIDE
source files. Decision columns are left empty; run
phase7a_enrich_gate_workbooks.py afterwards for evidence/suggestions.

    python scripts/phase7a_build_gate_workbooks.py
"""

from __future__ import annotations

import asyncio
import collections
import csv
import hashlib
import math
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.master_data.phase6.pipeline import ACTIVE_CLASSIFICATION_VERSION  # noqa: E402
from app.modules.master_data.phase7.usability import is_out_of_market  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "data" / "phase7" / "gate_review_20260925"
EXTRACT = Path.home() / "Downloads" / "MUHIDE_extracted"
G3_IDS = ["MA-0263479", "MA-0272304", "MA-0269017", "MA-0279593", "MA-0279803"]
REVIEW_COLS = ["decision (CORRECT / MATERIAL_ERROR / CANNOT_VERIFY)",
               "error_type (NOT_EXIST / WRONG_IDENTITY / WRONG_DOMAIN / WRONG_CR / OTHER)",
               "evidence_url", "reviewer", "reviewed_at", "notes"]
G3_COLS = ["decision (CONFIRMED_VALID_CR / NOT_A_CR / UNRESOLVED_ESCALATE)",
           "reviewer", "reviewed_at", "notes"]
V = ACTIVE_CLASSIFICATION_VERSION
G5_SPOT_SIZE = 150  # report 110 recommendation H


def _h(seed: str, key: str) -> str:
    return hashlib.sha256(f"{seed}|{key}".encode()).hexdigest()


def _src(x: dict) -> str:
    s = [t.strip() for t in x["Source_Systems"].split(";") if t.strip()]
    return s[0] if len(s) == 1 else "MULTI_SOURCE"


def _noncom(x: dict) -> bool:
    return "NCNP" in x["Source_Systems"] or (x["Primary_Domain"] or "").lower().endswith(".gov.sa")


async def _load():
    c = await asyncpg.connect(host="localhost", user="salesos",
                              password="salesos_dev_password", database="salesos_test")
    try:
        assert await c.fetchval("SELECT current_database()") == "salesos_test"
        async with c.transaction(readonly=True):
            mp = {str(r["gid"]): r["legacy_id"] for r in await c.fetch(
                "SELECT legacy_id, global_entity_id gid FROM md_legacy_id_mappings "
                "WHERE legacy_id_type='LEGACY_MUHIDE_MA_ID'")}
            p1 = await c.fetch(
                """SELECT rc.global_entity_id::text gid, rc.reason, ic.identity_state, ic.sales_readiness,
                          ic.cr_class, g.canonical_name, g.city,
                          CASE WHEN ic.signals ? 'display_domain' THEN ic.signals->>'display_domain'
                               ELSE g.domain END AS domain
                     FROM md_review_candidates rc
                     JOIN md_identity_classifications ic ON ic.global_entity_id = rc.global_entity_id
                          AND ic.classification_version = $1
                     JOIN md_global_companies g ON g.id = rc.global_entity_id
                    WHERE rc.candidate_type = 'P1' AND rc.status = 'pending'""", V)
            g3 = {r["legacy_id"]: r for r in await c.fetch(
                """SELECT m.legacy_id, m.global_entity_id::text gid, ic.cr_class, ic.identity_state,
                          ic.sales_readiness
                     FROM md_legacy_id_mappings m
                     JOIN md_identity_classifications ic ON ic.global_entity_id = m.global_entity_id
                          AND ic.classification_version = $1
                    WHERE m.legacy_id_type = 'LEGACY_MUHIDE_MA_ID' AND m.legacy_id = ANY($2)""",
                V, G3_IDS)}
            disp = {str(r["gid"]): r["d"] for r in await c.fetch(
                """SELECT global_entity_id gid,
                          CASE WHEN signals ? 'display_domain' THEN signals->>'display_domain' END AS d
                     FROM md_identity_classifications WHERE classification_version = $1""", V)}
    finally:
        await c.close()
    return mp, p1, g3, disp


def main() -> None:
    master = {x["Master Account ID"]: x for x in csv.DictReader(
        open(EXTRACT / "01_Master_Accounts.csv", encoding="utf-8-sig"))}
    mp, p1, g3, disp = asyncio.run(_load())
    per_src = collections.defaultdict(list)
    with open(EXTRACT / "03_Source_Map.csv", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if r["Master Account ID"] in G3_IDS:
                per_src[r["Master Account ID"]].append(
                    f"{r['Source System']}: name={r['Source Company Name']} | cr={r['Source CR Number']}"
                    f" | domain={r['Source Domain']}")

    with open(OUT / "G3_HUMAN_REVIEW_5_ACCOUNTS.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ma_id", "global_company_id", "name", "domain", "city", "cr_numbers_raw",
                    "per_source_evidence", "cr_class_now", "identity_now", "readiness_now",
                    "question"] + G3_COLS)
        for k in G3_IDS:
            x, r = master[k], g3[k]
            q = ("Is the 10-digit number (7-series, possibly a unified national number) a real CR?"
                 if "NCNP" in x["Source_Systems"] else "Multi-value SOCPA field: which value, if any, is the real CR?")
            w.writerow([k, r["gid"], x["Canonical_Company_Name"], x["Primary_Domain"], x["City"],
                        x["CR_Numbers"], " || ".join(per_src[k]), r["cr_class"], r["identity_state"],
                        r["sales_readiness"], q] + [""] * len(G3_COLS))

    head = ["review_set", "reason", "source_stratum", "ma_id", "global_company_id", "name", "domain",
            "city", "cr_numbers", "cr_class", "identity_state", "sales_readiness", "non_commercial"]

    def write(name: str, rows: list) -> None:
        with open(OUT / name, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(head + REVIEW_COLS)
            for tag, r in rows:
                x = master[mp[r["gid"]]]
                w.writerow([tag, r["reason"], _src(x), x["Master Account ID"], r["gid"], r["canonical_name"],
                            r["domain"], r["city"], x["CR_Numbers"], r["cr_class"], r["identity_state"],
                            r["sales_readiness"], _noncom(x)] + [""] * len(REVIEW_COLS))

    corr = collections.defaultdict(list)
    for r in p1:
        if r["reason"] == "CORROBORATION_REVIEW":
            corr[_src(master[mp[r["gid"]]])].append(r)
    fc = [("FULL", r) for r in p1 if r["reason"] == "FIELD_CONFLICT_REVIEW"]
    wk = [("FULL", r) for r in p1 if r["reason"] == "WEAK_IDENTITY_REVIEW"]
    sm = [("SAMPLE_5PCT", r) for s, v in sorted(corr.items())
          for r in sorted(v, key=lambda r: _h("G4-CORR-" + V, r["gid"]))[:max(1, math.ceil(0.05 * len(v)))]]
    write("G4_P1_FIELD_CONFLICT_FULL.csv", fc)
    write("G4_P1_WEAK_IDENTITY_FULL.csv", wk)
    write("G4_P1_CORROBORATION_SAMPLE_5PCT.csv", sm)

    sample_dir = OUT / "p2_sample_v5"
    sample = next(sample_dir.glob("*.csv"))
    pool = collections.defaultdict(list)
    for r in csv.DictReader(open(sample, encoding="utf-8-sig")):
        if r["sampling_stratum"] != "SALES_READY_WITH_REVIEW":
            continue
        x = master[mp[r["global_company_id"]]]
        apollo_only = x["Source_Systems"].strip() == "Apollo Accounts"
        if not _noncom(x) and not is_out_of_market(
            apollo_only=apollo_only, city=x["City"], domain=disp.get(r["global_company_id"])
        ):
            pool[_src(x)].append((r, x))
    tot = sum(len(v) for v in pool.values())
    alloc = {s: max(1, round(G5_SPOT_SIZE * len(v) / tot)) for s, v in pool.items()}
    with open(OUT / "G5_SRWR_REAL_WORLD_SPOT_CHECK.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_stratum", "ma_id", "global_company_id", "name", "domain", "city",
                    "cr_numbers", "apollo_ids"] + REVIEW_COLS)
        n = 0
        for s, v in sorted(pool.items()):
            for r, x in sorted(v, key=lambda t: _h("G5-SPOT-" + V, t[0]["global_company_id"]))[:alloc[s]]:
                w.writerow([s, x["Master Account ID"], r["global_company_id"], x["Canonical_Company_Name"],
                            disp.get(r["global_company_id"]) or "", x["City"], x["CR_Numbers"],
                            x["Apollo_Account_IDs"]]
                           + [""] * len(REVIEW_COLS))
                n += 1
    print({"version": V, "G3": len(G3_IDS), "G4_field_conflict": len(fc), "G4_weak": len(wk),
           "G4_corroboration_sample": len(sm), "G4_corroboration_total": sum(len(v) for v in corr.values()),
           "G5_spot_check": n, "G5_alloc": alloc})


if __name__ == "__main__":
    main()
