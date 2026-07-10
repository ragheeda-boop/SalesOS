from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from ..signals import SignalEngine, Recommendation, RecommendationCategory, Priority, BuyingSignal
from ..graph import RelationshipGraphService
from ..market import MarketIntelligenceEngine
from ..company import CompanyIntelligenceEngine
from ..enrichment import EnrichmentService


class ForecastHorizon(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class DecisionCategory(str, Enum):
    REVENUE = "revenue"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    RESOURCE = "resource"
    STRATEGY = "strategy"


@dataclass
class Forecast:
    horizon: ForecastHorizon
    predicted_revenue: float
    confidence: float
    lower_bound: float
    upper_bound: float
    factors: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutiveDecision:
    id: str
    category: DecisionCategory
    title: str
    description: str
    priority: Priority
    confidence: float
    expected_impact: str
    supporting_signals: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    acted_upon: bool = False


@dataclass
class RevenueInsight:
    title: str
    value: Any
    change: Optional[float] = None
    direction: Optional[str] = None
    confidence: float = 0.5


class RevenueBrain:
    """
    The highest intelligence layer. Analyzes all inputs:
    - Company Intelligence
    - Market Intelligence
    - Relationship Graph
    - Signals & Recommendations
    - Enrichment Data

    Produces: Forecasts, Executive Decisions, Revenue Insights
    """

    def __init__(self, company_engine: CompanyIntelligenceEngine,
                 signal_engine: SignalEngine,
                 market_engine: MarketIntelligenceEngine,
                 graph_service: RelationshipGraphService,
                 enrichment_service: EnrichmentService,
                 db_session_factory: Optional[Callable] = None,
                 feature_store: Any = None):
        self.company_engine = company_engine
        self.signal_engine = signal_engine
        self.market_engine = market_engine
        self.graph_service = graph_service
        self.enrichment_service = enrichment_service
        self._db_session_factory = db_session_factory
        self._feature_store = feature_store
        self._decisions: list[ExecutiveDecision] = []
        self._forecasts: dict[ForecastHorizon, list[Forecast]] = {
            h: [] for h in ForecastHorizon
        }
        self._last_analysis: Optional[datetime] = None

    async def analyze_all(self) -> dict[str, Any]:
        """Run a full analysis across all intelligence layers."""
        now = datetime.utcnow()

        decisions = await self._generate_decisions()
        self._decisions.extend(decisions)

        forecasts = await self._generate_forecasts()
        for h, f in forecasts.items():
            self._forecasts[h].append(f)

        insights = self._compile_insights()

        self._last_analysis = now
        return {
            "decisions": decisions,
            "forecasts": forecasts,
            "insights": insights,
            "analyzed_at": now,
            "company_count": self.company_engine.stats["total_companies"],
            "signal_count": self.signal_engine.stats["total_signals"],
        }

    async def _generate_decisions(self) -> list[ExecutiveDecision]:
        """Generate executive decisions from all intelligence sources."""
        decisions = []
        hot_companies = self.signal_engine.get_hot_companies(min_signals=2)
        top_signals = self.signal_engine.get_signals(priority=Priority.HIGH, days_back=7)
        market_trends = self.market_engine.get_trends(days_back=30)

        if hot_companies:
            decisions.append(ExecutiveDecision(
                id=f"dec_{len(self._decisions)}_hot",
                category=DecisionCategory.OPPORTUNITY,
                title=f"{len(hot_companies)} حساب ساخن يتطلب متابعة فورية",
                description="اكتشاف حسابات ذات نشاط عالي تستدعي تدخل فريق المبيعات",
                priority=Priority.HIGH,
                confidence=0.85,
                expected_impact="فرصة إيرادات عالية",
                supporting_signals=[s["company_id"] for s in hot_companies[:5]],
            ))

        if top_signals:
            decisions.append(ExecutiveDecision(
                id=f"dec_{len(self._decisions)}_signals",
                category=DecisionCategory.REVENUE,
                title=f"{len(top_signals)} إشارة شراء عالية الأولوية",
                description="إشارات شراء تتطلب استجابة سريعة من فريق المبيعات",
                priority=Priority.HIGH,
                confidence=0.8,
                expected_impact="تسريع دورة البيع",
                supporting_signals=[s.id for s in top_signals[:5]],
            ))

        at_risk = [
            ci for ci in self.company_engine.get_all()
            if ci.data_completeness < 30
        ]
        if at_risk:
            decisions.append(ExecutiveDecision(
                id=f"dec_{len(self._decisions)}_risk",
                category=DecisionCategory.RISK,
                title=f"{len(at_risk)} شركة بحاجة لتحديث البيانات",
                description="بيانات غير مكتملة تؤثر على دقة التحليل والتوصيات",
                priority=Priority.MEDIUM,
                confidence=0.9,
                expected_impact="تحسين جودة البيانات",
                supporting_signals=[ci.id for ci in at_risk[:5]],
            ))

        for trend in market_trends[:3]:
            if trend.signal_count >= 5:
                decisions.append(ExecutiveDecision(
                    id=f"dec_{len(self._decisions)}_trend",
                    category=DecisionCategory.STRATEGY,
                    title=f"اتجاه سوقي: {trend.topic} ({trend.signal_count} إشارة)",
                    description=f"مؤشرات {trend.topic} في ازدياد بمعدل {trend.momentum} يومياً",
                    priority=Priority.MEDIUM,
                    confidence=0.7,
                    expected_impact="فرصة استراتيجية",
                ))

        return decisions

    async def _generate_forecasts(self) -> dict[ForecastHorizon, Forecast]:
        """Generate revenue forecasts from signals, FeatureStore, and pipeline data."""
        now = datetime.utcnow()

        recent_signals = self.signal_engine.get_signals(days_back=30)
        hot_companies = self.signal_engine.get_hot_companies(min_signals=1)

        signal_momentum = len(recent_signals) / 30.0 if recent_signals else 0
        hot_momentum = len(hot_companies) / 30.0 if hot_companies else 0

        # Try to get real revenue base from DB + FeatureStore
        base_revenue = 1000000.0
        revenue_companies = 0
        if self._db_session_factory:
            from sqlalchemy import text
            try:
                async with self._db_session_factory() as session:
                    rows = await session.execute(
                        text("SELECT COUNT(*) as cnt, COALESCE(SUM(annual_revenue), 0) as total FROM companies WHERE annual_revenue IS NOT NULL")
                    )
                    r = rows.mappings().one()
                    if r["total"] > 0:
                        base_revenue = float(r["total"])
                        revenue_companies = r["cnt"]
            except Exception:
                pass

        # Use FeatureStore scores to adjust growth factor
        growth_multiplier = 1.0
        if self._feature_store and revenue_companies > 0:
            try:
                for ci in self.company_engine.get_all()[:10]:
                    tenant_id = ci.business_object.profile.data.get("tenant_id", "default")
                    features = await self._feature_store.get_features(company_id=ci.id, tenant_id=tenant_id)
                    if features:
                        growth = features.get("growth_score")
                        if growth and growth.score > 0.6:
                            growth_multiplier += 0.05
            except Exception:
                pass

        signal_factor = 1 + (signal_momentum * 0.02)
        hot_factor = 1 + (hot_momentum * 0.05)
        growth_factor = min(signal_factor * hot_factor * growth_multiplier, 1.5)

        monthly_forecast = base_revenue * growth_factor
        confidence = min(0.5 + (len(recent_signals) * 0.005), 0.9)

        return {
            ForecastHorizon.WEEKLY: Forecast(
                horizon=ForecastHorizon.WEEKLY,
                predicted_revenue=monthly_forecast / 4,
                confidence=confidence,
                lower_bound=monthly_forecast / 5,
                upper_bound=monthly_forecast / 3,
                factors=[
                    f"إشارات: {len(recent_signals)}",
                    f"حسابات ساخنة: {len(hot_companies)}",
                    f"معدل النمو: {((growth_factor - 1) * 100):.0f}%",
                ],
            ),
            ForecastHorizon.MONTHLY: Forecast(
                horizon=ForecastHorizon.MONTHLY,
                predicted_revenue=monthly_forecast,
                confidence=confidence * 0.9,
                lower_bound=monthly_forecast * 0.7,
                upper_bound=monthly_forecast * 1.3,
                factors=[
                    f"إشارات: {len(recent_signals)}",
                    f"حسابات ساخنة: {len(hot_companies)}",
                    f"معدل النمو: {((growth_factor - 1) * 100):.0f}%",
                ],
            ),
            ForecastHorizon.QUARTERLY: Forecast(
                horizon=ForecastHorizon.QUARTERLY,
                predicted_revenue=monthly_forecast * 3,
                confidence=confidence * 0.7,
                lower_bound=monthly_forecast * 1.5,
                upper_bound=monthly_forecast * 4.5,
                factors=[
                    f"اتجاه الإشارات: {signal_momentum:.1f} يومياً",
                    f"زخم الحسابات: {hot_momentum:.1f} يومياً",
                ],
            ),
            ForecastHorizon.YEARLY: Forecast(
                horizon=ForecastHorizon.YEARLY,
                predicted_revenue=monthly_forecast * 12,
                confidence=confidence * 0.5,
                lower_bound=monthly_forecast * 5,
                upper_bound=monthly_forecast * 18,
                factors=[
                    "تقدير سنوي بناءً على البيانات المتاحة",
                    "تخضع للتغيير حسب ظروف السوق",
                ],
            ),
        }

    def _compile_insights(self) -> list[RevenueInsight]:
        """Compile key revenue insights from all data."""
        insights = []
        companies = self.company_engine.get_all()
        signals = self.signal_engine.get_signals(days_back=7)

        insights.append(RevenueInsight(
            title="إجمالي الشركات",
            value=len(companies),
            confidence=1.0,
        ))

        hot = self.signal_engine.get_hot_companies(min_signals=2)
        insights.append(RevenueInsight(
            title="حسابات ساخنة",
            value=len(hot),
            change=len(hot) * 5 if hot else 0,
            direction="up" if hot else "stable",
            confidence=0.85,
        ))

        high_priority = [s for s in signals if s.priority == Priority.HIGH]
        insights.append(RevenueInsight(
            title="إشارات عالية الأولوية",
            value=len(high_priority),
            confidence=0.9,
        ))

        if companies:
            avg_completeness = sum(
                ci.data_completeness for ci in companies
            ) / len(companies)
            insights.append(RevenueInsight(
                title="متوسط اكتمال البيانات",
                value=f"{avg_completeness:.1f}%",
                direction="up" if avg_completeness > 50 else "down",
                confidence=0.95,
            ))

        active_recs = self.signal_engine.get_recommendations()
        insights.append(RevenueInsight(
            title="التوصيات النشطة",
            value=len(active_recs),
            confidence=0.9,
        ))

        return insights

    def get_decisions(self, category: Optional[DecisionCategory] = None,
                      limit: int = 10) -> list[ExecutiveDecision]:
        results = self._decisions
        if category:
            results = [d for d in results if d.category == category]
        return sorted(
            results, key=lambda d: (d.priority.value, d.confidence), reverse=True
        )[:limit]

    def get_forecasts(self, horizon: Optional[ForecastHorizon] = None) -> list[Forecast]:
        if horizon:
            return self._forecasts.get(horizon, [])
        all_forecasts = []
        for h_f in self._forecasts.values():
            all_forecasts.extend(h_f)
        return sorted(all_forecasts, key=lambda f: f.generated_at, reverse=True)

    def get_latest_forecast(self, horizon: ForecastHorizon) -> Optional[Forecast]:
        forecasts = self._forecasts.get(horizon, [])
        return forecasts[-1] if forecasts else None

    def get_revenue_readiness(self) -> dict[str, Any]:
        """Overall revenue readiness score."""
        companies = self.company_engine.get_all()
        signals = self.signal_engine.get_signals(days_back=30)
        hot = self.signal_engine.get_hot_companies(min_signals=2)

        data_score = (
            sum(ci.data_completeness for ci in companies) / max(len(companies), 1)
            if companies else 0
        )
        signal_score = min(len(signals) * 2, 100)
        hot_score = min(len(hot) * 10, 100)
        recommendation_score = min(
            len(self.signal_engine.get_recommendations()) * 5, 100
        )

        overall = round(
            data_score * 0.3 + signal_score * 0.3 + hot_score * 0.2 + recommendation_score * 0.2,
            1
        )

        return {
            "overall_readiness": overall,
            "data_quality": round(data_score, 1),
            "signal_intensity": round(signal_score, 1),
            "hot_accounts": round(hot_score, 1),
            "recommendation_coverage": round(recommendation_score, 1),
            "total_companies": len(companies),
            "total_signals": len(signals),
            "hot_companies": len(hot),
            "analysis_timestamp": self._last_analysis,
        }

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_decisions": len(self._decisions),
            "decisions_by_category": {
                cat.value: sum(1 for d in self._decisions if d.category == cat)
                for cat in DecisionCategory
            },
            "forecasts_generated": sum(len(f) for f in self._forecasts.values()),
            "last_analysis": self._last_analysis,
            "revenue_readiness": self.get_revenue_readiness()["overall_readiness"],
        }
