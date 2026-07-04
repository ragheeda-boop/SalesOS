from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from ..digital_twin import TwinEngine, DigitalTwin
from ..revenue_brain import RevenueBrain


class ScenarioType(str, Enum):
    PRICE_CHANGE = "price_change"
    HIRE_IMPACT = "hire_impact"
    MARKET_ENTRY = "market_entry"
    PRODUCT_LAUNCH = "product_launch"
    COMPETITOR_RESPONSE = "competitor_response"
    REVENUE_FORECAST = "revenue_forecast"
    CUSTOM = "custom"


@dataclass
class Scenario:
    id: str
    type: ScenarioType
    title: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScenarioResult:
    scenario_id: str
    predicted_outcomes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    simulated_at: datetime = field(default_factory=datetime.utcnow)


class SimulationEngine:
    """
    What-if analysis engine.
    Answers: What happens if we raise prices 8%? What if we hire 3 sales reps?
    What if we enter the UAE market?
    """

    def __init__(self, revenue_brain: Optional[RevenueBrain] = None,
                 twin_engine: Optional[TwinEngine] = None):
        self.revenue_brain = revenue_brain
        self.twin_engine = twin_engine
        self._scenarios: list[Scenario] = []
        self._results: list[ScenarioResult] = []

    async def simulate(self, scenario: Scenario) -> ScenarioResult:
        """Run a simulation for a given scenario."""
        self._scenarios.append(scenario)

        if scenario.type == ScenarioType.PRICE_CHANGE:
            result = await self._simulate_price_change(scenario)
        elif scenario.type == ScenarioType.HIRE_IMPACT:
            result = await self._simulate_hire_impact(scenario)
        elif scenario.type == ScenarioType.MARKET_ENTRY:
            result = await self._simulate_market_entry(scenario)
        elif scenario.type == ScenarioType.PRODUCT_LAUNCH:
            result = await self._simulate_product_launch(scenario)
        elif scenario.type == ScenarioType.COMPETITOR_RESPONSE:
            result = await self._simulate_competitor_response(scenario)
        elif scenario.type == ScenarioType.REVENUE_FORECAST:
            result = await self._simulate_revenue_forecast(scenario)
        else:
            result = self._simulate_custom(scenario)

        self._results.append(result)
        return result

    async def _simulate_price_change(self, scenario: Scenario) -> ScenarioResult:
        change_pct = scenario.parameters.get("change_pct", 0)
        current_revenue = scenario.parameters.get("current_revenue", 1000000)
        elasticity = scenario.parameters.get("elasticity", 0.3)

        volume_change = change_pct * elasticity * -1
        new_revenue = current_revenue * (1 + change_pct / 100) * (1 + volume_change / 100)
        profit_impact = new_revenue - current_revenue

        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={
                "price_change_pct": change_pct,
                "estimated_volume_change_pct": round(volume_change, 1),
                "current_revenue": current_revenue,
                "projected_revenue": round(new_revenue),
                "revenue_impact": round(profit_impact),
                "revenue_impact_pct": round((profit_impact / current_revenue) * 100, 1),
                "breakeven_required_volume": round(abs(change_pct) / (1 + change_pct / 100), 1),
            },
            confidence=0.65,
            risks=["حساسية العملاء للسعر", "رد فعل المنافسين", "تأثير على العقود طويلة الأجل"],
            recommendations=[
                "اختبار السعر على شريحة صغيرة أولاً",
                "مراقبة معدل التحويل أسبوعياً",
                "تقديم قيمة مضافة تبرر السعر الجديد",
            ],
        )

    async def _simulate_hire_impact(self, scenario: Scenario) -> ScenarioResult:
        hires = scenario.parameters.get("hires", 1)
        role = scenario.parameters.get("role", "sales_rep")
        cost_per_hire = scenario.parameters.get("cost_per_hire", 120000)
        avg_deal_size = scenario.parameters.get("avg_deal_size", 100000)
        ramp_months = scenario.parameters.get("ramp_months", 6)

        total_cost = hires * cost_per_hire
        expected_deals_per_rep = 12 / (ramp_months / 2)
        expected_revenue = hires * expected_deals_per_rep * avg_deal_size

        roi = round(((expected_revenue - total_cost) / total_cost) * 100, 1)

        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={
                "hires": hires,
                "role": role,
                "total_cost": total_cost,
                "expected_annual_revenue": round(expected_revenue),
                "roi_pct": roi,
                "ramp_months": ramp_months,
                "breakeven_months": round(total_cost / (expected_revenue / 12), 1),
            },
            confidence=0.6,
            risks=["صعوبة التوظيف", "فترة تأهيل أطول من متوقع", "دوران الموظفين"],
            recommendations=[
                "توظيف شخصين أولاً وقياس الأداء",
                "برنامج تأهيل مدته 3 أشهر",
                "تحديد مؤشرات أداء واضحة من اليوم الأول",
            ],
        )

    async def _simulate_market_entry(self, scenario: Scenario) -> ScenarioResult:
        market = scenario.parameters.get("market", "UAE")
        entry_cost = scenario.parameters.get("entry_cost", 500000)
        expected_revenue_year1 = scenario.parameters.get("expected_revenue_year1", 300000)
        expected_revenue_year2 = scenario.parameters.get("expected_revenue_year2", 800000)
        expected_revenue_year3 = scenario.parameters.get("expected_revenue_year3", 1500000)

        total_3yr_cost = entry_cost * 3
        total_3yr_revenue = expected_revenue_year1 + expected_revenue_year2 + expected_revenue_year3
        net_3yr = total_3yr_revenue - total_3yr_cost
        roi_3yr = round((net_3yr / total_3yr_cost) * 100, 1)

        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={
                "market": market,
                "entry_cost": entry_cost,
                "revenue_year_1": expected_revenue_year1,
                "revenue_year_2": expected_revenue_year2,
                "revenue_year_3": expected_revenue_year3,
                "total_3yr_revenue": total_3yr_revenue,
                "net_3yr_profit": net_3yr,
                "roi_3yr_pct": roi_3yr,
                "breakeven_quarter": 5 if net_3yr > 0 else "> 12",
            },
            confidence=0.5,
            risks=["مخاطر تنظيمية", "منافسون محليون", "تحديات ثقافية", "تقلبات العملة"],
            recommendations=[
                "دراسة السوق بتعمق قبل الدخول",
                "شريك محلي لتخفيف المخاطر",
                "دخول تدريجي على مرحلتين",
            ],
        )

    async def _simulate_product_launch(self, scenario: Scenario) -> ScenarioResult:
        product = scenario.parameters.get("product_name", "New Product")
        dev_cost = scenario.parameters.get("development_cost", 300000)
        launch_cost = scenario.parameters.get("launch_cost", 100000)
        expected_monthly_revenue = scenario.parameters.get("expected_monthly_revenue", 50000)
        target_market_size = scenario.parameters.get("target_market_size", 5000000)

        total_investment = dev_cost + launch_cost
        monthly_breakeven = round(total_investment / expected_monthly_revenue, 1)

        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={
                "product": product,
                "total_investment": total_investment,
                "expected_monthly_revenue": expected_monthly_revenue,
                "monthly_breakeven": monthly_breakeven,
                "target_market_share_pct": round((expected_monthly_revenue * 12 / target_market_size) * 100, 2),
                "year_1_projection": round(expected_monthly_revenue * 12 - total_investment),
                "year_2_projection": round(expected_monthly_revenue * 12 * 1.3),
            },
            confidence=0.55,
            risks=["تأخير في التطوير", "رفض السوق", "مشاكل تقنية"],
            recommendations=[
                "MVP أولاً ثم التوسع",
                "اختبار مع 5 عملاء قبل الإطلاق",
                "حملة تسويقية مسبقة",
            ],
        )

    async def _simulate_competitor_response(self, scenario: Scenario) -> ScenarioResult:
        competitor_action = scenario.parameters.get("competitor_action", "price_cut")
        expected_impact = scenario.parameters.get("expected_impact", 15)
        current_market_share = scenario.parameters.get("current_market_share", 30)

        projected_share = current_market_share * (1 - expected_impact / 100 * 0.5)

        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={
                "competitor_action": competitor_action,
                "estimated_impact_pct": expected_impact,
                "current_market_share": current_market_share,
                "projected_market_share": round(projected_share, 1),
                "market_share_loss": round(current_market_share - projected_share, 1),
                "urgency_level": "high" if expected_impact > 20 else "medium",
            },
            confidence=0.6,
            risks=["تقليد الاستراتيجية", "حرب أسعار", "تآكل العلامة التجارية"],
            recommendations=[
                "تجنب حرب الأسعار - ركز على القيمة",
                "تسريع برنامج الولاء",
                "تعزيز نقاط التميز التنافسية",
            ],
        )

    async def _simulate_revenue_forecast(self, scenario: Scenario) -> ScenarioResult:
        base_revenue = scenario.parameters.get("base_revenue", 1000000)
        growth_rate = scenario.parameters.get("growth_rate", 15)
        cost_increase = scenario.parameters.get("cost_increase", 5)

        projections = {}
        for year in range(1, 4):
            revenue = base_revenue * (1 + growth_rate / 100) ** year
            costs = base_revenue * 0.7 * (1 + cost_increase / 100) ** year
            profit = revenue - costs
            margin = (profit / revenue) * 100
            projections[f"year_{year}"] = {
                "revenue": round(revenue),
                "costs": round(costs),
                "profit": round(profit),
                "margin_pct": round(margin, 1),
            }

        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={
                "base_revenue": base_revenue,
                "growth_rate": growth_rate,
                "projections": projections,
                "total_3yr_revenue": round(sum(p["revenue"] for p in projections.values())),
                "total_3yr_profit": round(sum(p["profit"] for p in projections.values())),
                "avg_margin": round(sum(p["margin_pct"] for p in projections.values()) / 3, 1),
            },
            confidence=0.6,
            risks=["افتراضات النمو قد تكون متفائلة", "ظروف السوق غير متوقعة"],
            recommendations=[
                "مراجعة الافتراضات شهرياً",
                "سيناريو متحفظ مع نمو 8%",
                "تحديث التوقعات مع البيانات الفعلية",
            ],
        )

    def _simulate_custom(self, scenario: Scenario) -> ScenarioResult:
        return ScenarioResult(
            scenario_id=scenario.id,
            predicted_outcomes={"note": "تم استلام السيناريو المخصص. يحتاج تحليل إضافي."},
            confidence=0.3,
            recommendations=["تحديد معايير القياس", "توفير بيانات تاريخية للتحليل"],
        )

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        for s in self._scenarios:
            if s.id == scenario_id:
                return s
        return None

    def get_result(self, scenario_id: str) -> Optional[ScenarioResult]:
        for r in self._results:
            if r.scenario_id == scenario_id:
                return r
        return None

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_scenarios": len(self._scenarios),
            "total_results": len(self._results),
            "scenario_types": list(set(s.type.value for s in self._scenarios)),
            "avg_confidence": round(
                sum(r.confidence for r in self._results) / max(len(self._results), 1), 2
            ),
        }


class DecisionIntelligence:
    """
    Autonomous decision engine.
    Analyzes scenarios and recommends the best course of action.
    """

    def __init__(self, simulation_engine: SimulationEngine):
        self.simulation_engine = simulation_engine

    async def evaluate_options(self, goal: str, options: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate multiple decision options and recommend the best."""
        results = []
        for option in options:
            scenario = Scenario(
                id=f"opt_{len(self.simulation_engine._scenarios)}",
                type=ScenarioType(option.get("type", ScenarioType.CUSTOM)),
                title=option.get("title", "Option"),
                description=option.get("description", ""),
                parameters=option.get("parameters", {}),
            )
            result = await self.simulation_engine.simulate(scenario)
            results.append({
                "option": option["title"],
                "result": result.predicted_outcomes,
                "confidence": result.confidence,
                "risks": result.risks,
            })

        ranked = sorted(results, key=lambda r: r["confidence"], reverse=True)

        return {
            "goal": goal,
            "options_evaluated": len(options),
            "ranked_options": ranked,
            "recommended": ranked[0]["option"] if ranked else None,
            "recommendation_reason": "أعلى درجة ثقة وأقل مخاطر" if ranked else "",
        }
