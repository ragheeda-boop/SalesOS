from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from ..business_objects import EntityType


class MergeStatus(str, Enum):
    """Status of a merge suggestion in the HITL workflow."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_MERGED = "auto_merged"


@dataclass
class MergeSuggestion:
    """A merge suggestion with confidence and workflow status."""
    source_id: str
    target_id: str
    confidence: float
    match_type: str  # "exact", "fuzzy", "transliteration", "cr_match"
    matched_fields: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: MergeStatus = MergeStatus.PENDING
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str = ""

    def approve(self, reviewer: str, notes: str = "") -> None:
        self.status = MergeStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes

    def reject(self, reviewer: str, notes: str = "") -> None:
        self.status = MergeStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "confidence": round(self.confidence, 2),
            "match_type": self.match_type,
            "matched_fields": self.matched_fields,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
        }


@dataclass
class MatchResult:
    source_id: str
    target_id: str
    source_entity: str
    target_entity: str
    confidence: float
    match_type: str
    matched_fields: list[str] = field(default_factory=list)
    matched_at: datetime = field(default_factory=datetime.utcnow)


# ── Arabic transliteration map ──────────────────────────────────────

_ARABIC_ENGLISH_TRANSLITERATIONS: dict[str, list[str]] = {
    "الرياض": ["riyadh", "riyad", "al-riyadh"],
    "جدة": ["jeddah", "jaddah", "jedda", "jeddah"],
    "الدمام": ["dammam", "ad-dammam"],
    "مكة": ["makkah", "mecca", "makkah"],
    "المدينة": ["madinah", "medina", "al-madinah"],
    "شركة": ["sharika", "company", "co", "corp"],
    "مؤسسة": ["muassasa", "foundation", "est"],
    "أرامكو": ["aramco", "aramco"],
    "البنك": ["bank", "albank"],
    "السعودي": ["saudi", "saudia", "al-saudi"],
    "العربي": ["arabi", "arab", "al-arabi"],
    "الدولي": ["international", "intl", "international"],
    "الجديد": ["aljadeed", "new", "al-jadeed"],
    "المتحدة": ["mutahedah", "united", "al-mutahedah"],
    "العالمية": ["alamiyah", "global", "international"],
    "الوطنية": ["watania", "national", "al-watania"],
    "الخليجية": ["khalijiya", "gulf", "al-khalijiya"],
    "المصرية": ["masriya", "egyptian", "al-masriya"],
}

# ── Common Arabic misspellings ──────────────────────────────────────

_COMMON_MISSPELLINGS: dict[str, str] = {
    "شركه": "شركة",
    "مؤسسه": "مؤسسة",
    "مصنعه": "مصنع",
    "مجوعة": "مجموعة",
    "الرياضه": "الرياض",
    "جده": "جدة",
    "الرسيم": "الرسمي",
    "التجاري": "التجاري",
}


class EntityMatcher:
    """Links related entities: companies, people, emails, phones into unified graph.
    Discovers relationships that are not explicitly defined.

    Enhanced with:
    - Arabic transliteration matching
    - CR number as unique identifier for deduplication
    - Tunable fuzzy matching thresholds
    - Confidence scoring for merge suggestions
    - Human-in-the-loop (HITL) approval workflow
    """

    def __init__(
        self,
        fuzzy_threshold: float = 0.3,
        auto_merge_threshold: float = 0.95,
        review_threshold: float = 0.7,
    ):
        self._matches: list[MatchResult] = []
        self._merge_suggestions: list[MergeSuggestion] = []
        self._fuzzy_threshold = fuzzy_threshold
        self._auto_merge_threshold = auto_merge_threshold
        self._review_threshold = review_threshold

    def match(self, source_type: EntityType, source_data: dict[str, Any],
              target_type: EntityType, target_data: dict[str, Any]) -> Optional[MatchResult]:
        """Try to match two entities with enhanced scoring."""
        matched_fields = []
        confidence_sum = 0.0
        checks = 0

        # 1. CR Number match (highest weight — unique identifier)
        sv_cr = source_data.get("cr_number", "").strip()
        tv_cr = target_data.get("cr_number", "").strip()
        if sv_cr and tv_cr:
            checks += 1
            if sv_cr == tv_cr:
                matched_fields.append("cr_number")
                confidence_sum += self._field_weight("cr_number")

        # 2. VAT Number match
        sv_vat = source_data.get("vat_number", "").strip()
        tv_vat = target_data.get("vat_number", "").strip()
        if sv_vat and tv_vat:
            checks += 1
            if sv_vat == tv_vat:
                matched_fields.append("vat_number")
                confidence_sum += self._field_weight("vat_number")

        # 3. Email match
        sv_email = source_data.get("email", "").lower().strip()
        tv_email = target_data.get("email", "").lower().strip()
        if sv_email and tv_email:
            checks += 1
            if sv_email == tv_email:
                matched_fields.append("email")
                confidence_sum += self._field_weight("email")

        # 4. Phone match (last 8 digits)
        sv_phone = source_data.get("phone", "").replace(" ", "").replace("-", "")
        tv_phone = target_data.get("phone", "").replace(" ", "").replace("-", "")
        if sv_phone and tv_phone:
            checks += 1
            if sv_phone[-8:] == tv_phone[-8:]:
                matched_fields.append("phone")
                confidence_sum += self._field_weight("phone")

        # 5. Domain match
        sv_domain = source_data.get("domain", "").lower().strip()
        tv_domain = target_data.get("domain", "").lower().strip()
        if sv_domain and tv_domain:
            checks += 1
            if sv_domain == tv_domain:
                matched_fields.append("domain")
                confidence_sum += self._field_weight("domain")

        # 6. Name matching (Arabic + English + transliteration)
        name_result = self._match_names(source_data, target_data)
        if name_result["matched"]:
            checks += 1
            matched_fields.append(name_result["field"])
            confidence_sum += name_result["score"]

        if not matched_fields:
            return None

        confidence = confidence_sum / max(checks, 1)
        if confidence < self._fuzzy_threshold:
            return None

        result = MatchResult(
            source_id=source_data.get("id", ""),
            target_id=target_data.get("id", ""),
            source_entity=source_type.value,
            target_entity=target_type.value,
            confidence=round(confidence, 2),
            match_type=self._determine_match_type(confidence, matched_fields),
            matched_fields=matched_fields,
        )
        self._matches.append(result)

        # Create merge suggestion
        self._create_merge_suggestion(result)

        return result

    def _match_names(
        self, source: dict[str, Any], target: dict[str, Any]
    ) -> dict[str, Any]:
        """Match names with Arabic transliteration support."""
        result = {"matched": False, "field": "", "score": 0.0}

        # Try Arabic name match
        sn_ar = source.get("name_ar", "")
        tn_ar = target.get("name_ar", "")
        if sn_ar and tn_ar:
            sn_norm = self._normalize_arabic(sn_ar)
            tn_norm = self._normalize_arabic(tn_ar)

            if sn_norm == tn_norm:
                return {"matched": True, "field": "name_ar", "score": 0.8}
            if sn_norm in tn_norm or tn_norm in sn_norm:
                return {"matched": True, "field": "name_ar", "score": 0.65}

            # Transliteration check
            if self._transliteration_match(sn_ar, tn_ar):
                return {"matched": True, "field": "name_ar_transliteration", "score": 0.55}

            # Fuzzy check
            if self._fuzzy_name_match(sn_norm, tn_norm):
                return {"matched": True, "field": "name_ar_fuzzy", "score": 0.5}

        # Try English name match
        sn_en = source.get("name_en", "")
        tn_en = target.get("name_en", "")
        if sn_en and tn_en:
            sn_lower = sn_en.lower().strip()
            tn_lower = tn_en.lower().strip()

            # Clean common suffixes
            for suffix in [" co", " ltd", " inc", " llc", " corp", " company"]:
                sn_lower = sn_lower.replace(suffix, "")
                tn_lower = tn_lower.replace(suffix, "")

            if sn_lower == tn_lower:
                return {"matched": True, "field": "name_en", "score": 0.8}
            if sn_lower in tn_lower or tn_lower in sn_lower:
                return {"matched": True, "field": "name_en", "score": 0.65}

        return result

    def _normalize_arabic(self, text: str) -> str:
        """Normalize Arabic text for matching."""
        if not text:
            return ""
        text = text.strip().lower()
        # Apply common misspelling corrections
        for misspell, correct in _COMMON_MISSPELLINGS.items():
            text = text.replace(misspell, correct)
        # Basic normalization
        text = text.replace("ة", "ه").replace("ى", "ي").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        text = text.replace("ئ", "ي").replace("ؤ", "و")
        return text

    def _transliteration_match(self, ar_name: str, ar_target: str) -> bool:
        """Check if names match via transliteration patterns."""
        ar_norm = self._normalize_arabic(ar_name)
        tgt_norm = self._normalize_arabic(ar_target)

        for arabic, english_variants in _ARABIC_ENGLISH_TRANSLITERATIONS.items():
            arabic_norm = self._normalize_arabic(arabic)
            if arabic_norm in ar_norm:
                for variant in english_variants:
                    if variant.lower() in tgt_norm:
                        return True
        return False

    def _fuzzy_name_match(self, a: str, b: str) -> bool:
        """Levenshtein-based fuzzy matching for Arabic names."""
        if not a or not b:
            return False
        # Quick check: same length within 3 chars
        if abs(len(a) - len(b)) > 3:
            return False
        # Calculate Levenshtein distance
        distance = self._levenshtein(a, b)
        max_len = max(len(a), len(b))
        similarity = 1.0 - (distance / max(max_len, 1))
        return similarity >= 0.75

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        """Calculate Levenshtein edit distance."""
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

    def _determine_match_type(self, confidence: float, fields: list[str]) -> str:
        """Determine match type from confidence and fields."""
        if "cr_number" in fields and confidence > 0.9:
            return "cr_match"
        if confidence > 0.85:
            return "exact"
        if any("transliteration" in f for f in fields):
            return "transliteration"
        return "fuzzy"

    def _create_merge_suggestion(self, match: MatchResult) -> None:
        """Create a merge suggestion for HITL review."""
        suggestion = MergeSuggestion(
            source_id=match.source_id,
            target_id=match.target_id,
            confidence=match.confidence,
            match_type=match.match_type,
            matched_fields=match.matched_fields,
        )

        if match.confidence >= self._auto_merge_threshold:
            suggestion.status = MergeStatus.AUTO_MERGED
        elif match.confidence < self._review_threshold:
            suggestion.status = MergeStatus.REJECTED

        self._merge_suggestions.append(suggestion)

    def batch_match(self, entities_a: list[dict[str, Any]],
                    entities_b: list[dict[str, Any]],
                    source_type: EntityType,
                    target_type: EntityType) -> list[MatchResult]:
        results = []
        for a in entities_a:
            for b in entities_b:
                result = self.match(source_type, a, target_type, b)
                if result:
                    results.append(result)
        return results

    def _field_weight(self, field: str) -> float:
        weights = {
            "cr_number": 1.0,
            "vat_number": 0.95,
            "email": 0.8,
            "phone": 0.7,
            "domain": 0.6,
        }
        return weights.get(field, 0.5)

    def get_matches(self, entity_id: Optional[str] = None) -> list[MatchResult]:
        if entity_id:
            return [
                m for m in self._matches
                if m.source_id == entity_id or m.target_id == entity_id
            ]
        return self._matches

    def get_merge_suggestions(
        self, status: Optional[MergeStatus] = None
    ) -> list[MergeSuggestion]:
        """Get merge suggestions, optionally filtered by status."""
        if status:
            return [s for s in self._merge_suggestions if s.status == status]
        return list(self._merge_suggestions)

    def approve_merge(self, source_id: str, target_id: str, reviewer: str, notes: str = "") -> bool:
        """Approve a merge suggestion (HITL workflow)."""
        for s in self._merge_suggestions:
            if s.source_id == source_id and s.target_id == target_id:
                s.approve(reviewer, notes)
                return True
        return False

    def reject_merge(self, source_id: str, target_id: str, reviewer: str, notes: str = "") -> bool:
        """Reject a merge suggestion (HITL workflow)."""
        for s in self._merge_suggestions:
            if s.source_id == source_id and s.target_id == target_id:
                s.reject(reviewer, notes)
                return True
        return False

    def get_pending_reviews(self) -> list[MergeSuggestion]:
        """Get all merge suggestions pending human review."""
        return [s for s in self._merge_suggestions if s.status == MergeStatus.PENDING]

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_matches": len(self._matches),
            "exact_matches": sum(1 for m in self._matches if m.match_type == "exact"),
            "fuzzy_matches": sum(1 for m in self._matches if m.match_type == "fuzzy"),
            "cr_matches": sum(1 for m in self._matches if m.match_type == "cr_match"),
            "transliteration_matches": sum(
                1 for m in self._matches if m.match_type == "transliteration"
            ),
            "avg_confidence": round(
                sum(m.confidence for m in self._matches) / max(len(self._matches), 1), 2
            ),
            "merge_suggestions": {
                "total": len(self._merge_suggestions),
                "pending": sum(1 for s in self._merge_suggestions if s.status == MergeStatus.PENDING),
                "approved": sum(1 for s in self._merge_suggestions if s.status == MergeStatus.APPROVED),
                "rejected": sum(1 for s in self._merge_suggestions if s.status == MergeStatus.REJECTED),
                "auto_merged": sum(1 for s in self._merge_suggestions if s.status == MergeStatus.AUTO_MERGED),
            },
        }
