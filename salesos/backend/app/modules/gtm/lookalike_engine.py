"""STORY-11-04 — Lookalike engine (deterministic, Opportunity-history shaped).

Honesty: CI uses in-memory won/lost fixtures — live Opportunity ML backtest
not claimed. Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.gtm.lookalike import (
    LookalikeError,
    LookalikeHit,
    LookalikeSeed,
    OpportunityRecord,
)


def _norm(value: str) -> str:
    return (value or "").strip().lower()


@dataclass
class MemOpportunityHistory:
    """Tenant-scoped Opportunity-shaped training set for lookalikes."""

    records: list[OpportunityRecord] = field(default_factory=list)

    def for_tenant(self, tenant_id: str) -> list[OpportunityRecord]:
        tid = str(tenant_id)
        return [r for r in self.records if not r.tenant_id or r.tenant_id == tid]

    def counts(self, tenant_id: str) -> tuple[int, int]:
        rows = self.for_tenant(tenant_id)
        won = sum(1 for r in rows if r.outcome == "won")
        lost = sum(1 for r in rows if r.outcome == "lost")
        return won, lost


def build_demo_opportunity_history(*, tenant_id: str = "") -> MemOpportunityHistory:
    """Deterministic won/lost fixture (not live Muhide Opportunity rows)."""
    rows = [
        OpportunityRecord("o1", "Won Tech Riyadh", "technology", "riyadh", 80, "won", tenant_id),
        OpportunityRecord("o2", "Won Tech Jeddah", "technology", "jeddah", 120, "won", tenant_id),
        OpportunityRecord("o3", "Lost Retail Riyadh", "retail", "riyadh", 40, "lost", tenant_id),
        OpportunityRecord("o4", "Won Health Dammam", "healthcare", "dammam", 200, "won", tenant_id),
        OpportunityRecord("o5", "Lost Tech Makkah", "technology", "makkah", 15, "lost", tenant_id),
        OpportunityRecord(
            "o6", "Won Construct Riyadh", "construction", "riyadh", 90, "won", tenant_id
        ),
        OpportunityRecord(
            "o7", "Lost Health Jeddah", "healthcare", "jeddah", 50, "lost", tenant_id
        ),
        OpportunityRecord("o8", "Won Tech Riyadh B", "technology", "riyadh", 60, "won", tenant_id),
    ]
    return MemOpportunityHistory(records=rows)


def _similarity(seed: LookalikeSeed, row: OpportunityRecord) -> tuple[float, list[str]]:
    matched: list[str] = []
    score = 0.0
    maximum = 0.0

    if seed.industry:
        maximum += 1.0
        if _norm(row.industry) == seed.industry:
            score += 1.0
            matched.append("industry")
    if seed.city:
        maximum += 1.0
        if _norm(row.city) == seed.city:
            score += 1.0
            matched.append("city")
    if seed.employees_count is not None and row.employees_count is not None:
        maximum += 1.0
        # within 50% band counts as size match
        target = seed.employees_count
        if (
            target > 0
            and abs(row.employees_count - target) / target <= 0.5
            or target == 0
            and row.employees_count == 0
        ):
            score += 1.0
            matched.append("employees")

    # Empty seed bands → soft name token overlap only
    if maximum <= 0:
        seed_tokens = set(_norm(seed.company_name).split())
        row_tokens = set(_norm(row.company_name).split())
        if seed_tokens and row_tokens:
            overlap = len(seed_tokens & row_tokens) / max(len(seed_tokens), 1)
            return round(overlap, 4), (["name"] if overlap > 0 else [])
        return 0.0, []

    return round(score / maximum, 4), matched


def _outcome_affinity(rows: list[OpportunityRecord]) -> str:
    outcomes = {r.outcome for r in rows}
    if outcomes == {"won"}:
        return "won"
    if outcomes == {"lost"}:
        return "lost"
    return "mixed"


def rank_lookalikes(
    seed: LookalikeSeed,
    history: MemOpportunityHistory,
    *,
    tenant_id: str,
    limit: int = 10,
    exclude_seed_name: bool = True,
) -> tuple[list[LookalikeHit], int, int]:
    """Rank Opportunity-history companies by firmographic similarity to seed."""
    if not isinstance(seed, LookalikeSeed):
        raise LookalikeError("seed required")
    lim = max(1, min(int(limit), 50))
    won_n, lost_n = history.counts(tenant_id)
    if won_n + lost_n < 1:
        raise LookalikeError("tenant opportunity history is empty")

    # Group by company_name to collapse duplicate outcomes
    by_name: dict[str, list[OpportunityRecord]] = {}
    for row in history.for_tenant(tenant_id):
        key = _norm(row.company_name)
        if exclude_seed_name and key == _norm(seed.company_name):
            continue
        by_name.setdefault(key, []).append(row)

    scored: list[LookalikeHit] = []
    for _key, group in by_name.items():
        # Prefer won exemplar when present for feature display
        exemplar = next((r for r in group if r.outcome == "won"), group[0])
        sim, matched = _similarity(seed, exemplar)
        if sim <= 0:
            continue
        # Boost when seed aligns with won history pattern
        affinity = _outcome_affinity(group)
        boost = 0.05 if affinity == "won" else (-0.05 if affinity == "lost" else 0.0)
        scored.append(
            LookalikeHit(
                company_id=exemplar.id,
                company_name=exemplar.company_name,
                industry=_norm(exemplar.industry),
                city=_norm(exemplar.city),
                employees_count=exemplar.employees_count,
                similarity=round(min(1.0, max(0.0, sim + boost)), 4),
                outcome_affinity=affinity,
                matched_features=matched,
            )
        )

    scored.sort(key=lambda h: (-h.similarity, h.company_name))
    return scored[:lim], won_n, lost_n
