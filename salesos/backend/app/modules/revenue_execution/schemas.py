from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    company_id: str
    title: str
    estimated_value: Decimal
    confidence: Decimal
    buying_intent: Decimal | None = None
    relationship_strength: Decimal | None = None
    source_action_id: str | None = None


class OpportunityStageUpdate(BaseModel):
    stage: str


class OpportunityResponse(BaseModel):
    id: str
    company_id: str | None = None
    title: str
    stage: str
    estimated_value: Decimal | None = None
    confidence: Decimal | None = None
    win_probability: Decimal | None = None
    source: str
    risk_level: str | None = None
    created_at: datetime | None = None
    last_activity_at: datetime | None = None


class TaskCreate(BaseModel):
    title: str
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    source: str = "manual"
    company_id: str | None = None
    due_date: date | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    priority: str
    source: str
    company_id: str | None = None
    completed: bool
    created_at: datetime | None = None


class PipelineStage(BaseModel):
    id: str
    label: str
    deals: int
    value: float


class PipelineResponse(BaseModel):
    total_deals: int
    total_value: float
    weighted_value: float
    stages: list[PipelineStage]
