from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class EmployeeProfile(BaseModel):
    id: str
    full_name: str
    full_name_ar: Optional[str] = None
    email: str
    role: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    tenant_id: str
    created_at: datetime
    team: list[dict] = []
    manager: Optional[dict] = None


class EmployeePortfolioItem(BaseModel):
    id: str
    name: str
    type: str
    value: float = 0.0
    status: str = ""
    company_id: Optional[str] = None
    company_name: Optional[str] = None


class EmployeePortfolio(BaseModel):
    companies: list[dict] = []
    contacts: list[dict] = []
    pipeline: list[EmployeePortfolioItem] = []
    revenue: float = 0.0
    contracts: list[EmployeePortfolioItem] = []
    projects: list[dict] = []


class CalendarIntelligence(BaseModel):
    today_count: int = 0
    week_count: int = 0
    month_count: int = 0
    total_hours: float = 0.0
    avg_duration_minutes: float = 0.0
    unique_companies_met: int = 0
    upcoming: list[dict] = []


class EmailIntelligence(BaseModel):
    sent: int = 0
    received: int = 0
    replies: int = 0
    avg_response_hours: float = 0.0
    top_contacts: list[dict] = []
    top_companies: list[dict] = []


class ActivityIntelligence(BaseModel):
    meetings: int = 0
    emails: int = 0
    calls: int = 0
    tasks: int = 0
    notes: int = 0
    documents: int = 0
    total: int = 0
    recent: list[dict] = []


class EmployeeKPIs(BaseModel):
    revenue: float = 0.0
    pipeline: float = 0.0
    win_rate: float = 0.0
    response_rate: float = 0.0
    follow_up_rate: float = 0.0
    activities: int = 0
    productivity: float = 0.0
    forecast: float = 0.0


class AICoachAction(BaseModel):
    type: str
    title: str
    description: str
    priority: str = "medium"
    target_id: Optional[str] = None
    target_type: Optional[str] = None


class Employee360Response(BaseModel):
    profile: EmployeeProfile
    portfolio: EmployeePortfolio = EmployeePortfolio()
    calendar_intelligence: CalendarIntelligence = CalendarIntelligence()
    email_intelligence: EmailIntelligence = EmailIntelligence()
    activity_intelligence: ActivityIntelligence = ActivityIntelligence()
    kpis: EmployeeKPIs = EmployeeKPIs()
    ai_coach: list[AICoachAction] = []
