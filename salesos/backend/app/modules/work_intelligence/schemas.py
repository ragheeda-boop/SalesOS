from datetime import datetime
from pydantic import BaseModel


class TimeAllocation(BaseModel):
    meeting_hours: float = 0.0
    email_hours: float = 0.0
    call_hours: float = 0.0
    task_hours: float = 0.0
    focus_hours: float = 0.0
    total_tracked: float = 0.0


class MeetingLoad(BaseModel):
    meetings_today: int = 0
    meetings_this_week: int = 0
    meetings_this_month: int = 0
    avg_meetings_per_day: float = 0.0
    total_meeting_hours_this_week: float = 0.0
    overbooked: bool = False
    recommendation: str = ""


class ActivityScore(BaseModel):
    overall: float = 0.0
    volume: float = 0.0
    variety: float = 0.0
    recency: float = 0.0
    consistency: float = 0.0
    grade: str = ""


class WorkRecommendation(BaseModel):
    type: str
    title: str
    description: str
    priority: str = "medium"
    metric: str = ""


class WorkIntelligenceResponse(BaseModel):
    employee_id: str
    tenant_id: str
    period_days: int = 30
    time_allocation: TimeAllocation = TimeAllocation()
    meeting_load: MeetingLoad = MeetingLoad()
    activity_score: ActivityScore = ActivityScore()
    recommendations: list[WorkRecommendation] = []
    generated_at: datetime = datetime.now()
