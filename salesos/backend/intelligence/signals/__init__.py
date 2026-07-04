from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from ..business_objects import SignalType


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationCategory(str, Enum):
    NEXT_BEST_ACTION = "next_best_action"
    RISK_MITIGATION = "risk_mitigation"
    OPPORTUNITY = "opportunity"
    FOLLOW_UP = "follow_up"
    MEETING = "meeting"
    RESEARCH = "research"
    OUTREACH = "outreach"


@dataclass
class BuyingSignal:
    id: str
    company_id: str
    signal_type: SignalType
    title: str
    description: Optional[str] = None
    intensity: float = 0.5
    priority: Priority = Priority.MEDIUM
    source: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation:
    id: str
    company_id: str
    category: RecommendationCategory
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    confidence: float = 0.5
    source_signals: list[str] = field(default_factory=list)
    expected_impact: Optional[str] = None
    action_url: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    dismissed: bool = False


class SignalEngine:
    """
    Detects buying signals and generates actionable recommendations.
    Signals → Analysis → Recommendations → Actions
    """

    def __init__(self):
        self._signals: list[BuyingSignal] = []
        self._recommendations: list[Recommendation] = []
        self._signal_weights = {
            SignalType.HIRING: 0.8,
            SignalType.FUNDING: 0.9,
            SignalType.EXPANSION: 0.85,
            SignalType.CONTRACT: 0.7,
            SignalType.PROJECT: 0.75,
            SignalType.NEWS: 0.3,
            SignalType.PARTNERSHIP: 0.6,
            SignalType.MERGER: 0.95,
            SignalType.LEADERSHIP: 0.65,
            SignalType.TENDER: 0.8,
            SignalType.COMPETITOR_MOVE: 0.7,
            SignalType.REGULATORY: 0.5,
        }

    def ingest_signal(self, company_id: str, signal_type: SignalType,
                      title: str, description: Optional[str] = None,
                      source: str = "", intensity: Optional[float] = None,
                      metadata: Optional[dict[str, Any]] = None) -> BuyingSignal:
        """Ingest a new signal and generate recommendations."""
        base_intensity = intensity or self._signal_weights.get(signal_type, 0.5)
        now = datetime.utcnow()

        signal = BuyingSignal(
            id=f"sig_{company_id}_{int(now.timestamp())}_{len(self._signals)}",
            company_id=company_id,
            signal_type=signal_type,
            title=title,
            description=description,
            intensity=min(base_intensity + self._calculate_context_boost(company_id, signal_type), 1.0),
            priority=self._calculate_priority(signal_type, base_intensity),
            source=source,
            detected_at=now,
            expires_at=now + timedelta(days=90),
            metadata=metadata or {},
        )
        self._signals.append(signal)

        recommendations = self._generate_recommendations(signal)
        self._recommendations.extend(recommendations)

        return signal

    def _calculate_context_boost(self, company_id: str, signal_type: SignalType) -> float:
        """Calculate a context-based intensity boost."""
        recent = [s for s in self._signals if s.company_id == company_id
                  and s.detected_at > datetime.utcnow() - timedelta(days=30)]
        related = [s for s in recent if s.signal_type == signal_type]
        return min(len(related) * 0.05, 0.3)

    def _calculate_priority(self, signal_type: SignalType, intensity: float) -> Priority:
        if intensity >= 0.8 or signal_type in (SignalType.MERGER, SignalType.FUNDING):
            return Priority.HIGH
        if intensity >= 0.6 or signal_type in (SignalType.HIRING, SignalType.EXPANSION):
            return Priority.MEDIUM
        return Priority.LOW

    def _generate_recommendations(self, signal: BuyingSignal) -> list[Recommendation]:
        """Generate recommendations from a signal."""
        recs = []
        now = datetime.utcnow()

        signal_recipes = {
            SignalType.HIRING: [
                RecommendationCategory.NEXT_BEST_ACTION,
                RecommendationCategory.RESEARCH,
            ],
            SignalType.FUNDING: [
                RecommendationCategory.OPPORTUNITY,
                RecommendationCategory.OUTREACH,
            ],
            SignalType.EXPANSION: [
                RecommendationCategory.OPPORTUNITY,
                RecommendationCategory.MEETING,
            ],
            SignalType.TENDER: [
                RecommendationCategory.FOLLOW_UP,
                RecommendationCategory.OUTREACH,
            ],
            SignalType.LEADERSHIP: [
                RecommendationCategory.RESEARCH,
                RecommendationCategory.OUTREACH,
            ],
            SignalType.MERGER: [
                RecommendationCategory.RISK_MITIGATION,
                RecommendationCategory.RESEARCH,
            ],
        }

        category_actions = {
            RecommendationCategory.NEXT_BEST_ACTION: (
                "متابعة فورية", f"التواصل مع الشركة بناءً على إشارة {signal.signal_type.value}"
            ),
            RecommendationCategory.RISK_MITIGATION: (
                "تقييم المخاطر", f"مراجعة تأثير {signal.signal_type.value} على العلاقة"
            ),
            RecommendationCategory.OPPORTUNITY: (
                "استغلال الفرصة", f"{signal.title} - فرصة جديدة للتوسع"
            ),
            RecommendationCategory.FOLLOW_UP: (
                "متابعة", f"متابعة {signal.title}"
            ),
            RecommendationCategory.MEETING: (
                "جدولة اجتماع", f"ترتيب اجتماع لمناقشة {signal.title}"
            ),
            RecommendationCategory.RESEARCH: (
                "بحث", f"البحث عن معلومات إضافية حول {signal.title}"
            ),
            RecommendationCategory.OUTREACH: (
                "تواصل", f"التواصل مع صانع القرار"
            ),
        }

        for category in signal_recipes.get(signal.signal_type, [RecommendationCategory.NEXT_BEST_ACTION]):
            action_label, action_desc = category_actions.get(category, ("متابعة", signal.title))
            rec = Recommendation(
                id=f"rec_{signal.id}_{category.value}",
                company_id=signal.company_id,
                category=category,
                title=action_label,
                description=action_desc,
                priority=signal.priority,
                confidence=signal.intensity,
                source_signals=[signal.id],
                expected_impact=self._estimate_impact(category, signal.intensity),
                generated_at=now,
            )
            recs.append(rec)

        return recs

    def _estimate_impact(self, category: RecommendationCategory, intensity: float) -> str:
        if intensity >= 0.8:
            return "تأثير عالي على الإيرادات"
        if intensity >= 0.6:
            return "فرصة جيدة للتوسع"
        return "معلومة استخباراتية"

    def get_signals(self, company_id: Optional[str] = None,
                    priority: Optional[Priority] = None,
                    days_back: int = 30) -> list[BuyingSignal]:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        results = [s for s in self._signals if s.detected_at >= cutoff]

        if company_id:
            results = [s for s in results if s.company_id == company_id]
        if priority:
            results = [s for s in results if s.priority == priority]

        return sorted(results, key=lambda s: (s.priority.value, s.intensity), reverse=True)

    def get_recommendations(self, company_id: Optional[str] = None,
                            category: Optional[RecommendationCategory] = None,
                            active_only: bool = True) -> list[Recommendation]:
        results = self._recommendations
        if company_id:
            results = [r for r in results if r.company_id == company_id]
        if category:
            results = [r for r in results if r.category == category]
        if active_only:
            results = [r for r in results if not r.dismissed]
        return sorted(results, key=lambda r: (r.priority.value, r.confidence), reverse=True)

    def dismiss_recommendation(self, recommendation_id: str) -> bool:
        for rec in self._recommendations:
            if rec.id == recommendation_id:
                rec.dismissed = True
                return True
        return False

    def get_next_best_action(self, company_id: str) -> Optional[Recommendation]:
        recs = self.get_recommendations(company_id, RecommendationCategory.NEXT_BEST_ACTION)
        return recs[0] if recs else None

    def get_hot_companies(self, min_signals: int = 3, days_back: int = 30) -> list[dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        company_signals: dict[str, list[BuyingSignal]] = {}

        for signal in self._signals:
            if signal.detected_at < cutoff:
                continue
            if signal.company_id not in company_signals:
                company_signals[signal.company_id] = []
            company_signals[signal.company_id].append(signal)

        hot = []
        for company_id, signals in company_signals.items():
            if len(signals) >= min_signals:
                hot.append({
                    "company_id": company_id,
                    "signal_count": len(signals),
                    "avg_intensity": round(sum(s.intensity for s in signals) / len(signals), 2),
                    "top_priority": max(s.priority.value for s in signals),
                    "latest_signal": max(s.detected_at for s in signals),
                    "signals": [{"type": s.signal_type.value, "title": s.title} for s in signals[:5]],
                })

        return sorted(hot, key=lambda h: h["signal_count"], reverse=True)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_signals": len(self._signals),
            "total_recommendations": len(self._recommendations),
            "active_recommendations": sum(1 for r in self._recommendations if not r.dismissed),
            "signal_types": list(set(s.signal_type.value for s in self._signals)),
            "hot_companies": len(self.get_hot_companies()),
            "unique_companies": len(set(s.company_id for s in self._signals)),
        }
