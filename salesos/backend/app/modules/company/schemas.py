from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name_ar: str = Field(..., min_length=1, max_length=500)
    name_en: str | None = None
    cr_number: str = Field(..., min_length=1, max_length=50)
    cr_type: str | None = None
    status: str = "active"
    city: str | None = None
    region: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    activity_description: str | None = None
    activity_code: str | None = None
    legal_form: str | None = None


class CompanyUpdate(BaseModel):
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


class CompanyResponse(BaseModel):
    id: UUID
    name_ar: str
    name_en: str | None
    cr_number: str
    cr_type: str | None
    status: str
    city: str | None
    region: str | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    email: str | None
    website: str | None
    address: str | None
    capital: float | None
    activity_description: str | None
    activity_code: str | None
    industry: str | None
    isic_code: str | None
    isic_description: str | None
    legal_form: str | None
    employees_count: int | None
    incorporation_date: date | None
    expiry_date: date | None
    is_golden_record: bool | None
    confidence_score: float | None
    source_ids: list | None
    tags: list | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyListResponse(BaseModel):
    id: UUID
    name_ar: str
    name_en: str | None
    cr_number: str
    status: str
    city: str | None
    region: str | None
    confidence_score: float | None
    created_at: datetime


class CompanySearchParams(BaseModel):
    q: str | None = None
    cr_number: str | None = None
    status: str | None = None
    city: str | None = None
    region: str | None = None
    activity_code: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"
    cursor: str | None = None


class BranchCreate(BaseModel):
    name_ar: str = Field(..., min_length=1, max_length=500)
    name_en: str | None = None
    branch_number: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None


class BranchResponse(BaseModel):
    id: UUID
    name_ar: str
    name_en: str | None
    branch_number: str | None
    city: str | None
    address: str | None
    phone: str | None
    company_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LicenseCreate(BaseModel):
    license_number: str
    license_type: str
    status: str = "active"
    issuing_authority: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None


class LicenseResponse(BaseModel):
    id: UUID
    license_number: str
    license_type: str
    status: str
    issuing_authority: str | None
    issue_date: date | None
    expiry_date: date | None
    company_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ContactCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    position: str | None = None
    is_primary: bool = False


class ContactResponse(BaseModel):
    id: UUID
    name: str
    email: str | None
    phone: str | None
    mobile: str | None
    position: str | None
    is_primary: bool
    company_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyIngestRequest(BaseModel):
    source: str = Field(..., description="Source slug (e.g., balady, taqeem)")
    data: list[dict] = Field(..., description="Array of company records from source")


class BulkEditRequest(BaseModel):
    company_ids: list[str] = Field(..., min_length=1)
    updates: dict = Field(..., description="Fields to update: industry, size, status, tags")


class BulkEditResponse(BaseModel):
    updated: int
    failed: int
    errors: list[dict]


class BulkDeleteRequest(BaseModel):
    company_ids: list[str] = Field(..., min_length=1)


class BulkDeleteResponse(BaseModel):
    deleted: int


class CompanyOverview(BaseModel):
    total_contacts: int = 0
    total_opportunities: int = 0
    total_revenue: float = 0.0
    active_contracts: int = 0
    pending_tasks: int = 0
    upcoming_meetings: int = 0
    last_activity: str | None = None
    signal_count: int = 0
    contacts_page: int = 1
    contacts_total: int = 0
    opportunities_page: int = 1
    opportunities_total: int = 0
    timeline_page: int = 1
    timeline_total: int = 0


class CompanyOrganization(BaseModel):
    branches: list[BranchResponse] = []
    departments: list[str] = []
    employees_count: int = 0
    legal_form: str | None = None
    incorporation_date: str | None = None


class CompanySignals(BaseModel):
    items: list[dict] = []
    total: int = 0


class CrmDeal(BaseModel):
    id: str
    name: str | None = None
    value: float = 0.0
    stage: str | None = None
    status: str | None = None
    probability: float | None = None
    owner_id: str | None = None
    created_at: str | None = None


class CrmSection(BaseModel):
    deals: list[CrmDeal] = []
    deals_total: int = 0
    deals_value: float = 0.0
    contacts: list[dict] = []
    contacts_total: int = 0
    opportunities: list[dict] = []
    opportunities_total: int = 0


class TimelineSection(BaseModel):
    events: list[dict] = []
    count: int = 0
    page: int = 1
    total: int = 0


class EnrichmentFirmographics(BaseModel):
    industry: str | None = None
    isic_code: str | None = None
    isic_description: str | None = None
    legal_form: str | None = None
    employees_count: int | None = None
    capital: float | None = None
    incorporation_date: str | None = None
    city: str | None = None
    region: str | None = None
    activity_description: str | None = None
    activity_code: str | None = None


class EnrichmentFinancials(BaseModel):
    total_revenue: float = 0.0
    total_opportunity_value: float = 0.0
    active_contracts: int = 0
    pending_invoices: int = 0


class EnrichmentSection(BaseModel):
    firmographics: EnrichmentFirmographics = EnrichmentFirmographics()
    financials: EnrichmentFinancials = EnrichmentFinancials()
    sources: list = []
    is_golden_record: bool = False
    confidence_score: float = 0.0
    last_enriched_at: str | None = None


class EntityResolutionSection(BaseModel):
    is_golden_record: bool = False
    golden_record_id: str | None = None
    confidence_score: float = 0.0
    source_count: int = 0
    duplicates_detected: int = 0
    conflicts_pending: int = 0


class KgRelationship(BaseModel):
    entity_id: str
    entity_name: str | None = None
    relationship_type: str
    strength: float = 0.0
    properties: dict = {}


class KgHierarchy(BaseModel):
    parent_company: dict | None = None
    subsidiaries: list[dict] = []
    level: int = 0


class KnowledgeGraphSection(BaseModel):
    relationships: list[KgRelationship] = []
    hierarchy: KgHierarchy = KgHierarchy()
    competitors: list[dict] = []
    partners: list[dict] = []
    decision_makers: list[dict] = []


class Company360Response(BaseModel):
    company: CompanyResponse
    crm: CrmSection = CrmSection()
    timeline: TimelineSection = TimelineSection()
    enrichment: EnrichmentSection = EnrichmentSection()
    entity_resolution: EntityResolutionSection = EntityResolutionSection()
    knowledge_graph: KnowledgeGraphSection = KnowledgeGraphSection()
    overview: CompanyOverview = CompanyOverview()
    organization: CompanyOrganization = CompanyOrganization()
    contacts: list[dict] = []
    assigned_employees: list[dict] = []
    emails: list[dict] = []
    meetings: list[dict] = []
    tasks: list[dict] = []
    opportunities: list[dict] = []
    contracts: list[dict] = []
    invoices: list[dict] = []
    timeline_legacy: list[dict] = []
    documents: list[dict] = []
    signals: CompanySignals = CompanySignals()
    branches: list[BranchResponse] = []
    licenses: list[LicenseResponse] = []
    contact_count: int = 0
    opportunity_count: int = 0
    total_revenue: float = 0.0
    contacts_page: int = 1
    contacts_total: int = 0
    opportunities_page: int = 1
    opportunities_total: int = 0
    timeline_page: int = 1
    timeline_total: int = 0
    enrichment_legacy: dict = {}
    golden_record_id: str | None = None
    golden_record_data: dict | None = None
    related_entities: list[dict] = []
    decision_makers: list[dict] = []
    health_score: float = 0.0
    engagement: dict | None = None
