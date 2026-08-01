import uuid
from datetime import date
from typing import Any

from sqlalchemy import Boolean, Computed, Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

# Import Contact for relationship resolution (bypasses string-name conflict)
from app.common.models import BaseModel

# DEC-129 / Phase 0 criterion 7.4 — matches Alembic 0023 GENERATED ALWAYS expression.
# Do NOT DROP: live FTS for search_runtime / domains.search.
_COMPANIES_SEARCH_VECTOR_EXPR = (
    "to_tsvector('simple', "
    "COALESCE(name_ar, '') || ' ' || "
    "COALESCE(name_en, '') || ' ' || "
    "COALESCE(cr_number, '') || ' ' || "
    "COALESCE(city, '') || ' ' || "
    "COALESCE(industry, '') || ' ' || "
    "COALESCE(activity_description, '') || ' ' || "
    "COALESCE(region, '') || ' ' || "
    "COALESCE(legal_form, '')"
    ")"
)


class _PgVector(UserDefinedType):
    """pgvector metadata stand-in (DEC-130e) — no pgvector package required.

    Live DB reflects embedding_vector as NullType; compare_against_backend
    returns True so alembic check does not propose DROP/ALTER.
    """

    cache_ok = True

    def __init__(self, dim: int = 3072) -> None:
        self.dim = dim

    def get_col_spec(self, **_kw: Any) -> str:
        return f"vector({self.dim})"

    def compare_against_backend(self, _dialect: Any, _conn_type: Any) -> bool:
        return True


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
    # Comments live in code/docs only — DB has no COMMENT (DEC-130g; no COMMENT DDL)
    cr_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    cr_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
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
    industry: Mapped[str | None] = mapped_column(String(200), index=True)
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

    # ── Feature-store / hierarchy columns (Alembic 0002) — DEC-129 KEEP ──
    parent_company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
        index=True,
    )
    annual_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_prev_year: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_2yr_ago: Mapped[float | None] = mapped_column(Float, nullable=True)
    employee_count_prev_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    branch_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default="0"
    )

    # ── DNC + embedding (Alembic 0003 / 0006) — DEC-130e KEEP (no DROP) ──
    do_not_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    embedding_vector: Mapped[Any | None] = mapped_column(
        _PgVector(3072), nullable=True
    )

    # ── FTS columns (Alembic 0006 tsv + 0023 search_vector) — DEC-129 KEEP ──
    tsv: Mapped[Any | None] = mapped_column(TSVECTOR, nullable=True)
    search_vector: Mapped[Any | None] = mapped_column(
        TSVECTOR,
        Computed(_COMPANIES_SEARCH_VECTOR_EXPR, persisted=True),
        nullable=True,
    )

    branches: Mapped[list["Branch"]] = relationship(
        "Branch", back_populates="company", lazy="selectin", cascade="all, delete-orphan"
    )
    licenses: Mapped[list["License"]] = relationship(
        "License", back_populates="company", lazy="selectin", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "app.modules.contact.models.Contact",
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_companies_tenant_confidence", "tenant_id", "confidence_score"),
        Index("ix_companies_tenant_golden", "tenant_id", "is_golden_record"),
        Index("ix_companies_tenant_created", "tenant_id", "created_at"),
        Index("ix_companies_tenant_status", "tenant_id", "status"),
        Index("ix_companies_tsv", "tsv", postgresql_using="gin"),
        Index("idx_companies_search_vector", "search_vector", postgresql_using="gin"),
        # Live unique (0001) — register to silence remove_index (DEC-130g)
        Index("ix_companies_tenant_cr", "tenant_id", "cr_number", unique=True),
        Index("ix_companies_confidence_score", "confidence_score"),
        Index("idx_companies_tenant_search", "tenant_id"),
        # Live GIN trigram indexes (0024/0029) — metadata register only (no DROP)
        Index(
            "idx_companies_name_trgm",
            "name_ar",
            postgresql_using="gin",
            postgresql_ops={"name_ar": "gin_trgm_ops"},
        ),
        Index(
            "idx_companies_name_ar_trgm",
            "name_ar",
            postgresql_using="gin",
            postgresql_ops={"name_ar": "gin_trgm_ops"},
        ),
        Index(
            "idx_companies_name_en_trgm",
            "name_en",
            postgresql_using="gin",
            postgresql_ops={"name_en": "gin_trgm_ops"},
        ),
        Index(
            "idx_companies_cr_number_trgm",
            "cr_number",
            postgresql_using="gin",
            postgresql_ops={"cr_number": "gin_trgm_ops"},
        ),
        Index(
            "idx_companies_city_trgm",
            "city",
            postgresql_using="gin",
            postgresql_ops={"city": "gin_trgm_ops"},
        ),
        Index(
            "idx_companies_region_trgm",
            "region",
            postgresql_using="gin",
            postgresql_ops={"region": "gin_trgm_ops"},
        ),
        Index(
            "idx_companies_activity_desc_trgm",
            "activity_description",
            postgresql_using="gin",
            postgresql_ops={"activity_description": "gin_trgm_ops"},
        ),
    )

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

    # Index owned by __table_args__ (live name ix_licenses_company) — no index=True
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
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

    __table_args__ = (
        Index("ix_licenses_expiry_status", "expiry_date", "status"),
        # Live name (0028) — register to silence remove_index (DEC-130g)
        Index("ix_licenses_company", "company_id"),
        # Rename twin from former column index=True — KEEP (DEC-130g; no DROP)
        Index("ix_licenses_company_id", "company_id"),
    )

    def __repr__(self) -> str:
        return f"<License {self.license_number}: {self.license_type}>"


# Canonical Contact ORM lives in contact module (unified `contacts` table post-0022).
from app.modules.contact.models import Contact  # noqa: E402
