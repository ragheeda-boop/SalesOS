"""Quality Scorer — Entity Data Quality Assessment.

Computes quality scores for global entities based on:
- Completeness: how many fields are populated
- Accuracy: evidence tier of source data
- Consistency: conflict count vs field count
- Freshness: how recently data was updated
- Provenance: source diversity and authority

Results stored in md_quality_scores table.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ── Completeness Fields ──────────────────────────────────────────────────────

COMPLETENESS_FIELDS = [
    "canonical_name", "canonical_name_ar", "cr_number", "vat_number",
    "unified_national_number", "domain", "website", "city", "region",
    "phone", "email", "address", "industry", "legal_entity_type",
]


# ── Quality Scorer ───────────────────────────────────────────────────────────


class QualityScorer:
    """Computes and persists quality scores for global entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def score_entity(
        self,
        global_entity_id: str,
        entity_type: str = "company",
    ) -> dict[str, Any]:
        """Compute and persist quality score for a single entity.

        Returns the score record.
        """
        now = datetime.now(UTC)

        # Fetch entity
        table = "md_global_companies" if entity_type == "company" else "md_global_people"
        result = await self.session.execute(
            text(f"SELECT * FROM {table} WHERE id = :id"),
            {"id": global_entity_id},
        )
        entity = result.mappings().first()
        if not entity:
            return {}

        entity_dict = dict(entity)

        # Completeness
        completeness = self._compute_completeness(entity_dict)

        # Accuracy (from field provenance authority scores)
        accuracy = await self._compute_accuracy(global_entity_id)

        # Consistency (from conflict count)
        consistency = await self._compute_consistency(global_entity_id)

        # Freshness
        freshness = self._compute_freshness(entity_dict, now)

        # Provenance (source count)
        provenance = await self._compute_provenance(global_entity_id)

        # Overall
        overall = (
            completeness * 0.3
            + accuracy * 0.25
            + consistency * 0.2
            + freshness * 0.1
            + provenance * 0.15
        )

        score_id = str(uuid.uuid4())
        details = {
            "completeness": completeness,
            "accuracy": accuracy,
            "consistency": consistency,
            "freshness": freshness,
            "provenance": provenance,
        }

        await self.session.execute(
            text(
                "INSERT INTO md_quality_scores "
                "(id, global_entity_id, completeness_score, accuracy_score, "
                "consistency_score, freshness_score, provenance_score, "
                "overall_score, scored_at, details) "
                "VALUES (:id, :entity_id, :completeness, :accuracy, "
                ":consistency, :freshness, :provenance, :overall, :now, :details)"
            ),
            {
                "id": score_id,
                "entity_id": global_entity_id,
                "completeness": completeness,
                "accuracy": accuracy,
                "consistency": consistency,
                "freshness": freshness,
                "provenance": provenance,
                "overall": overall,
                "now": now,
                "details": details,
            },
        )

        return {
            "id": score_id,
            "global_entity_id": global_entity_id,
            "completeness_score": completeness,
            "accuracy_score": accuracy,
            "consistency_score": consistency,
            "freshness_score": freshness,
            "provenance_score": provenance,
            "overall_score": overall,
            "scored_at": now.isoformat(),
        }

    async def get_latest_score(
        self,
        global_entity_id: str,
    ) -> dict[str, Any] | None:
        """Get the most recent quality score for an entity."""
        result = await self.session.execute(
            text(
                "SELECT * FROM md_quality_scores "
                "WHERE global_entity_id = :entity_id "
                "ORDER BY scored_at DESC LIMIT 1"
            ),
            {"entity_id": global_entity_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    # ── Scoring Components ────────────────────────────────────────────────

    def _compute_completeness(self, entity: dict) -> float:
        """Fraction of completeness fields that are populated."""
        filled = sum(
            1 for f in COMPLETENESS_FIELDS
            if entity.get(f) and str(entity[f]).strip()
        )
        return filled / len(COMPLETENESS_FIELDS) if COMPLETENESS_FIELDS else 0.0

    async def _compute_accuracy(self, global_entity_id: str) -> float:
        """Average authority score across current field values."""
        result = await self.session.execute(
            text(
                "SELECT AVG(authority_score) AS avg_authority "
                "FROM md_field_provenance "
                "WHERE global_entity_id = :entity_id AND is_current = true"
            ),
            {"entity_id": global_entity_id},
        )
        row = result.mappings().first()
        if row and row["avg_authority"] is not None:
            return float(row["avg_authority"])
        return 0.5  # Default when no provenance data

    async def _compute_consistency(self, global_entity_id: str) -> float:
        """1.0 - (conflicts / total_fields). Higher = more consistent."""
        conflict_result = await self.session.execute(
            text(
                "SELECT COUNT(*) FROM md_entity_conflicts "
                "WHERE global_entity_id = :entity_id AND resolution = 'open'"
            ),
            {"entity_id": global_entity_id},
        )
        conflicts = conflict_result.scalar() or 0

        field_result = await self.session.execute(
            text(
                "SELECT COUNT(DISTINCT field_name) FROM md_field_provenance "
                "WHERE global_entity_id = :entity_id"
            ),
            {"entity_id": global_entity_id},
        )
        total_fields = field_result.scalar() or 1

        return max(0.0, 1.0 - (conflicts / total_fields))

    def _compute_freshness(self, entity: dict, now: datetime) -> float:
        """Score based on how recently data was updated."""
        updated_at = entity.get("updated_at")
        if not updated_at:
            return 0.3

        if isinstance(updated_at, str):
            from datetime import datetime as dt
            updated_at = dt.fromisoformat(updated_at.replace("Z", "+00:00"))

        age_days = (now - updated_at).days
        if age_days <= 7:
            return 1.0
        elif age_days <= 30:
            return 0.8
        elif age_days <= 90:
            return 0.6
        elif age_days <= 365:
            return 0.4
        return 0.2

    async def _compute_provenance(self, global_entity_id: str) -> float:
        """Score based on source diversity (source_count)."""
        result = await self.session.execute(
            text(
                "SELECT source_count FROM md_global_companies WHERE id = :id"
            ),
            {"id": global_entity_id},
        )
        row = result.mappings().first()
        if not row:
            return 0.0

        source_count = row.get("source_count", 1) or 1
        # 1 source = 0.3, 2 = 0.6, 3 = 0.8, 4+ = 1.0
        return min(1.0, 0.3 + (source_count - 1) * 0.23)
