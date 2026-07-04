"""KPIRegistry — every metric has a definition, formula, and source.

This is the reference catalog for all Revenue Analytics measurements.
"""

from __future__ import annotations

from .models import KPI, MetricCategory


class KPIRegistry:
    """Central registry for all KPIs. Each KPI has one owner, one formula."""

    _registry: dict[str, KPI] = {}

    @classmethod
    def register(cls, kpi: KPI) -> None:
        cls._registry[kpi.id] = kpi

    @classmethod
    def get(cls, kpi_id: str) -> KPI | None:
        return cls._registry.get(kpi_id)

    @classmethod
    def by_category(cls, category: MetricCategory) -> list[KPI]:
        return [k for k in cls._registry.values() if k.category == category]

    @classmethod
    def all(cls) -> dict[str, KPI]:
        return dict(cls._registry)

    @classmethod
    def load_defaults(cls) -> None:
        cls._registry.clear()
        # ── Revenue ──
        cls.register(KPI(id="booked_revenue", name="Booked Revenue", name_ar="الإيراد المسجل",
                         category=MetricCategory.REVENUE, formula="SUM(quote.grand_total WHERE quote.accepted)",
                         unit="currency", source_domains=["quote"]))
        cls.register(KPI(id="expected_revenue", name="Expected Revenue", name_ar="الإيراد المتوقع",
                         category=MetricCategory.REVENUE, formula="forecast.total_expected_revenue",
                         unit="currency", source_domains=["forecast"]))
        cls.register(KPI(id="revenue_growth", name="Revenue Growth", name_ar="نمو الإيرادات",
                         category=MetricCategory.REVENUE, formula="(current_revenue - previous_revenue) / previous_revenue",
                         unit="percent", source_domains=["quote", "forecast"]))
        cls.register(KPI(id="revenue_variance", name="Revenue Variance", name_ar="تباين الإيرادات",
                         category=MetricCategory.REVENUE, formula="ABS(forecast - actual) / forecast",
                         unit="percent", higher_is_better=False, source_domains=["forecast", "quote"]))

        # ── Pipeline ──
        cls.register(KPI(id="pipeline_coverage", name="Pipeline Coverage", name_ar="تغطية خط المبيعات",
                         category=MetricCategory.PIPELINE, formula="total_pipeline_value / quota",
                         unit="percent", source_domains=["opportunity", "pipeline"]))
        cls.register(KPI(id="pipeline_velocity", name="Pipeline Velocity", name_ar="سرعة خط المبيعات",
                         category=MetricCategory.PIPELINE, formula="AVG(stage_velocity_days)",
                         unit="days", higher_is_better=False, source_domains=["pipeline"]))
        cls.register(KPI(id="stage_conversion", name="Stage Conversion", name_ar="معدل التحويل",
                         category=MetricCategory.PIPELINE, formula="SUM(exited) / SUM(entered)",
                         unit="percent", source_domains=["pipeline"]))
        cls.register(KPI(id="stage_aging", name="Stage Aging", name_ar="تقادم المرحلة",
                         category=MetricCategory.PIPELINE, formula="AVG(days_in_stage > sla_days)",
                         unit="percent", higher_is_better=False, source_domains=["pipeline"]))

        # ── Commercial ──
        cls.register(KPI(id="quote_acceptance", name="Quote Acceptance Rate", name_ar="معدل قبول العروض",
                         category=MetricCategory.COMMERCIAL, formula="accepted_quotes / total_quotes",
                         unit="percent", source_domains=["quote"]))
        cls.register(KPI(id="avg_discount", name="Average Discount", name_ar="متوسط الخصم",
                         category=MetricCategory.COMMERCIAL, formula="AVG(quote.discount_percent)",
                         unit="percent", higher_is_better=False, source_domains=["quote"]))
        cls.register(KPI(id="approval_time", name="Average Approval Time", name_ar="متوسط وقت الاعتماد",
                         category=MetricCategory.COMMERCIAL, formula="AVG(approved_at - submitted_at)",
                         unit="days", higher_is_better=False, source_domains=["quote"]))

        # ── Customer ──
        cls.register(KPI(id="renewal_rate", name="Renewal Rate", name_ar="معدل التجديد",
                         category=MetricCategory.CUSTOMER, formula="renewed_contracts / expiring_contracts",
                         unit="percent", source_domains=["contract"]))
        cls.register(KPI(id="expansion_rate", name="Expansion Rate", name_ar="معدل التوسع",
                         category=MetricCategory.CUSTOMER, formula="expansion_revenue / existing_revenue",
                         unit="percent", source_domains=["contract", "quote"]))

        # ── Forecast ──
        cls.register(KPI(id="forecast_accuracy", name="Forecast Accuracy", name_ar="دقة التوقعات",
                         category=MetricCategory.FORECAST, formula="1 - ABS(forecast - actual) / forecast",
                         unit="percent", source_domains=["forecast", "quote"]))
        cls.register(KPI(id="forecast_bias", name="Forecast Bias", name_ar="انحياز التوقعات",
                         category=MetricCategory.FORECAST, formula="AVG(forecast - actual)",
                         unit="percent", higher_is_better=False, source_domains=["forecast"]))
        cls.register(KPI(id="forecast_stability", name="Forecast Stability", name_ar="استقرار التوقعات",
                         category=MetricCategory.FORECAST, formula="1 - STDDEV(snapshot_deltas)",
                         unit="percent", source_domains=["forecast"]))

        # ── Operational ──
        cls.register(KPI(id="activity_sla", name="Activity SLA Compliance", name_ar="الالتزام بمواعيد النشاطات",
                         category=MetricCategory.OPERATIONAL, formula="activities_on_time / total_activities",
                         unit="percent", source_domains=["activity"]))
        cls.register(KPI(id="rep_productivity", name="Rep Productivity", name_ar="إنتاجية المندوب",
                         category=MetricCategory.OPERATIONAL, formula="total_activities / active_reps",
                         unit="count", source_domains=["activity"]))
