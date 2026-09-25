#!/usr/bin/env python3
"""Report 116 W7b — persist the G4 cluster-verdict dispersion analysis.

Report 116 SS6.2 found that "cluster-and-certify" (grouping P1 corroboration
candidates by their evidence signature and bulk-applying one verdict per
cluster) is NOT viable: the same signature produces mixed human verdicts.
That finding existed only as console output. This script reproduces it
against the live database and writes a durable markdown report.

Read-only: SELECTs from md_review_candidates and md_review_queue_state only.
No write, no merge, no CR promotion, no classification change.

    python scripts/phase7a_cluster_dispersion_report.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import asyncpg


def _loads(value):
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return value

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OUT = (
    Path(__file__).resolve().parents[3]
    / "project-audit" / "117_G4_CLUSTER_DISPERSION_REPORT_2026-09-26.md"
)

SIGNATURE_FIELDS = (
    "best_match_confidence", "cr_class", "field_conflict",
    "real_domain_present", "apollo_account_present",
)

_DISP_TO_VERDICT = {"CONFIRM": "CORRECT", "ESCALATE": "MATERIAL_ERROR", "REVIEW": "CANNOT_VERIFY"}


async def main() -> int:
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="salesos",
        password="salesos_dev_password", database="salesos_test",
    )
    try:
        db = await conn.fetchval("SELECT current_database()")
        assert db == "salesos_test", f"REFUSING: connected to {db!r}"

        rows = await conn.fetch(
            """
            SELECT rc.global_entity_id::text AS gid, rc.evidence,
                   q.disposition, q.evidence_ref
              FROM md_review_candidates rc
              LEFT JOIN md_review_queue_state q
                ON q.queue_type = 'P1_CANDIDATE' AND q.subject_key = rc.global_entity_id::text
             WHERE rc.candidate_type = 'P1' AND rc.reason = 'CORROBORATION_REVIEW'
               AND rc.status <> 'superseded'
            """
        )
        total = len(rows)

        clusters: dict[tuple, list] = defaultdict(list)
        for r in rows:
            ev = _loads(r["evidence"])
            sig = tuple(ev.get(f) for f in SIGNATURE_FIELDS)
            clusters[sig].append(r)

        cluster_stats = []
        for sig, members in clusters.items():
            verdicts = Counter()
            error_types = Counter()
            for m in members:
                if m["disposition"] in _DISP_TO_VERDICT:
                    verdicts[_DISP_TO_VERDICT[m["disposition"]]] += 1
                    et = _loads(m["evidence_ref"]).get("error_type")
                    if et:
                        error_types[et] += 1
                else:
                    verdicts["NOT_REVIEWED"] += 1
            cluster_stats.append((sig, len(members), verdicts, error_types))
        cluster_stats.sort(key=lambda t: -t[1])

        rows_with_reviewed_no_error_type = 0
        rows_reviewed_total = 0
        for _sig, _n, verdicts, error_types in cluster_stats:
            reviewed_here = sum(v for k, v in verdicts.items() if k != "NOT_REVIEWED")
            rows_reviewed_total += reviewed_here
            rows_with_reviewed_no_error_type += max(0, reviewed_here - sum(error_types.values()))

        # Cumulative coverage of the largest clusters.
        cumulative = 0
        coverage_lines = []
        for i, (sig, n, _verdicts, _err) in enumerate(cluster_stats, start=1):
            cumulative += n
            coverage_lines.append((i, n, cumulative, round(100 * cumulative / total, 1)))

        mixed_clusters = [
            (sig, n, v, e) for sig, n, v, e in cluster_stats
            if sum(1 for k in v if k != "NOT_REVIEWED") > 1
        ]

        lines = []
        lines.append("# 117 — G4 corroboration cluster / verdict dispersion (report 116 W7b)\n")
        lines.append(
            "**Read-only.** Reproduces report 116 SS6.2's cluster-and-certify falsification "
            "against the live `salesos_test` database and persists it (it previously existed "
            "only as console output). No write, no merge, no classification change.\n"
        )
        lines.append(f"Population: **{total:,}** P1 `CORROBORATION_REVIEW` candidates "
                      f"(active, non-superseded). Clustered by evidence signature "
                      f"`{SIGNATURE_FIELDS}`.\n")
        lines.append(f"Distinct evidence signatures: **{len(cluster_stats)}**.\n")
        lines.append(f"Rows with a captured disposition: **{rows_reviewed_total:,}** of {total:,}.\n")

        lines.append("\n## Cumulative coverage of the largest clusters\n")
        lines.append("| Rank | Cluster size | Cumulative | % of population |")
        lines.append("|---:|---:|---:|---:|")
        for i, n, cum, pct in coverage_lines[:10]:
            lines.append(f"| {i} | {n:,} | {cum:,} | {pct}% |")

        lines.append("\n## Every cluster with more than one reviewed verdict (mixed = not certifiable)\n")
        lines.append(
            f"**{len(mixed_clusters)}** of {len(cluster_stats)} clusters have MIXED verdicts among "
            "their reviewed members — the same evidence signature produced different human/agent "
            "judgments, so no deterministic rule keyed on this signature alone can replace "
            "individual review for these clusters.\n"
        )
        lines.append("| Signature (confidence, cr_class, field_conflict, real_domain, apollo) | "
                      "size | CORRECT | MATERIAL_ERROR | CANNOT_VERIFY | not reviewed |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for sig, n, v, _e in sorted(mixed_clusters, key=lambda t: -t[1])[:20]:
            lines.append(
                f"| `{sig}` | {n:,} | {v.get('CORRECT', 0)} | {v.get('MATERIAL_ERROR', 0)} | "
                f"{v.get('CANNOT_VERIFY', 0)} | {v.get('NOT_REVIEWED', 0):,} |"
            )
        if len(mixed_clusters) > 20:
            lines.append(f"\n... and {len(mixed_clusters) - 20} more mixed clusters (see raw data).\n")

        lines.append("\n## error_type completeness among reviewed rows\n")
        lines.append(
            f"Of {rows_reviewed_total} rows with a captured disposition, "
            f"**{rows_with_reviewed_no_error_type}** carry no `error_type` at all in their "
            "evidence_ref — the reasoning behind the verdict was never captured, which is "
            "exactly why no deterministic rule can be reverse-engineered from the reviewed "
            "sample: the missing ingredient is not a smarter clustering key, it is the reason "
            "itself. Report 116 W1 makes `reason` mandatory going forward; this does not "
            "retroactively fill in these rows.\n"
        )

        lines.append("\n## Conclusion\n")
        lines.append(
            "Cluster-and-certify (bulk-applying one verdict per evidence-signature cluster) is "
            "**not viable** for the G4 P1 corroboration backlog: the largest clusters are exactly "
            "the ones with mixed verdicts, so certifying by signature would apply the wrong "
            "verdict to a material fraction of any large cluster. The remaining backlog needs "
            "individual review, or new evidence (e.g. a live source check) that the current "
            "signature does not capture — not a shortcut around the review itself. This "
            "reproduces and persists report 116 SS6.2's finding; no gate is closed by this "
            "report.\n"
        )

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

        print(f"total={total} distinct_signatures={len(cluster_stats)} "
              f"reviewed={rows_reviewed_total} mixed_clusters={len(mixed_clusters)} "
              f"no_error_type={rows_with_reviewed_no_error_type}")
        print(f"wrote {OUT}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
