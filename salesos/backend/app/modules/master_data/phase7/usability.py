"""Phase 7 — sales-usability of Phase 6 accounts under PO decisions A2/A3.

A Phase 6 readiness state is not, on its own, permission to sell. Report 91:
- A2: Phase 7 work consuming Phase 6 output must treat the pending human-review
  populations as un-adjudicated (2,661 P3 pairs, 36 short-CR accounts).
- A3: no P2 account is sales-usable until its stratum's sample passes review
  at the PO-set threshold.
- G4 (report 90): P1 review (Tier A conflicts, Tier B spot-check) is open.

This module is the single place those rules are applied. Gate state lives in
``GATES`` as reviewed code rather than a DB flag, so opening a gate requires a
code change plus a closure report — the same audit bar as any other gate.
Read-only: nothing here writes, merges, or adjudicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

READY_STATES = ("SALES_READY", "SALES_READY_WITH_REVIEW")

# Blocker codes (stable API values).
NOT_READY = "NOT_SALES_READY"
P1_REVIEW_OPEN = "P1_REVIEW_GATE_OPEN"  # G4
P2_STRATUM_NOT_ACCEPTED = "P2_STRATUM_NOT_ACCEPTED"  # A3 / G5
P3_PAIR_PENDING = "PENDING_P3_FUZZY_PAIR"  # G2
SHORT_CR_PENDING = "PENDING_SHORT_CR_ADJUDICATION"  # G3
CR_AMBIGUOUS_MULTI = "CR_SUSPICIOUS_MULTI"  # G3 population by classification
NON_COMMERCIAL = "NON_COMMERCIAL_SEGMENT"  # G5-3 (report 104/106)
OUT_OF_MARKET = "OUT_OF_MARKET"  # G5 review (reports 109/110)

# PO decision G5-3 (report 106): non-profits (NCNP register) and government
# bodies (.gov.sa) form a separate, non-commercial segment excluded from
# sales-usable. Reversible by setting this to False.
EXCLUDE_NON_COMMERCIAL = True

# G5 review (report 110): an account known only from Apollo whose city is not a
# Saudi city is a foreign company, not a Saudi sales target. Empty city = kept.
EXCLUDE_OUT_OF_MARKET = True
_SAUDI_CITIES_PATH = (
    __import__("pathlib").Path(__file__).resolve().parents[1] / "phase6" / "data" / "saudi_cities.txt"
)


def _load_saudi_cities() -> frozenset[str]:
    with open(_SAUDI_CITIES_PATH, encoding="utf-8") as fh:
        return frozenset(
            line.strip().lower() for line in fh if line.strip() and not line.startswith("#")
        )


SAUDI_CITIES = _load_saudi_cities()


# Two-letter TLDs widely used as generic names; they say nothing about country.
_GENERIC_CCTLDS = frozenset({"co", "io", "me", "ai", "tv", "cc", "ly", "so", "ws", "fm", "gg", "to", "am", "is", "it", "in"})


def foreign_cctld(domain: str | None) -> bool:
    """True if the domain ends in a non-Saudi country-code TLD (e.g. .com.bd, .cn)."""
    labels = [x for x in (domain or "").strip().lower().rstrip(".").split(".") if x]
    if len(labels) < 2:
        return False
    tld = labels[-1]
    return len(tld) == 2 and tld != "sa" and tld not in _GENERIC_CCTLDS


def is_out_of_market(*, apollo_only: bool, city: str | None, domain: str | None = None) -> bool:
    if not apollo_only:
        return False
    c = (city or "").strip().lower()
    if c:
        return c not in SAUDI_CITIES
    return foreign_cctld(domain)  # empty city: fall back to the domain's country code


@dataclass(frozen=True)
class Gate:
    code: str
    status: str  # OPEN | CLOSED
    source: str


# Update only with a closure report citing the human decision that closed it.
GATES: dict[str, Gate] = {
    "G2": Gate("G2", "OPEN", "report 90 §1; report 91 §2 (P3 pairs never auto-merged)"),
    "G3": Gate("G3", "OPEN", "report 90 §1; report 91 §4.2 (government-ID hard veto)"),
    "G4": Gate("G4", "OPEN", "report 90 §1 (P1 Tier A/B review)"),
    "G5:SALES_READY_WITH_REVIEW": Gate(
        "G5:SALES_READY_WITH_REVIEW", "OPEN", "report 91 §3 (3% sample; threshold PO-set)"
    ),
    "G5:ENRICHMENT_REQUIRED": Gate(
        "G5:ENRICHMENT_REQUIRED", "OPEN", "report 91 §3 (1% sample; threshold PO-set)"
    ),
}


def _open(key: str, gates: dict[str, Gate]) -> bool:
    gate = gates.get(key)
    return gate is None or gate.status != "CLOSED"  # unknown gate = fail closed


def account_blockers(
    *,
    sales_readiness: str,
    review_priority: str,
    cr_class: str | None,
    in_pending_p3_pair: bool,
    in_pending_short_cr: bool,
    non_commercial: bool = False,
    out_of_market: bool = False,
    gates: dict[str, Gate] = GATES,
) -> list[str]:
    """Every reason this account may not be treated as sales-usable (empty = usable)."""
    blockers: list[str] = []
    if sales_readiness not in READY_STATES:
        blockers.append(NOT_READY)
    if review_priority == "P1" and _open("G4", gates):
        blockers.append(P1_REVIEW_OPEN)
    if review_priority == "P2" and _open(f"G5:{sales_readiness}", gates):
        blockers.append(P2_STRATUM_NOT_ACCEPTED)
    if in_pending_p3_pair and _open("G2", gates):
        blockers.append(P3_PAIR_PENDING)
    if in_pending_short_cr and _open("G3", gates):
        blockers.append(SHORT_CR_PENDING)
    if cr_class == "SUSPICIOUS_MULTI" and _open("G3", gates):
        blockers.append(CR_AMBIGUOUS_MULTI)
    if non_commercial and EXCLUDE_NON_COMMERCIAL:
        blockers.append(NON_COMMERCIAL)
    if out_of_market and EXCLUDE_OUT_OF_MARKET:
        blockers.append(OUT_OF_MARKET)
    return blockers


_FACTS_SQL = """
WITH p3 AS (
    SELECT global_company_id AS id FROM md_review_queue_state
     WHERE queue_type = 'P3_PAIR' AND status = 'pending' AND global_company_id IS NOT NULL
    UNION
    SELECT global_company_id_b FROM md_review_queue_state
     WHERE queue_type = 'P3_PAIR' AND status = 'pending' AND global_company_id_b IS NOT NULL
), scr AS (
    SELECT global_company_id AS id FROM md_review_queue_state
     WHERE queue_type = 'SHORT_CR' AND status = 'pending' AND global_company_id IS NOT NULL
), src AS (
    SELECT m.global_entity_id AS id,
           bool_or(s.raw_payload->>'Source System' = 'NCNP') AS has_ncnp,
           bool_and(s.raw_payload->>'Source System' = 'Apollo Accounts') AS apollo_only
      FROM md_source_rows s
      JOIN md_legacy_id_mappings m
        ON m.legacy_id_type = 'LEGACY_MUHIDE_MA_ID'
       AND m.legacy_id = s.raw_payload->>'Master Account ID'
     WHERE s.source_id = 'muhide_source_map'
     GROUP BY m.global_entity_id
)
SELECT ic.global_entity_id, g.slug, g.canonical_name,
       CASE WHEN ic.signals ? 'display_domain' THEN ic.signals->>'display_domain'
            ELSE g.domain END AS domain,
       g.city,
       ic.sales_readiness, ic.review_priority, ic.cr_class,
       (p3.id IS NOT NULL) AS in_p3, (scr.id IS NOT NULL) AS in_scr,
       (coalesce(src.has_ncnp, false) OR lower(coalesce(g.domain, '')) LIKE '%.gov.sa') AS non_commercial,
       coalesce(src.apollo_only, false) AS apollo_only
  FROM md_identity_classifications ic
  JOIN md_global_companies g ON g.id = ic.global_entity_id
  LEFT JOIN p3 ON p3.id = ic.global_entity_id
  LEFT JOIN scr ON scr.id = ic.global_entity_id
  LEFT JOIN src ON src.id = ic.global_entity_id
 WHERE ic.sales_readiness = ANY(:ready)
   AND ic.classification_version = :version
 ORDER BY g.canonical_name, ic.global_entity_id
