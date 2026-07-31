import strawberry


@strawberry.type
class CompanyType:
    id: str
    name_ar: str
    name_en: str | None = None
    cr_number: str
    status: str
    city: str | None = None
    region: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    activity_description: str | None = None
    activity_code: str | None = None
    industry: str | None = None
    legal_form: str | None = None
    employees_count: int | None = None
    confidence_score: float | None = None
    is_golden_record: bool | None = None
    tags: list[str] | None = None
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
    expected_close_date: str | None = None
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
    stage_velocity: list[str] | None = None


@strawberry.type
class SearchResultItemType:
    id: str
    name_ar: str
    name_en: str | None = None
    cr_number: str
    city: str | None = None
    confidence_score: float | None = None


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
    stage: str | None = None
    status: str | None = None
    company_id: str | None = None
    owner_id: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    limit: int = 20
    offset: int = 0


@strawberry.input
class CompanyUpdateInput:
    name_ar: str | None = None
    name_en: str | None = None
    status: str | None = None
    city: str | None = None
    region: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    activity_description: str | None = None
    tags: list[str] | None = None


@strawberry.input
class CreateOpportunityInput:
    company_id: str
    name: str
    value: float = 0.0
    currency: str = "SAR"
    expected_close_date: str | None = None
    owner_id: str = ""
    description: str = ""
