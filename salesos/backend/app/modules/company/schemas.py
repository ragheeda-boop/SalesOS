from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


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
    legal_form: str | None
    confidence_score: float | None
    tags: list | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class CompanyIngestRequest(BaseModel):
    source: str = Field(..., description="Source slug (e.g., balady, taqeem)")
    data: list[dict] = Field(..., description="Array of company records from source")


class CompanyOverview(BaseModel):
    total_contacts: int = 0
    total_opportunities: int = 0
    total_revenue: float = 0.0
    active_contracts: int = 0
    pending_tasks: int = 0
    upcoming_meetings: int = 0
    last_activity: str | None = None
    signal_count: int = 0


class CompanyOrganization(BaseModel):
    branches: list[BranchResponse] = []
    departments: list[str] = []
    employees_count: int = 0
    legal_form: str | None = None
    incorporation_date: str | None = None


class CompanySignals(BaseModel):
    items: list[dict] = []
    total: int = 0


class Company360Response(BaseModel):
    company: CompanyResponse
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
    timeline: list[dict] = []
    documents: list[dict] = []
    signals: CompanySignals = CompanySignals()
    branches: list[BranchResponse] = []
    licenses: list[LicenseResponse] = []
    contact_count: int = 0
    opportunity_count: int = 0
    total_revenue: float = 0.0
