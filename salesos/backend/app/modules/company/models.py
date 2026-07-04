import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import BaseModel
# Import Contact for relationship resolution (bypasses string-name conflict)
from sqlalchemy.orm import relationship as _sa_relationship


class Source(BaseModel):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    base_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ingestion_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Source {self.name}>"


class Company(BaseModel):
    __tablename__ = "companies"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    name_ar: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(500))
    cr_number: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Commercial Registration number"
    )
    cr_type: Mapped[str | None] = mapped_column(
        String(50), comment="CR type code (e.g., شركة, مؤسسة)"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active", index=True, comment="Current company status"
    )
    city: Mapped[str | None] = mapped_column(String(200), index=True)
    region: Mapped[str | None] = mapped_column(String(200))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    postal_code: Mapped[str | None] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(50))
    fax: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text)

    capital: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    employees_count: Mapped[int | None] = mapped_column(Integer)

    activity_description: Mapped[str | None] = mapped_column(Text)
    activity_code: Mapped[str | None] = mapped_column(String(50))
    isic_code: Mapped[str | None] = mapped_column(String(20))
    isic_description: Mapped[str | None] = mapped_column(String(500))

    legal_form: Mapped[str | None] = mapped_column(String(100))
    incorporation_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)

    is_golden_record: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, default=0.0)
    source_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[list | None] = mapped_column(JSONB, default=list)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    branches: Mapped[list["Branch"]] = relationship("Branch", back_populates="company", lazy="selectin")
    licenses: Mapped[list["License"]] = relationship("License", back_populates="company", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Company {self.cr_number}: {self.name_ar}>"


class Branch(BaseModel):
    __tablename__ = "branches"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    name_ar: Mapped[str] = mapped_column(String(500), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(500))
    branch_number: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped[Company] = relationship("Company", back_populates="branches")

    def __repr__(self) -> str:
        return f"<Branch {self.branch_number}: {self.name_ar}>"


class License(BaseModel):
    __tablename__ = "licenses"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    license_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    license_type: Mapped[str] = mapped_column(String(100), nullable=False)
    license_type_ar: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="active")
    issuing_authority: Mapped[str | None] = mapped_column(String(200))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    renewal_date: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(100))

    company: Mapped[Company] = relationship("Company", back_populates="licenses")

    def __repr__(self) -> str:
        return f"<License {self.license_number}: {self.license_type}>"


class Contact(BaseModel):
    __tablename__ = "contacts"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    position: Mapped[str | None] = mapped_column(String(255))
    position_ar: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String(100))
    confidence_score: Mapped[float | None] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<Contact {self.name}: {self.email}>"
