from datetime import datetime
from pydantic import BaseModel

from app.application.dashboard.dto.widget_contract import DashboardWidget


class MissionCenterData(BaseModel):
    companiesTracked: int = 0
    activeDeals: int = 0
    pipelineValue: float = 0.0
    signalsToday: int = 0
    decisionsPending: int = 0


class DecisionItem(BaseModel):
    id: str
    companyId: str
    companyName: str
    type: str  # 'opportunity' | 'risk' | 'recommendation'
    title: str
    priority: str  # 'high' | 'medium' | 'low'
    dueBy: str | None = None
    score: float = 0.0


class DecisionQueueData(BaseModel):
    items: list[DecisionItem] = []
    total: int = 0


class SignalItem(BaseModel):
    id: str
    companyId: str
    companyName: str
    category: str  # 'tender' | 'regulatory' | 'competitor' | 'financial' | 'news'
    title: str
    summary: str
    severity: str  # 'low' | 'medium' | 'high' | 'critical'
    source: str
    timestamp: str
    isUnseen: bool = True


class IntelligenceFeedData(BaseModel):
    items: list[SignalItem] = []
    total: int = 0
    unseenCount: int = 0


class AIBriefData(BaseModel):
    summary: str = ""
    highlights: list[str] = []
    generatedAt: str = ""


class MarketTrend(BaseModel):
    name: str
    direction: str  # 'up' | 'down' | 'stable'
    change: float = 0.0
    description: str = ""


class CompanyMover(BaseModel):
    companyId: str
    companyName: str
    scoreChange: float = 0.0
    reason: str = ""


class MarketPulseData(BaseModel):
    trends: list[MarketTrend] = []
    topMovers: list[CompanyMover] = []


class ActivityItem(BaseModel):
    id: str
    type: str  # 'signal' | 'decision' | 'update' | 'note'
    title: str
    companyId: str | None = None
    companyName: str | None = None
    timestamp: str


class RecentActivityData(BaseModel):
    items: list[ActivityItem] = []
    total: int = 0


class DashboardDTO(BaseModel):
    generatedAt: datetime | None = None
    period: str = "today"
    totalTracked: int = 0

    missionCenter: DashboardWidget | None = None
    decisionQueue: DashboardWidget | None = None
    intelligenceFeed: DashboardWidget | None = None
    aiBrief: DashboardWidget | None = None
    marketPulse: DashboardWidget | None = None
    recentActivity: DashboardWidget | None = None

    scoredDecisions: list[dict] = []
    overallHealth: float = 1.0
