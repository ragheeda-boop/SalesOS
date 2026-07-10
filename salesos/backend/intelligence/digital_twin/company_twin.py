from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from ..business_objects import BusinessObject, EntityType
from .twin import DigitalTwin, TwinState, TwinMetrics


@dataclass
class CompanyState:
    """Specialized state for company twins."""
    revenue_trend: str = "stable"
    hiring_activity: str = "low"
    expansion_signals: int = 0
    partnership_count: int = 0
    competitive_threats: int = 0
    relationship_health: float = 0.5
    market_position: str = "unknown"
    risk_score: float = 0.0
    growth_potential: float = 0.5


class CompanyTwin(DigitalTwin):
    """
    Specialized digital twin for companies.
    Adds company-specific intelligence layers.
    """

    def __init__(self, business_object: BusinessObject,
                 db_session_factory: Optional[Callable[[], AsyncSession]] = None,
                 feature_store: Any = None):
        super().__init__(business_object)
        self._db_session_factory = db_session_factory
        self._feature_store = feature_store
        self.company_state = CompanyState()

    def analyze_performance(self) -> dict[str, Any]:
        """Analyze company performance and health."""
        signals = self.business_object.signals
        hiring = sum(1 for s in signals if s.type.value == "hiring")
        funding = sum(1 for s in signals if s.type.value == "funding")
        expansion = sum(1 for s in signals if s.type.value == "expansion")

        self.company_state.hiring_activity = "high" if hiring > 2 else "medium" if hiring > 0 else "low"
        self.company_state.expansion_signals = expansion
        self.company_state.relationship_health = min(0.5 + len(signals) * 0.05, 1.0)

        growth_score = hiring * 10 + funding * 15 + expansion * 12
        self.company_state.growth_potential = min(growth_score / 100, 1.0)

        revenue_signals = sum(1 for s in signals if s.type.value in ("contract", "funding", "expansion"))
        if revenue_signals > 3:
            self.company_state.revenue_trend = "growing"
        elif revenue_signals > 0:
            self.company_state.revenue_trend = "stable"
        else:
            self.company_state.revenue_trend = "declining"

        return {
            "growth_potential": self.company_state.growth_potential,
            "revenue_trend": self.company_state.revenue_trend,
            "relationship_health": self.company_state.relationship_health,
            "hiring_activity": self.company_state.hiring_activity,
            "signals_breakdown": {"hiring": hiring, "funding": funding, "expansion": expansion},
        }

    async def predict_next_quarter(self) -> dict[str, Any]:
        """Predict next quarter performance using signal data + FeatureStore."""
        growth = self.company_state.growth_potential

        # Try to use real FeatureStore scores
        feature_scores = {}
        if self._feature_store:
            try:
                tenant_id = self.business_object.profile.data.get("tenant_id", "default")
                features = await self._feature_store.get_features(
                    company_id=self.business_object.id,
                    tenant_id=tenant_id,
                )
                if features:
                    feature_scores = {k: v.score for k, v in features.items()}
                    growth = feature_scores.get("growth_score", growth)
            except Exception:
                pass

        revenue_change = 0
        if growth > 0.7:
            revenue_change = 15
        elif growth > 0.4:
            revenue_change = 8
        elif growth > 0.2:
            revenue_change = 3
        else:
            revenue_change = -5

        return {
            "predicted_revenue_change_pct": revenue_change,
            "predicted_growth": growth,
            "confidence": round(0.3 + growth * 0.5, 2),
            "feature_scores": feature_scores,
            "key_assumptions": [
                f"معدل النمو: {growth:.0%}",
                f"إشارات توسع: {self.company_state.expansion_signals}",
            ],
        }
