"""DB-05 Slice 2 (DEC-121): emails/meetings type authority = Alembic UUID DDL."""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import UUID

from domains.commercial.infrastructure.models import EmailModel, MeetingModel

_UUID_COLS = ("id", "tenant_id", "opportunity_id")


def _assert_uuid_str_columns(model) -> None:
    for name in _UUID_COLS:
        col = model.__table__.c[name]
        assert isinstance(col.type, UUID), f"{model.__tablename__}.{name} type={col.type!r}"
        assert (
            col.type.as_uuid is False
        ), f"{model.__tablename__}.{name} must keep as_uuid=False (Mapped[str])"


def test_meeting_model_uuid_authority() -> None:
    _assert_uuid_str_columns(MeetingModel)


def test_email_model_uuid_authority() -> None:
    _assert_uuid_str_columns(EmailModel)
