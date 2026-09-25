from pydantic import BaseModel, Field


class RevenueByCurrency(BaseModel):
    currency: str
    total_booked: float = 0.0
    total_pipeline: float = 0.0
    weighted_pipeline: float = 0.0
    forecast: float = 0.0
    growth_percent: float = 0.0


class RevenueKPI(BaseModel):
    total_booked: float | None = 0.0
    total_pipeline: float | None = 0.0
    weighted_pipeline: float | None = 0.0
    forecast: float | None = 0.0
    growth_percent: float | None = 0.0
    currency_consistent: bool = True
    by_currency: list[RevenueByCurrency] = Field(default_factory=list)


class TeamKPI(BaseModel):
    total_employees: int = 0
    active_employees: int = 0
    top_performers: list[dict] = []
    avg_win_rate: float = 0.0


class RiskKPI(BaseModel):
    expiring_contracts: int = 0
    stalled_deals: int = 0
    inactive_companies: int = 0
    low_pipeline_employees: int = 0


class HealthKPI(BaseModel):
    overall_health: str = "good"
    data_completeness: float = 0.0
    sync_status: str = "synced"
    last_activity: str = ""


class PipelineHealth(BaseModel):
    total_deals: int = 0
    total_value: float | None = 0.0
    won_deals: int = 0
    lost_deals: int = 0
    win_rate: float = 0.0
    avg_deal_size: float | None = 0.0
    by_currency: list[dict] = Field(default_factory=list)
    by_stage: list[dict] = []


class RenewalKPI(BaseModel):
    due_next_30_days: int = 0
    due_next_90_days: int = 0
    total_renewal_value: float = 0.0
    at_risk: list[dict] = []


class GrowthKPI(BaseModel):
    new_companies_30d: int = 0
    new_contacts_30d: int = 0
    new_opportunities_30d: int = 0
    new_contracts_30d: int = 0


class ExecutiveDashboard(BaseModel):
    revenue: RevenueKPI = RevenueKPI()
    team: TeamKPI = TeamKPI()
    risk: RiskKPI = RiskKPI()
    health: HealthKPI = HealthKPI()
    pipeline: PipelineHealth = PipelineHealth()
    renewals: RenewalKPI = RenewalKPI()
    growth: GrowthKPI = GrowthKPI()
