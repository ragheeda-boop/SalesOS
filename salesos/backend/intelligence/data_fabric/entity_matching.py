from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..business_objects import EntityType


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


class EntityMatcher:
    """
    Links related entities: companies, people, emails, phones into unified graph.
    Discovers relationships that are not explicitly defined.
    """

    def __init__(self):
        self._matches: list[MatchResult] = []

    def match(self, source_type: EntityType, source_data: dict[str, Any],
              target_type: EntityType, target_data: dict[str, Any]) -> Optional[MatchResult]:
        """Try to match two entities."""
        matched_fields = []
        confidence_sum = 0.0
        checks = 0

        for field in ["email", "phone", "domain", "cr_number", "vat_number"]:
            sv = source_data.get(field)
            tv = target_data.get(field)
            if sv and tv:
                checks += 1
                if sv.lower() == tv.lower():
                    matched_fields.append(field)
                    confidence_sum += self._field_weight(field)

        if source_data.get("name") and target_data.get("name"):
            checks += 1
            sn = source_data["name"].lower().replace(" co", "").replace(" ltd", "").strip()
            tn = target_data["name"].lower().replace(" co", "").replace(" ltd", "").strip()
            if sn == tn or sn in tn or tn in sn:
                matched_fields.append("name")
                confidence_sum += 0.7

        if not matched_fields:
            return None

        confidence = confidence_sum / max(checks, 1)
        if confidence < 0.3:
            return None

        result = MatchResult(
            source_id=source_data.get("id", ""),
            target_id=target_data.get("id", ""),
            source_entity=source_type.value,
            target_entity=target_type.value,
            confidence=round(confidence, 2),
            match_type="exact" if confidence > 0.85 else "fuzzy",
            matched_fields=matched_fields,
        )
        self._matches.append(result)
        return result

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

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_matches": len(self._matches),
            "exact_matches": sum(1 for m in self._matches if m.match_type == "exact"),
            "fuzzy_matches": sum(1 for m in self._matches if m.match_type == "fuzzy"),
            "avg_confidence": round(
                sum(m.confidence for m in self._matches) / max(len(self._matches), 1), 2
            ),
        }
