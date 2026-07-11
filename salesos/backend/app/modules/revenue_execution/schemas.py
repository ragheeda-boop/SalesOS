from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime, date

class OpportunityCreate(BaseModel):
    company_id: str
    title: str
    estimated_value: Decimal
    confidence: Decimal
    buying_intent: Optional[Decimal] = None
    relationship_strength: Optional[Decimal] = None
    source_action_id: Optional[str] = None

class OpportunityStageUpdate(BaseModel):
    stage: str

class OpportunityResponse(BaseModel):
    id: str
    company_id: Optional[str] = None
    title: str
    stage: str
    estimated_value: Optional[Decimal] = None
    confidence: Optional[Decimal] = None
    win_probability: Optional[Decimal] = None
    source: str
    risk_level: Optional[str] = None
    created_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

class TaskCreate(BaseModel):
    title: str
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    source: str = "manual"
    company_id: Optional[str] = None
    due_date: Optional[date] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    priority: str
    source: str
    company_id: Optional[str] = None
    completed: bool
    created_at: Optional[datetime] = None

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
