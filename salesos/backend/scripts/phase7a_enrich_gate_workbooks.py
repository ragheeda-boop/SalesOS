"""Add per-source evidence and a MACHINE SUGGESTION to the gate review workbooks.

Local files only (the MUHIDE source map); no database access, no network.
The suggestion is an aid for the human reviewer, never a decision: the
decision columns are left empty (report 106/107).

    python scripts/phase7a_enrich_gate_workbooks.py
"""

from __future__ import annotations

import collections
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WB = ROOT / "docs" / "data" / "phase7" / "gate_review_20260925"
SOURCE_MAP = Path.home() / "Downloads" / "MUHIDE_extracted" / "03_Source_Map.csv"
FILES = [
    "G4_P1_FIELD_CONFLICT_FULL.csv",
    "G4_P1_WEAK_IDENTITY_FULL.csv",
    "G4_P1_CORROBORATION_SAMPLE_5PCT.csv",
    "G5_SRWR_REAL_WORLD_SPOT_CHECK.csv",
]
NEW_COLS = ["evidence_domains_by_source", "evidence_names_by_source", "domain_relation",
            "machine_suggestion (NOT A DECISION)", "suggestion_reason"]
GENERIC_TLDS = {"com", "sa", "net", "org", "co", "info", "biz", "edu", "gov", "me", "io"}
STOP = {"co", "company", "est", "establishment", "trading", "for", "and", "the", "group", "ltd", "llc"}


def _base(domain: str) -> str:
    d = domain.lower().strip().removeprefix("http://").removeprefix("https://").split("/")[0]
    d = d.removeprefix("www.")
    labels = [x for x in d.split(".") if x]
    while len(labels) > 1 and labels[-1] in GENERIC_TLDS:
        labels.pop()
    return labels[-1] if labels else d


def _latin_tokens(name: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]{3,}", name.lower()) if t not in STOP}


def _relation(domains: set[str]) -> str:
    bases = {_base(d) for d in domains if d}
    if len(domains) <= 1:
        return "SINGLE"
    return "ALIAS_SAME_BASE" if len(bases) == 1 else "DIFFERENT_BASES"


def _suggest(reason: str, domains: set[str], names: set[str], relation: str) -> tuple[str, str]:
    toks = set().union(*(_latin_tokens(n) for n in names)) if names else set()
    matching = sorted(d for d in domains if any(t in _base(d) or _base(d) in t for t in toks))
    if reason == "FIELD_CONFLICT_REVIEW":
        if relation == "ALIAS_SAME_BASE":
            return "LIKELY_CORRECT", "domains differ only by www/TLD (same base name)"
        if matching and len(matching) < len(domains):
            return "NEEDS_HUMAN", f"domains unrelated; name matches {matching[0]}, check the other(s)"
        return "NEEDS_HUMAN", "sources report unrelated domains; confirm which belongs to the entity"
    if matching:
        return "LIKELY_CORRECT", f"company name matches domain {matching[0]}"
    if not toks:
        return "NEEDS_HUMAN", "Arabic-only name; domain cannot be matched automatically"
    return "NEEDS_HUMAN", "company name does not appear in the domain"


def main() -> None:
    wanted: set[str] = set()
    for f in FILES:
        with open(WB / f, encoding="utf-8-sig") as fh:
            wanted |= {r["ma_id"] for r in csv.DictReader(fh)}
    by_ma: dict[str, dict[str, dict[str, set[str]]]] = collections.defaultdict(
        lambda: collections.defaultdict(lambda: {"domain": set(), "name": set()}))
    with open(SOURCE_MAP, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            ma = r["Master Account ID"]
            if ma in wanted:
                e = by_ma[ma][r["Source System"]]
                if r["Source Domain"].strip():
                    e["domain"].add(r["Source Domain"].strip().lower())
                if r["Source Company Name"].strip():
                    e["name"].add(r["Source Company Name"].strip())

    tally: dict[str, collections.Counter] = {}
    for f in FILES:
        path = WB / f
        with open(path, encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            header = [c for c in reader.fieldnames if c not in NEW_COLS]
            rows = list(reader)
        cut = next(i for i, c in enumerate(header) if c.startswith("decision"))
        out_header = header[:cut] + NEW_COLS + header[cut:]
        tally[f] = collections.Counter()
        for r in rows:
            src = by_ma.get(r["ma_id"], {})
            domains = set().union(*(v["domain"] for v in src.values())) if src else set()
            if r.get("domain"):
                domains.add(r["domain"].lower())
            names = set().union(*(v["name"] for v in src.values())) if src else set()
            if r.get("name"):
                names.add(r["name"])
            relation = _relation(domains)
            sug, why = _suggest(r.get("reason", "G5"), domains, names, relation)
            r["evidence_domains_by_source"] = " || ".join(
                f"{s}: {', '.join(sorted(v['domain']))}" for s, v in sorted(src.items()) if v["domain"])
            r["evidence_names_by_source"] = " || ".join(
                f"{s}: {' | '.join(sorted(v['name']))}" for s, v in sorted(src.items()) if v["name"])
            r["domain_relation"] = relation
            r["machine_suggestion (NOT A DECISION)"] = sug
            r["suggestion_reason"] = why
            tally[f][sug] += 1
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=out_header)
            w.writeheader()
            w.writerows(rows)
    for f, c in tally.items():
        print(f, dict(c))


if __name__ == "__main__":
    main()
