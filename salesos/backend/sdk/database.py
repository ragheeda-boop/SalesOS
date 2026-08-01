"""Database abstractions: SQLAlchemy Base, Repository, UnitOfWork, and query helpers."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from sqlalchemy import DateTime, Select, func, select
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

from sdk.events.base import DomainEvent
from sdk.pagination import CursorPage, build_keyset_condition, decode_cursor, encode_cursor


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


T = TypeVar("T")
TId = TypeVar("TId")


class Entity(ABC):
    """Base class for domain entities."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    def __init__(self):
        self._events: list[DomainEvent] = []

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events


class Repository(ABC, Generic[T, TId]):
    """Generic repository interface following Domain-Driven Design."""

    def __init__(self, session: AsyncSession):
        self._session = session

    @abstractmethod
    async def get(self, id: TId) -> T: ...

    @abstractmethod
    async def save(self, entity: T) -> None: ...

    @abstractmethod
    async def delete(self, id: TId) -> None: ...

    async def exists(self, id: TId) -> bool:
        try:
            await self.get(id)
            return True
        except Exception:
            return False


class SqlAlchemyRepository(Repository[T, TId], ABC):
    """SQLAlchemy-based repository implementation."""

    model_class: type[Any]

    async def get(self, id: TId) -> T:
        result = await self._session.get(self.model_class, id)
        if result is None:
            from sdk.exceptions import ObjectNotFoundError

            raise ObjectNotFoundError(self.model_class.__name__, str(id))
        return cast(T, result)

    async def save(self, entity: T) -> None:
        self._session.add(entity)
        await self._session.flush()

    async def delete(self, id: TId) -> None:
        entity = await self.get(id)
        await self._session.delete(entity)
        await self._session.flush()

    async def find_all(
        self, page: int = 1, page_size: int = 20, order_by: str = "created_at", desc: bool = True
    ) -> tuple[list[T], int]:
        stmt: Select[Any] = select(self.model_class)
        count_stmt = select(func.count()).select_from(self.model_class)
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        order_col = getattr(self.model_class, order_by, None)
        if order_col:
            stmt = stmt.order_by(order_col.desc() if desc else order_col.asc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_all_cursored(
        self,
        page_size: int = 20,
        order_by: str = "created_at",
        desc: bool = True,
        cursor: str | None = None,
    ) -> CursorPage[T]:
        stmt: Select[Any] = select(self.model_class)
        order_col = getattr(self.model_class, order_by, None)
        if order_col:
            stmt = stmt.order_by(order_col.desc() if desc else order_col.asc())

        if cursor:
            cursor_id, cursor_sort = decode_cursor(cursor)
            condition = build_keyset_condition(
                self.model_class,
                cursor_id,
                cursor_sort,
                sort_by=order_by,
                sort_dir="desc" if desc else "asc",
            )
            stmt = stmt.where(condition)

        stmt = stmt.limit(page_size + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        has_next = len(rows) > page_size
        if has_next:
            rows = rows[:page_size]

        next_cursor = None
        previous_cursor = None
        if rows:
            last = rows[-1]
            sort_val = getattr(last, order_by, None)
            next_cursor = encode_cursor(str(last.id), sort_val)
            first = rows[0]
            sort_val_first = getattr(first, order_by, None)
            previous_cursor = encode_cursor(str(first.id), sort_val_first)

        return CursorPage(
            items=rows,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
            has_next=has_next,
        )


class UnitOfWork:
    """Unit of Work pattern for managing transactional consistency."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        session = self.session
        if session is None:
            return
        if exc_type is not None:
            await session.rollback()
        else:
            await session.commit()
        await session.close()
        self.session = None

    async def flush(self) -> None:
        if self.session:
            await self.session.flush()

    def get_repository(self, repo_class: type[Repository]) -> Repository:
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not active")
        return repo_class(self.session)


class Specification(ABC):
    """Specification pattern for building reusable query filters."""

    @abstractmethod
    def apply(self, stmt: Select[Any]) -> Select[Any]: ...

    def __and__(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)


class AndSpecification(Specification):
    def __init__(self, *specs: Specification):
        self.specs = specs

    def apply(self, stmt: Select[Any]) -> Select[Any]:
        for spec in self.specs:
            stmt = spec.apply(stmt)
        return stmt


class OrSpecification(Specification):
    def __init__(self, *specs: Specification):
        self.specs = specs

    def apply(self, stmt: Select[Any]) -> Select[Any]:
        from sqlalchemy import or_

        conditions: list[ColumnElement[bool]] = [
            cast(ColumnElement[bool], c)
            for c in (spec.apply(select(func.now())).whereclause for spec in self.specs)
            if c is not None
        ]
        return stmt.where(or_(*conditions))
