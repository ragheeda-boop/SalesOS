from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..business_objects import EntityType


@dataclass
class IdentityFragment:
    """A partial identity from a single source."""
    source: str
    name: Optional[str] = None
    name_en: Optional[str] = None
    email: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    cr_number: Optional[str] = None
    vat_number: Optional[str] = None
    duns_number: Optional[str] = None
    external_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedIdentity:
    """A resolved unique identity after merging fragments."""
    id: str
    entity_type: EntityType
    canonical_name: str
    fragments: list[IdentityFragment] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    confidence: float = 0.0
    resolved_at: datetime = field(default_factory=datetime.utcnow)
    matched_by: list[str] = field(default_factory=list)


class IdentityResolver:
    """
    Resolves identities across sources.
    ABC Co, ABC Construction, ABC Ltd → same company.
    Uses multiple matching strategies.
    """

    def __init__(self):
        self._resolved: dict[str, ResolvedIdentity] = {}

    def resolve(self, fragment: IdentityFragment) -> ResolvedIdentity:
        """
        Try to resolve a fragment to an existing identity.
        Returns existing match or creates new.
        """
        candidates = self._find_candidates(fragment)
        if candidates:
            best = candidates[0]
            best.fragments.append(fragment)
            best.aliases.append(fragment.name or "")
            best.confidence = self._calculate_confidence(best)
            return best

        new_id = ResolvedIdentity(
            id=f"rid_{len(self._resolved)}",
            entity_type=self._infer_type(fragment),
            canonical_name=fragment.name or fragment.name_en or "Unknown",
            fragments=[fragment],
            aliases=[fragment.name or ""],
            confidence=0.3,
        )
        self._resolved[new_id.id] = new_id
        return new_id

    def _find_candidates(self, fragment: IdentityFragment) -> list[ResolvedIdentity]:
        """Find matching resolved identities."""
        candidates = []

        for identity in self._resolved.values():
            score = self._match_score(identity, fragment)
            if score >= 0.6:
                identity.matched_by.append(f"score_{score:.2f}")
                candidates.append((identity, score))

        return [c for c, _ in sorted(candidates, key=lambda x: x[1], reverse=True)]

    def _match_score(self, identity: ResolvedIdentity,
                     fragment: IdentityFragment) -> float:
        """Calculate match score between resolved identity and fragment."""
        scores = []

        for existing in identity.fragments:
            # CR number match (exact)
            if fragment.cr_number and existing.cr_number == fragment.cr_number:
                scores.append(1.0)
            if fragment.vat_number and existing.vat_number == fragment.vat_number:
                scores.append(0.95)
            if fragment.duns_number and existing.duns_number == fragment.duns_number:
                scores.append(0.95)

            # Domain match
            if fragment.domain and existing.domain:
                if fragment.domain == existing.domain:
                    scores.append(0.9)
                elif fragment.domain.split(".")[0] == existing.domain.split(".")[0]:
                    scores.append(0.6)

            # Name fuzzy match
            if fragment.name and existing.name:
                if fragment.name == existing.name:
                    scores.append(0.8)
                elif self._fuzzy_match(fragment.name, existing.name):
                    scores.append(0.5)

            # Email domain match
            if fragment.email and existing.email:
                if fragment.email.split("@")[-1] == existing.email.split("@")[-1]:
                    scores.append(0.7)

            # Phone match
            if fragment.phone and existing.phone:
                if fragment.phone[-8:] == existing.phone[-8:]:
                    scores.append(0.85)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _fuzzy_match(self, a: str, b: str) -> bool:
        """Simple fuzzy name matching."""
        a_clean = a.lower().replace(" co", "").replace(" ltd", "").replace(" inc", "").replace(" llc", "").replace("شركة ", "").strip()
        b_clean = b.lower().replace(" co", "").replace(" ltd", "").replace(" inc", "").replace(" llc", "").replace("شركة ", "").strip()
        return a_clean == b_clean or a_clean in b_clean or b_clean in a_clean

    def _infer_type(self, fragment: IdentityFragment) -> EntityType:
        """Infer entity type from fragment data."""
        if fragment.cr_number or fragment.vat_number or fragment.duns_number:
            return EntityType.COMPANY
        if fragment.email:
            return EntityType.CONTACT
        return EntityType.COMPANY

    def _calculate_confidence(self, identity: ResolvedIdentity) -> float:
        """Calculate overall confidence score."""
        if not identity.fragments:
            return 0.0
        source_count = len(set(f.source for f in identity.fragments))
        fragment_count = len(identity.fragments)
        return min(0.3 + (source_count * 0.15) + (fragment_count * 0.05), 0.99)

    def get_resolved(self, identity_id: str) -> Optional[ResolvedIdentity]:
        return self._resolved.get(identity_id)

    def search(self, query: str) -> list[ResolvedIdentity]:
        q = query.lower()
        return [
            identity for identity in self._resolved.values()
            if q in identity.canonical_name.lower()
            or any(q in a.lower() for a in identity.aliases if a)
        ]

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_resolved": len(self._resolved),
            "avg_confidence": round(
                sum(i.confidence for i in self._resolved.values()) / max(len(self._resolved), 1), 2
            ),
            "total_fragments": sum(
                len(i.fragments) for i in self._resolved.values()
            ),
        }