"""


async def _load(session: AsyncSession, gates: dict[str, Gate] = GATES) -> list[dict[str, Any]]:
    from app.modules.master_data.phase6.pipeline import ACTIVE_CLASSIFICATION_VERSION

    rows = await session.execute(
        text(_FACTS_SQL),
        {"ready": list(READY_STATES), "version": ACTIVE_CLASSIFICATION_VERSION},
    )
    out = []
    for r in rows.mappings():
        blockers = account_blockers(
            sales_readiness=r["sales_readiness"],
            review_priority=r["review_priority"],
            cr_class=r["cr_class"],
            in_pending_p3_pair=r["in_p3"],
            in_pending_short_cr=r["in_scr"],
            non_commercial=r["non_commercial"],
            out_of_market=is_out_of_market(
                apollo_only=r["apollo_only"], city=r["city"], domain=r["domain"]
            ),
            gates=gates,
        )
        out.append({
            "global_company_id": str(r["global_entity_id"]),
            "slug": r["slug"],
            "name": r["canonical_name"],
            "domain": r["domain"],
            "city": r["city"],
            "sales_readiness": r["sales_readiness"],
            "review_priority": r["review_priority"],
            "usable": not blockers,
            "blockers": blockers,
        })
    return out


async def usability_summary(session: AsyncSession, gates: dict[str, Gate] = GATES) -> dict[str, Any]:
    accounts = await _load(session, gates)
    by_readiness: dict[str, dict[str, int]] = {}
    by_blocker: dict[str, int] = {}
    for a in accounts:
        bucket = by_readiness.setdefault(a["sales_readiness"], {"total": 0, "usable": 0})
        bucket["total"] += 1
        bucket["usable"] += a["usable"]
        for b in a["blockers"]:
            by_blocker[b] = by_blocker.get(b, 0) + 1
    return {
        "ready_accounts": len(accounts),
        "usable_accounts": sum(a["usable"] for a in accounts),
        "by_readiness": by_readiness,
        "by_blocker": dict(sorted(by_blocker.items())),
        "gates": {k: {"status": g.status, "source": g.source} for k, g in gates.items()},
    }


async def list_accounts(
    session: AsyncSession, *, usable: bool | None, blocker: str | None, offset: int, limit: int
) -> tuple[list[dict[str, Any]], int]:
    accounts = await _load(session)
    if usable is not None:
        accounts = [a for a in accounts if a["usable"] is usable]
    if blocker:
        accounts = [a for a in accounts if blocker in a["blockers"]]
    return accounts[offset:offset + limit], len(accounts)
