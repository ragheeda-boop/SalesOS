from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class FreshnessGrade(str, Enum):
    REAL_TIME = "real_time"
    FRESH = "fresh"
    MODERATE = "moderate"
    STALE = "stale"
    EXPIRED = "expired"


@dataclass
class FreshnessScore:
    grade: FreshnessGrade
    hours_since_update: float
    max_valid_hours: float
    score: float


@dataclass
class QualityScore:
    completeness: float
    accuracy: float
    consistency: float
    freshness: float
    uniqueness: float
    overall: float
    issues: list[str] = field(default_factory=list)


@dataclass
class TrustScore:
    score: float
    source_reliability: float
    data_age_factor: float
    cross_reference_count: int
    last_verified: Optional[datetime] = None


FIELD_FRESHNESS: dict[str, float] = {
    "name": 8760,
    "cr_number": 8760,
    "vat_number": 8760,
    "address": 4380,
    "phone": 4380,
    "email": 2160,
    "website": 4380,
    "revenue": 720,
    "employees": 720,
    "status": 720,
    "industry": 2160,
    "description": 4380,
    "logo_url": 8760,
    "social_links": 2160,
}

SOURCE_RELIABILITY: dict[str, float] = {
    "government": 0.95,
    "manual": 0.9,
    "erp": 0.85,
    "crm": 0.8,
    "linkedin": 0.7,
    "website": 0.6,
    "news": 0.5,
    "enrichment_api": 0.4,
    "ai_extraction": 0.3,
    "web_scraper": 0.2,
}


class DataQualityEngine:
    """
    Evaluates and maintains data quality across all sources.
    Completeness, Accuracy, Consistency, Freshness, Uniqueness.
    """

    def __init__(self):
        self._quality_history: dict[str, list[QualityScore]] = {}

    def evaluate(self, entity_id: str, data: dict[str, Any],
                 source: str = "manual") -> QualityScore:
        completeness = self._calc_completeness(data)
        accuracy = self._calc_accuracy(data, source)
        consistency = self._calc_consistency(data)
        freshness = self._calc_freshness(data).score
        uniqueness = self._calc_uniqueness(data)

        issues = self._find_issues(data, completeness, freshness)

        score = QualityScore(
            completeness=round(completeness, 2),
            accuracy=round(accuracy, 2),
            consistency=round(consistency, 2),
            freshness=round(freshness, 2),
            uniqueness=round(uniqueness, 2),
            overall=round(
                completeness * 0.3 + accuracy * 0.25 +
                consistency * 0.15 + freshness * 0.2 + uniqueness * 0.1, 2
            ),
            issues=issues,
        )

        if entity_id not in self._quality_history:
            self._quality_history[entity_id] = []
        self._quality_history[entity_id].append(score)
        return score

    def _calc_completeness(self, data: dict[str, Any]) -> float:
        """How many fields are filled."""
        fields = ["name", "name_en", "cr_number", "vat_number", "email", "phone",
                  "website", "address", "city", "region", "industry", "status",
                  "revenue", "employees"]
        filled = sum(1 for f in fields if data.get(f))
        return filled / len(fields)

    def _calc_accuracy(self, data: dict[str, Any], source: str) -> float:
        """How accurate the data is based on source reliability."""
        base = SOURCE_RELIABILITY.get(source, 0.5)
        corrections = 0.0
        if data.get("email") and "@" in str(data.get("email", "")):
            corrections += 0.1
        if data.get("website") and "." in str(data.get("website", "")):
            corrections += 0.1
        if data.get("phone") and len(str(data.get("phone", ""))) >= 7:
            corrections += 0.1
        return min(base + corrections, 1.0)

    def _calc_consistency(self, data: dict[str, Any]) -> float:
        """Internal consistency of data."""
        checks = 0
        passed = 0

        if data.get("email") and data.get("domain"):
            checks += 1
            if str(data["email"]).split("@")[-1] == str(data["domain"]):
                passed += 1

        if data.get("city") and data.get("region"):
            checks += 1
            passed += 1

        if data.get("revenue") and data.get("employees"):
            checks += 1
            rev = float(data["revenue"]) if data["revenue"] else 0
            emp = int(data["employees"]) if data["employees"] else 0
            if rev > 0 and emp > 0:
                if (rev / emp) > 10000:
                    passed += 1
                else:
                    passed += 0.5

        return passed / max(checks, 1)

    def _calc_freshness(self, data: dict[str, Any]) -> FreshnessScore:
        """How fresh the data is."""
        updated_at = data.get("updated_at")
        if not updated_at:
            return FreshnessScore(FreshnessGrade.STALE, 9999, 720, 0.2)

        try:
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            hours = (datetime.utcnow() - updated_at).total_seconds() / 3600
        except (ValueError, TypeError):
            return FreshnessScore(FreshnessGrade.STALE, 9999, 720, 0.2)

        max_hours = 720

        if hours <= 1:
            return FreshnessScore(FreshnessGrade.REAL_TIME, hours, max_hours, 1.0)
        elif hours <= 24:
            return FreshnessScore(FreshnessGrade.FRESH, hours, max_hours, 0.9)
        elif hours <= 168:
            return FreshnessScore(FreshnessGrade.MODERATE, hours, max_hours, 0.6)
        elif hours <= 720:
            return FreshnessScore(FreshnessGrade.STALE, hours, max_hours, 0.3)
        else:
            return FreshnessScore(FreshnessGrade.EXPIRED, hours, max_hours, 0.1)

    def _calc_uniqueness(self, data: dict[str, Any]) -> float:
        """How unique the data is (avoids duplicates)."""
        fields = ["name", "cr_number", "email", "phone"]
        unique = 0
        for f in fields:
            if data.get(f):
                unique += 1
        return unique / len(fields)

    def _find_issues(self, data: dict[str, Any],
                     completeness: float,
                     freshness_score: FreshnessScore) -> list[str]:
        issues = []
        if completeness < 0.5:
            issues.append("بيانات غير مكتملة - ناقص أكثر من 50% من الحقول")
        if freshness_score.grade in (FreshnessGrade.STALE, FreshnessGrade.EXPIRED):
            issues.append("البيانات قديمة - آخر تحديث منذ أكثر من 30 يوماً")
        if not data.get("email"):
            issues.append("البريد الإلكتروني مفقود")
        if not data.get("phone"):
            issues.append("رقم الهاتف مفقود")
        if str(data.get("email", "")).count("@") != 1:
            issues.append("البريد الإلكتروني غير صالح")
        return issues

    def calculate_trust(self, entity_id: str, source: str,
                        cross_references: int = 0) -> TrustScore:
        reliability = SOURCE_RELIABILITY.get(source, 0.5)
        age_factor = 0.8
        cross_factor = min(cross_references * 0.1, 0.2)

        score = reliability * 0.5 + age_factor * 0.3 + cross_factor * 0.2
        return TrustScore(
            score=round(score, 2),
            source_reliability=reliability,
            data_age_factor=age_factor,
            cross_reference_count=cross_references,
            last_verified=datetime.utcnow(),
        )

    def get_quality_trend(self, entity_id: str) -> list[QualityScore]:
        return self._quality_history.get(entity_id, [])

    @property
    def stats(self) -> dict[str, Any]:
        all_scores = []
        for scores in self._quality_history.values():
            all_scores.extend(scores)
        return {
            "total_evaluations": len(all_scores),
            "avg_overall": round(
                sum(s.overall for s in all_scores) / max(len(all_scores), 1), 2
            ),
            "avg_completeness": round(
                sum(s.completeness for s in all_scores) / max(len(all_scores), 1), 2
            ),
        }
