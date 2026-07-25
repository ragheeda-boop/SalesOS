"""Matcher — Stage 3 of the Mapping Pipeline (ADR-012 §6).

Matches resolved entities against CRM records using a priority chain:
  1. ExplicitCRMRef    — direct company_id on the record
  2. OpportunityLookup — via opportunity_id → company_id
  3. ContactLookup     — via sender email → contact → company
  4. DomainMatch       — normalized domain → company website/email domain
  5. AIMatch           — AI fuzzy match on name + domain + context
"""

from __future__ import annotations

from intelligence.activity_intelligence.contracts.models import CandidateMatch, ResolvedEntities


class CRMMatcher:
    """Matches resolved entities against CRM records using priority chain."""

    def __init__(
        self,
        company_reader=None,
        contact_reader=None,
        opportunity_reader=None,
    ):
        self._company_reader = company_reader
        self._contact_reader = contact_reader
        self._opportunity_reader = opportunity_reader

    async def match(
        self,
        entities: ResolvedEntities,
        tenant_id: str,
        priority_chain: bool = True,
    ) -> list[CandidateMatch]:
        """Match resolved entities against CRM.

        Returns candidates sorted by method priority (highest first).
        """
        candidates: list[CandidateMatch] = []

        if priority_chain:
            # Try each method in priority order, stop on first match
            for method_fn in [
                self._match_explicit,
                self._match_opportunity,
                self._match_contact,
                self._match_domain,
            ]:
                result = await method_fn(entities, tenant_id)
                if result:
                    candidates.append(result)
                    return candidates
            # Fallback to AI match only if no other match
            result = await self._match_ai(entities, tenant_id)
            if result:
                candidates.append(result)
        else:
            # Collect all candidates
            for method_fn in [
                self._match_explicit,
                self._match_opportunity,
                self._match_contact,
                self._match_domain,
                self._match_ai,
            ]:
                result = await method_fn(entities, tenant_id)
                if result:
                    candidates.append(result)

        return candidates

    async def _match_explicit(
        self, entities: ResolvedEntities, tenant_id: str
    ) -> CandidateMatch | None:
        """Match by explicit CRM reference (company_id on the record)."""
        # This is handled upstream — if the communication already has company_id,
        # the pipeline skips matching. This method handles explicit IDs in subjects/headers.
        if entities.opportunity_hint and self._opportunity_reader:
            return CandidateMatch(
                entity_id=entities.opportunity_hint,
                entity_type="opportunity",
                method="explicit_ref",
                confidence=1.0,
                reason=f"Explicit opportunity reference: {entities.opportunity_hint}",
            )
        return None

    async def _match_opportunity(
        self, entities: ResolvedEntities, tenant_id: str
    ) -> CandidateMatch | None:
        """Match via opportunity ID lookup."""
        if entities.opportunity_hint and self._opportunity_reader:
            return CandidateMatch(
                entity_id=entities.opportunity_hint,
                entity_type="opportunity",
                method="opportunity_lookup",
                confidence=0.85,
                reason=f"Matched via opportunity: {entities.opportunity_hint}",
            )
        return None

    async def _match_contact(
        self, entities: ResolvedEntities, tenant_id: str
    ) -> CandidateMatch | None:
        """Match via sender email → contact → company."""
        if entities.person_email and self._contact_reader:
            contacts = await self._contact_reader.search_by_email(
                entities.person_email, tenant_id
            )
            if contacts:
                contact = contacts[0]
                company_id = contact.get("company_id")
                if company_id:
                    return CandidateMatch(
                        entity_id=company_id,
                        entity_type="company",
                        method="contact_lookup",
                        confidence=0.80,
                        reason=f"Matched via contact email: {entities.person_email}",
                    )
        return None

    async def _match_domain(
        self, entities: ResolvedEntities, tenant_id: str
    ) -> CandidateMatch | None:
        """Match via normalized domain → company website/email domain."""
        if entities.domain and self._company_reader:
            companies = await self._company_reader.search_by_domain(
                entities.domain, tenant_id
            )
            if companies:
                company = companies[0]
                return CandidateMatch(
                    entity_id=company.get("id", ""),
                    entity_type="company",
                    method="domain_match",
                    confidence=0.60,
                    reason=f"Matched via domain: {entities.domain}",
                )
        return None

    async def _match_ai(
        self, entities: ResolvedEntities, tenant_id: str
    ) -> CandidateMatch | None:
        """AI fuzzy match on name + domain + context."""
        if entities.company_hint and self._company_reader:
            companies = await self._company_reader.search_by_name(
                entities.company_hint, tenant_id, limit=5
            )
            if companies:
                company = companies[0]
                return CandidateMatch(
                    entity_id=company.get("id", ""),
                    entity_type="company",
                    method="ai_match",
                    confidence=0.40,
                    reason=f"AI fuzzy match: {entities.company_hint} → {company.get('name', '')}",
                )
        return None
