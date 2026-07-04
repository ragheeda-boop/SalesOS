"""Universal Business Object Model (UBOM) — base class for all business entities.

Every entity (Company, Contact, Deal, License, etc.) inherits from BusinessObject,
which provides built-in: ID, Tenant, Timeline, Permissions, AI, Search, Graph,
Feature Store, Audit, Events, Attachments, Tags, Relations, Status, Owner.

ADR-021: All new business entities MUST extend BusinessObject.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declared_attr, registry

# Common registry for all UBOM models
mapper_registry = registry()

# Global set of registered entity types
REGISTERED_ENTITY_TYPES: dict[str, type] = {}


class BusinessObject:
    """Abstract base for all business objects. NOT a table — use as mixin.

    Every entity model must inherit this class to automatically gain:
      - id (UUID, primary key)
      - tenant_id (UUID FK → tenants.id)
      - status (String)
      - owner_id (UUID, nullable)
      - tags (JSONB)
      - metadata (JSONB)
      - created_at, updated_at (DateTime)

    Additional capabilities are provided by the runtime layers:
      - Timeline: via TimelineRuntime (event subscriber)
      - Audit: via AuditLog table (event subscriber)
      - Events: via EventRuntime (publish on CRUD)
      - Search: via SearchRuntime (full-text + semantic index)
      - Graph: via KnowledgeGraphEngine (Neo4j node)
      - Feature Store: via FeatureStore (computed scores)
      - AI: via DecisionEngine (context + recommendations)
      - Permissions: via PolicyRuntime (policy evaluation)
    """

    @declared_attr
    def __tablename__(cls) -> str:
        # Auto-generate table name from class name: CompanyObject → companies
        name = cls.__name__
        if name.endswith("Object"):
            name = name[:-6]
        # Simple pluralization
        return f"{name.lower()}s"

    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    @declared_attr
    def tenant_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    @declared_attr
    def status(cls):
        return Column(String(50), nullable=False, default="active", server_default="active")

    @declared_attr
    def owner_id(cls):
        return Column(UUID(as_uuid=True), nullable=True, index=True)

    @declared_attr
    def tags(cls):
        return Column(JSONB, nullable=True, default=list)

    @declared_attr
    def metadata_(cls):
        return Column("metadata", JSONB, nullable=True, default=dict)

    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name, None)
            if isinstance(val, datetime):
                val = val.isoformat()
            elif hasattr(val, "hex"):
                val = str(val)
            result[col.name] = val
        return result

    @classmethod
    def register(cls):
        """Register this entity type in the global registry."""
        table_name = cls.__tablename__
        REGISTERED_ENTITY_TYPES[table_name] = cls
        REGISTERED_ENTITY_TYPES[cls.__name__] = cls
        return cls


# ── Concrete entity models inheriting from BusinessObject ─────

class CompanyObject(BusinessObject):
    __tablename__ = "companies"

    name_ar = Column(String(500), nullable=False)
    name_en = Column(String(500), nullable=True)
    cr_number = Column(String(50), nullable=False, index=True)
    cr_type = Column(String(50), nullable=True)
    city = Column(String(200), nullable=True)
    region = Column(String(200), nullable=True)
    industry = Column(String(200), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    capital = Column(Float, nullable=True)
    employees_count = Column(Integer, nullable=True)
    annual_revenue = Column(Float, nullable=True)
    activity_description = Column(Text, nullable=True)
    legal_form = Column(String(100), nullable=True)
    incorporation_date = Column(DateTime, nullable=True)
    is_golden_record = Column(Boolean, default=False, server_default="false")
    confidence_score = Column(Float, default=0.0, server_default="0.0")
    do_not_contact = Column(Boolean, default=False, server_default="false")
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    source_ids = Column(JSONB, nullable=True)
    embedding = Column(JSONB, nullable=True)

    def display_name(self) -> str:
        return self.name_ar or self.name_en or self.cr_number


class ContactObject(BusinessObject):
    __tablename__ = "contacts"

    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    position = Column(String(255), nullable=True)
    position_ar = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False, server_default="false")
    source = Column(String(100), nullable=True)
    confidence_score = Column(Float, default=0.0, server_default="0.0")

    def display_name(self) -> str:
        return self.name or self.email or ""


class LicenseObject(BusinessObject):
    __tablename__ = "licenses"

    license_number = Column(String(100), nullable=False)
    license_type = Column(String(100), nullable=False)
    license_type_ar = Column(String(200), nullable=True)
    issuing_authority = Column(String(200), nullable=True)
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    renewal_date = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True)


class BranchObject(BusinessObject):
    __tablename__ = "branches"

    name_ar = Column(String(500), nullable=False)
    name_en = Column(String(500), nullable=True)
    branch_number = Column(String(50), nullable=True)
    city = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class DealObject(BusinessObject):
    __tablename__ = "deals"

    deal_name = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="SAR")
    stage = Column(String(50), nullable=True)
    probability = Column(Float, nullable=True)
    expected_close_date = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    owner = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)


# ── Register all entity types ─────────────────────────────────

for cls in [CompanyObject, ContactObject, LicenseObject, BranchObject, DealObject]:
    cls.register()


def get_entity_type(table_name: str) -> Optional[type]:
    return REGISTERED_ENTITY_TYPES.get(table_name)


def get_all_entity_types() -> dict[str, dict]:
    result = {}
    for name, cls in REGISTERED_ENTITY_TYPES.items():
        if name.startswith("_"):
            continue
        # Collect declared Column objects from class dict (not __table__)
        fields = []
        for key, val in cls.__dict__.items():
            if isinstance(val, Column):
                fields.append(key)
        result[name] = {
            "class": cls.__name__,
            "table": getattr(cls, "__tablename__", name),
            "fields": sorted(fields),
        }
    return result
