"""Field Provenance Tracking — Per-Field Source & Authority.

Every field value on a global entity carries provenance:
- Which source record supplied this value
- What authority score it has (government > deterministic > fuzzy)
- Whether it conflicts with other known values
- Whether it is the current authoritative value

Uses md_field_provenance table with the UNIQUE partial index:
  (global_entity_id, field_name) WHERE is_current = true

This ensures at most ONE current value per field per entity.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entity_resolution.resolution_policy import (
    EvidenceTier,
    SIGNAL_WEIGHTS,
)


# ── Authority Score ──────────────────────────────────────────────────────────

TIER_AUTHORITY: dict[EvidenceTier, float] = {
    EvidenceTier.GOVERNMENT_ANCHOR: 1.0,
    EvidenceTier.STRONG_DETERMINISTIC: 0.8,
    EvidenceTier.WEAK_DETERMINISTIC: 0.6,
    EvidenceTier.NORMALIZED_EXACT: 0.5,
    EvidenceTier.FUZZY: 0.3,
}


def compute_authority_score(signal_name: str) -> float:
    """Compute authority score for a signal name."""
    if signal_name in SIGNAL_WEIGHTS:
        weight, tier = SIGNAL_WEIGHTS[signal_name]
        return TIER_AUTHORITY.get(tier, 0.1)
    return 0.1


# ── Field Provenance Service ─────────────────────────────────────────────────


class FieldProvenanceService:
    """Tracks per-field value provenance for global entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_field_value(
        self,
        global_entity_id: str,
        field_name: str,
        field_value: str,
        source_row_id: str,
        source_file_id: str,
        evidence_tier: str,
        signal_name: str,
        selection_reason: str = "matched_signal",
    ) -> str:
        """Record a field value with provenance.

        If a current value already exists for (entity, field), supersede it
        if the new value has higher authority.
        """
        now = datetime.now(UTC)
        authority = compute_authority_score(signal_name)
        prov_id = str(uuid.uuid4())

        # Check for existing current value
        existing = await self.session.execute(
            text(
                "SELECT id, authority_score FROM md_field_provenance "
                "WHERE global_entity_id = :entity_id AND field_name = :field_name "
                "AND is_current = true"
            ),
            {"entity_id": global_entity_id, "field_name": field_name},
        )
        existing_row = existing.mappings().first()

        if existing_row and existing_row["authority_score"] >= authority:
            # Existing value is stronger or equal — do not supersede
            # Still record as historical
            await self.session.execute(
                text(
                    "INSERT INTO md_field_provenance "
                    "(id, global_entity_id, field_name, field_value, source_row_id, "
                    "source_file_id, observed_at, evidence_tier, verification_status, "
                    "authority_score, selection_reason, conflict_status, is_current, created_at) "
                    "VALUES (:id, :entity_id, :field, :value, :src_row, :src_file, :now, "
                    ":tier, 'unverified', :authority, :reason, 'superseded', false, :now)"
                ),
                {
                    "id": prov_id,
                    "entity_id": global_entity_id,
                    "field": field_name,
                    "value": field_value,
                    "src_row": source_row_id,
                    "src_file": source_file_id,
                    "now": now,
                    "tier": evidence_tier,
                    "authority": authority,
                    "reason": selection_reason,
                },
            )
            return prov_id

        # Supersede existing current value if present
        if existing_row:
            await self.session.execute(
                text(
                    "UPDATE md_field_provenance SET is_current = false, superseded_at = :now "
                    "WHERE global_entity_id = :entity_id AND field_name = :field_name "
                    "AND is_current = true"
                ),
                {"entity_id": global_entity_id, "field_name": field_name, "now": now},
            )

        # Insert new current value
        await self.session.execute(
            text(
                "INSERT INTO md_field_provenance "
                "(id, global_entity_id, field_name, field_value, source_row_id, "
                "source_file_id, observed_at, evidence_tier, verification_status, "
                "authority_score, selection_reason, conflict_status, is_current, created_at) "
                "VALUES (:id, :entity_id, :field, :value, :src_row, :src_file, :now, "
                ":tier, 'unverified', :authority, :reason, 'none', true, :now)"
            ),
            {
                "id": prov_id,
                "entity_id": global_entity_id,
                "field": field_name,
                "value": field_value,
                "src_row": source_row_id,
                "src_file": source_file_id,
                "now": now,
                "tier": evidence_tier,
                "authority": authority,
                "reason": selection_reason,
            },
        )

        return prov_id

    async def get_field_provenance(
        self,
        global_entity_id: str,
        field_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get provenance history for a field (all values, current + historical)."""
        if field_name:
            result = await self.session.execute(
                text(
                    "SELECT * FROM md_field_provenance "
                    "WHERE global_entity_id = :entity_id AND field_name = :field_name "
                    "ORDER BY is_current DESC, authority_score DESC, observed_at DESC"
                ),
                {"entity_id": global_entity_id, "field_name": field_name},
            )
        else:
            result = await self.session.execute(
                text(
                    "SELECT * FROM md_field_provenance "
                    "WHERE global_entity_id = :entity_id "
                    "ORDER BY field_name, is_current DESC, authority_score DESC"
                ),
                {"entity_id": global_entity_id},
            )
        return [dict(r) for r in result.mappings().all()]

    async def get_current_values(
        self,
        global_entity_id: str,
    ) -> dict[str, str]:
        """Get the current authoritative value for each field on an entity."""
        result = await self.session.execute(
            text(
                "SELECT field_name, field_value, authority_score "
                "FROM md_field_provenance "
                "WHERE global_entity_id = :entity_id AND is_current = true "
                "ORDER BY field_name"
            ),
            {"entity_id": global_entity_id},
        )
        values = {}
        for row in result.mappings().all():
            values[row["field_name"]] = row["field_value"]
        return values

    async def count_conflicting_fields(
        self,
        global_entity_id: str,
    ) -> int:
        """Count fields with unresolved conflicts."""
        result = await self.session.execute(
            text(
                "SELECT COUNT(*) FROM md_field_provenance "
                "WHERE global_entity_id = :entity_id AND conflict_status = 'active'"
            ),
            {"entity_id": global_entity_id},
        )
        return result.scalar() or 0
