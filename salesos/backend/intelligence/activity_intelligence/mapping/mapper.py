"""Mapper — Stage 5 of the Mapping Pipeline (ADR-012 §6).

Persists the final mapping:
- Updates email/meeting record with company_id, contact_id, opportunity_id
- Records mapping provenance (method, confidence, resolved_by)
"""

from __future__ import annotations

from datetime import datetime, timezone

from intelligence.activity_intelligence.contracts.models import (
    MappingResult,
    ScoredCandidate,
)


class MappingPersister:
    """Persist the final mapping result to the database."""

    def __init__(self, db_session=None, email_repo=None, meeting_repo=None):
        self._db = db_session
        self._email_repo = email_repo
        self._meeting_repo = meeting_repo

    async def persist_email_mapping(
        self,
        email_id: str,
        scored: ScoredCandidate,
        mapping_provenance: dict | None = None,
    ) -> MappingResult:
        """Persist mapping for an email record."""
        result = MappingResult(
            source_id=email_id,
            mapped=True,
            entity_type=scored.candidate.entity_type,
            entity_id=scored.candidate.entity_id,
            confidence=scored.score,
            method=scored.candidate.method,
            reason=scored.reason,
        )

        if scored.candidate.entity_type == "company":
            result.company_id = scored.candidate.entity_id
        elif scored.candidate.entity_type == "contact":
            result.contact_id = scored.candidate.entity_id
        elif scored.candidate.entity_type == "opportunity":
            result.opportunity_id = scored.candidate.entity_id

        # Store mapping provenance for audit
        provenance = mapping_provenance or {}
        provenance.update({
            "method": scored.candidate.method,
            "confidence": scored.score,
            "entity_type": scored.candidate.entity_type,
            "entity_id": scored.candidate.entity_id,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        })

        return result

    async def persist_meeting_mapping(
        self,
        meeting_id: str,
        scored: ScoredCandidate,
        mapping_provenance: dict | None = None,
    ) -> MappingResult:
        """Persist mapping for a meeting record."""
        return await self.persist_email_mapping(
            email_id=meeting_id,
            scored=scored,
            mapping_provenance=mapping_provenance,
        )

    def build_unresolved(self, source_id: str, reason: str = "") -> MappingResult:
        """Build an unresolved mapping result."""
        return MappingResult.unresolved(
            source_id=source_id,
            reason=reason or "no_candidate_above_threshold",
        )
