import uuid
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import BaseModel


class Contact(BaseModel):
    """Unified contacts table (post-0022; formerly contacts_standalone)."""

    __tablename__ = "contacts"
    __table_args__ = (
        # Live composites (0022) — register to silence remove_index (DEC-130g)
        Index("ix_contacts_tenant_company", "tenant_id", "company_id"),
        Index("ix_contacts_tenant_email", "tenant_id", "email"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    name_ar: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))

    position: Mapped[str | None] = mapped_column(String(255))
    position_ar: Mapped[str | None] = mapped_column(String(255))
    department: Mapped[str | None] = mapped_column(String(255))

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String(100))
    confidence_score: Mapped[float | None] = mapped_column(Float, default=0.0)

    tags: Mapped[list | None] = mapped_column(JSONB, default=list)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, default=dict)

    company: Mapped[Any] = relationship(
        "app.modules.company.models.Company",
        back_populates="contacts",
    )

    def __repr__(self) -> str:
        return f"<Contact {self.name}: {self.email}>"
