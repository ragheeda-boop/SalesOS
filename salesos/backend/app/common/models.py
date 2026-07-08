"""Common SQLAlchemy models — re-exported from sdk.database for backward compatibility."""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from sdk.database import Base, BaseModel, TimestampMixin

__all__ = ["Base", "BaseModel", "TimestampMixin", "EntityCodeMixin"]


class EntityCodeMixin:
    entity_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="Universal entity identifier: MODULE_ENTITY_TYPE_UUID_SHORT",
    )
