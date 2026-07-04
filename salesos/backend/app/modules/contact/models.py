import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import BaseModel


class Contact(BaseModel):
    __tablename__ = "contacts_standalone"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=True
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

    def __repr__(self) -> str:
        return f"<Contact {self.name}: {self.email}>"
