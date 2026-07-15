from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import strawberry


@strawberry.type
class CompanyType:
    id: str
    name_ar: str
    name_en: Optional[str] = None
    cr_number: str
    status: str
    city: Optional[str] = None
    region: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    activity_description: Optional[str] = None
    activity_code: Optional[str] = None
    industry: Optional[str] = None
    legal_form: Optional[str] = None
    employees_count: Optional[int] = None
    confidence_score: Optional[float] = None
    is_golden_record: Optional[bool] = None
    tags: Optional[list[str]] = None
    created_at: str
    updated_at: str


@strawberry.type
class OpportunityType:
    id: str
    company_id: str
    name: str
    stage: str
    value: float
    currency: str
    probability: float
    health: str
    expected_close_date: Optional[str] = None
    owner_id: str
    status: str
    description: str
    created_at: str
    updated_at: str


@strawberry.type
class PipelineSummaryType:
    pipeline_value: float
    weighted_pipeline: float
    win_rate: float
    stage_velocity: Optional[list[str]] = None


@strawberry.type
class SearchResultItemType:
    id: str
    name_ar: str
    name_en: Optional[str] = None
    cr_number: str
    city: Optional[str] = None
    confidence_score: Optional[float] = None


@strawberry.type
class SearchResultType:
    query: str
    total: int
    duration_ms: float
    items: list[SearchResultItemType]


@strawberry.type
class EnrichmentResultType:
    task_id: str
    status: str
    company_id: str


@strawberry.input
class OpportunityFiltersInput:
    stage: Optional[str] = None
    status: Optional[str] = None
    company_id: Optional[str] = None
    owner_id: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    limit: int = 20
    offset: int = 0


@strawberry.input
class CompanyUpdateInput:
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    status: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    activity_description: Optional[str] = None
    tags: Optional[list[str]] = None


@strawberry.input
class CreateOpportunityInput:
    company_id: str
    name: str
    value: float = 0.0
    currency: str = "SAR"
    expected_close_date: Optional[str] = None
    owner_id: str = ""
    description: str = ""
