from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..business_objects import EntityType


# ── Arabic normalization map ────────────────────────────────────────

_ARABIC_NORMALIZE_TABLE: dict[int, str] = {
    ord('\u0622'): '\u0627', ord('\u0623'): '\u0627', ord('\u0625'): '\u0627',
    ord('\u0649'): '\u064A', ord('\u0629'): '\u0647', ord('\u0626'): '\u064A',
    ord('\u0624'): '\u0648', ord('\u0671'): '\u0627',
}

_COMMON_MISSPELLINGS: dict[str, str] = {
    "شركه": "شركة", "مؤسسه": "مؤسسة", "مصنعه": "مصنع",
    "مجوعة": "مجموعة", "جده": "جدة", "الرياضه": "الرياض",
}


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
    city: Optional[str] = None
    region: Optional[str] = None
    industry: Optional[str] = None
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
    """Resolves identities across sources with Arabic-aware matching.
    ABC Co, ABC Construction, ABC Ltd → same company.
    Uses multiple matching strategies including Arabic transliteration.

    Enhanced with:
    - Arabic transliteration matching
    - CR number as primary deduplication key
    - Tunable fuzzy thresholds
    - Confidence scoring with multi-signal fusion
    """

    def __init__(
        self,
        fuzzy_threshold: float = 0.6,
        auto_merge_threshold: float = 0.95,
    ):
        self._resolved: dict[str, ResolvedIdentity] = {}
        self._fuzzy_threshold = fuzzy_threshold
        self._auto_merge_threshold = auto_merge_threshold

    def resolve(self, fragment: IdentityFragment) -> ResolvedIdentity:
        """Try to resolve a fragment to an existing identity.
        Returns existing match or creates new.
        """
        candidates = self._find_candidates(fragment)
        if candidates:
            best = candidates[0]
            best.fragments.append(fragment)
            if fragment.name and fragment.name not in best.aliases:
                best.aliases.append(fragment.name)
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
            if score >= self._fuzzy_threshold:
                identity.matched_by.append(f"score_{score:.2f}")
                candidates.append((identity, score))

        return [c for c, _ in sorted(candidates, key=lambda x: x[1], reverse=True)]

    def _match_score(self, identity: ResolvedIdentity,
                     fragment: IdentityFragment) -> float:
        """Calculate match score between resolved identity and fragment.
        Enhanced with Arabic-aware matching.
        """
        scores = []

        for existing in identity.fragments:
            # CR number match (exact — highest priority dedup key)
            if fragment.cr_number and existing.cr_number:
                if fragment.cr_number.strip() == existing.cr_number.strip():
                    scores.append(1.0)

            # VAT Number match
            if fragment.vat_number and existing.vat_number:
                if fragment.vat_number.strip() == existing.vat_number.strip():
                    scores.append(0.95)

            # DUNS Number match
            if fragment.duns_number and existing.duns_number:
                if fragment.duns_number.strip() == existing.duns_number.strip():
                    scores.append(0.95)

            # Domain match
            if fragment.domain and existing.domain:
                if fragment.domain == existing.domain:
                    scores.append(0.9)
                elif fragment.domain.split(".")[0] == existing.domain.split(".")[0]:
                    scores.append(0.6)

            # Name matching — Arabic-aware
            name_score = self._match_names_arabic(fragment, existing)
            if name_score > 0:
                scores.append(name_score)

            # Email domain match
            if fragment.email and existing.email:
                if fragment.email.split("@")[-1] == existing.email.split("@")[-1]:
                    scores.append(0.7)
                if fragment.email.lower() == existing.email.lower():
                    scores.append(0.85)

            # Phone match (last 8 digits)
            if fragment.phone and existing.phone:
                fp = fragment.phone.replace(" ", "").replace("-", "")
                ep = existing.phone.replace(" ", "").replace("-", "")
                if fp[-8:] == ep[-8:]:
                    scores.append(0.85)

            # City match (Arabic-aware)
            if fragment.city and existing.city:
                fc = self._normalize_arabic_name(fragment.city)
                ec = self._normalize_arabic_name(existing.city)
                if fc and ec and fc == ec:
                    scores.append(0.4)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _match_names_arabic(
        self, fragment: IdentityFragment, existing: IdentityFragment
    ) -> float:
        """Match names with Arabic normalization and transliteration."""
        # Arabic name matching
        fn = fragment.name
        en_name = existing.name
        if fn and en_name:
            fn_norm = self._normalize_arabic_name(fn)
            en_norm = self._normalize_arabic_name(en_name)

            if fn_norm == en_norm:
                return 0.85
            if fn_norm in en_norm or en_norm in fn_norm:
                return 0.7
            if self._fuzzy_arabic_match(fn_norm, en_norm):
                return 0.55

        # English name matching
        fn_en = fragment.name_en
        en_en = existing.name_en
        if fn_en and en_en:
            fn_clean = fn_en.lower()
            en_clean = en_en.lower()
            for suffix in [" co", " ltd", " inc", " llc", " corp"]:
                fn_clean = fn_clean.replace(suffix, "")
                en_clean = en_clean.replace(suffix, "")
            if fn_clean == en_clean:
                return 0.85
            if fn_clean in en_clean or en_clean in fn_clean:
                return 0.7

        return 0.0

    def _normalize_arabic_name(self, text: str) -> str:
        """Normalize Arabic name for matching."""
        if not text:
            return ""
        text = text.strip().lower()
        for misspell, correct in _COMMON_MISSPELLINGS.items():
            text = text.replace(misspell, correct)
        text = text.translate(_ARABIC_NORMALIZE_TABLE)
        # Remove company type prefixes
        for prefix in ["شركة ", "مؤسسة ", "مصنع ", "مجموعة "]:
            text = text.replace(prefix, "")
        return text.strip()

    def _fuzzy_arabic_match(self, a: str, b: str) -> bool:
        """Levenshtein-based fuzzy matching."""
        if not a or not b:
            return False
        if abs(len(a) - len(b)) > 3:
            return False
        dist = self._levenshtein(a, b)
        max_len = max(len(a), len(b))
        sim = 1.0 - (dist / max(max_len, 1))
        return sim >= 0.75

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        if not a:
            return len(b)
        if not b:
            return len(a)
        a_len, b_len = len(a), len(b)
        matrix = [[0] * (b_len + 1) for _ in range(a_len + 1)]
        for i in range(a_len + 1):
            matrix[i][0] = i
        for j in range(b_len + 1):
            matrix[0][j] = j
        for i in range(1, a_len + 1):
            for j in range(1, b_len + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + cost,
                )
        return matrix[a_len][b_len]

    def _infer_type(self, fragment: IdentityFragment) -> EntityType:
        if fragment.cr_number or fragment.vat_number or fragment.duns_number:
            return EntityType.COMPANY
        if fragment.email:
            return EntityType.CONTACT
        return EntityType.COMPANY

    def _calculate_confidence(self, identity: ResolvedIdentity) -> float:
        if not identity.fragments:
            return 0.0
        source_count = len(set(f.source for f in identity.fragments))
        fragment_count = len(identity.fragments)
        # Boost for CR number presence
        has_cr = any(f.cr_number for f in identity.fragments)
        cr_boost = 0.1 if has_cr else 0.0
        return min(
            0.3 + (source_count * 0.15) + (fragment_count * 0.05) + cr_boost,
            0.99,
        )

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
            "identities_with_cr": sum(
                1 for i in self._resolved.values()
                if any(f.cr_number for f in i.fragments)
            ),
        }
