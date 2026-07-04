"""Database abstractions: Repository base, UnitOfWork, and query helpers."""

import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sdk.events.base import DomainEvent

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

    model_class: type = None

    async def get(self, id: TId) -> T:
        result = await self._session.get(self.model_class, id)
        if result is None:
            from sdk.exceptions import ObjectNotFoundError

            raise ObjectNotFoundError(self.model_class.__name__, str(id))
        return result

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
        stmt = select(self.model_class)
        count_stmt = select(func.count()).select_from(self.model_class)
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        order_col = getattr(self.model_class, order_by, None)
        if order_col:
            stmt = stmt.order_by(order_col.desc() if desc else order_col.asc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total


class UnitOfWork:
    """Unit of Work pattern for managing transactional consistency."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
        self.session = None

    async def flush(self) -> None:
        if self.session:
            await self.session.flush()

    def get_repository(self, repo_class: type[Repository]) -> Repository:
        return repo_class(self.session)


class Specification(ABC):
    """Specification pattern for building reusable query filters."""

    @abstractmethod
    def apply(self, stmt: Select) -> Select: ...

    def __and__(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)


class AndSpecification(Specification):
    def __init__(self, *specs: Specification):
        self.specs = specs

    def apply(self, stmt: Select) -> Select:
        for spec in self.specs:
            stmt = spec.apply(stmt)
        return stmt


class OrSpecification(Specification):
    def __init__(self, *specs: Specification):
        self.specs = specs

    def apply(self, stmt: Select) -> Select:
        from sqlalchemy import or_

        conditions = [spec.apply(select(func.now())).whereclause for spec in self.specs]
        return stmt.where(or_(*conditions))
