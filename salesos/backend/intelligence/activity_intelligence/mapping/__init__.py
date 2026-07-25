"""Mapping Pipeline — 5-stage mapping pipeline (ADR-012 §6).

Stages:
  1. Normalizer  — Clean raw data
  2. Resolver    — Extract entities
  3. Matcher     — Match against CRM
  4. Confidence  — Score matches
  5. Mapper      — Persist mapping
"""

from __future__ import annotations

from intelligence.activity_intelligence.contracts.models import (
    MappingResult,
    RawEmail,
    ScoredCandidate,
)
from intelligence.activity_intelligence.mapping.confidence import ConfidenceScorer
from intelligence.activity_intelligence.mapping.mapper import MappingPersister
from intelligence.activity_intelligence.mapping.matcher import CRMMatcher
from intelligence.activity_intelligence.mapping.normalizer import Normalizer
from intelligence.activity_intelligence.mapping.resolver import EntityResolver


class MappingPipeline:
    """5-stage pipeline: Normalize → Resolve → Match → Score → Persist."""

    def __init__(
        self,
        company_reader=None,
        contact_reader=None,
        opportunity_reader=None,
        threshold: float = 0.5,
    ):
        self.normalizer = Normalizer()
        self.resolver = EntityResolver()
        self.matcher = CRMMatcher(
            company_reader=company_reader,
            contact_reader=contact_reader,
            opportunity_reader=opportunity_reader,
        )
        self.confidence = ConfidenceScorer(threshold=threshold)
        self.mapper = MappingPersister()

    async def resolve_email(
        self, tenant_id: str, raw: RawEmail, email_id: str = ""
    ) -> MappingResult:
        """Run full mapping pipeline on a raw email."""
        # Stage 1: Normalize
        from_addr, _reply_to, _subject = self.normalizer.normalize_email(raw)

        # Stage 2: Resolve entities
        entities = self.resolver.resolve_from_email(raw, from_addr)

        # Stage 3: Match against CRM
        candidates = await self.matcher.match(entities, tenant_id)

        # Stage 4: Score confidence
        scored = self.confidence.score(candidates)

        # Stage 5: Persist if above threshold
        if scored:
            return await self.mapper.persist_email_mapping(
                email_id=email_id or raw.message_id,
                scored=scored,
            )

        return self.mapper.build_unresolved(
            source_id=email_id or raw.message_id,
            reason="no_candidate_above_threshold",
        )

    async def resolve_company_from_email(
        self, tenant_id: str, raw: RawEmail
    ) -> ScoredCandidate | None:
        """Resolve company from email (shorthand for email sync workers)."""
        from_addr, _reply_to, _subject = self.normalizer.normalize_email(raw)
        entities = self.resolver.resolve_from_email(raw, from_addr)
        candidates = await self.matcher.match(entities, tenant_id)
        return self.confidence.score(candidates)

    async def resolve_company_from_event(
        self, tenant_id: str, domain: str
    ) -> ScoredCandidate | None:
        """Resolve company from calendar event domain."""
        entities = self.resolver.resolve_domain(domain)
        candidates = await self.matcher.match(entities, tenant_id)
        return self.confidence.score(candidates)


__all__ = [
    "MappingPipeline",
    "Normalizer",
    "EntityResolver",
    "CRMMatcher",
    "ConfidenceScorer",
    "MappingPersister",
]
