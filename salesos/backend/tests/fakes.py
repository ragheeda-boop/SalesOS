"""Shared fake implementations for unit tests — replaces duplicated FakeMapping/FakeMappings/FakeResult across test files."""

from __future__ import annotations

from typing import Any, Callable, Optional
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession


class FakeDBResult:
    """Simulates a SQLAlchemy `CursorResult` for `.mappings()`, `.scalar()`, `.one_or_none()`, and iteration.

    Centralises all the duplicated `FakeMapping`/`FakeMappings`/`FakeResult` variants found
    across test files into a single unified implementation.
    """

    def __init__(self, rows: Optional[list[dict]] = None, one: Optional[dict] = None, scalar_val: Any = None):
        self._rows = rows or []
        self._one = one
        self._scalar_val = scalar_val
        self._row_iter_index = 0

    # ── dict-like access (replaces FakeMapping) ──────────────────────────────

    def __getitem__(self, key: str) -> Any:
        if self._one is not None:
            return self._one[key]
        if self._rows:
            return self._rows[0][key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        if self._one is not None:
            return self._one.get(key, default)
        if self._rows:
            return self._rows[0].get(key, default)
        return default

    def keys(self) -> list[str]:
        if self._one is not None:
            return list(self._one.keys())
        if self._rows:
            return list(self._rows[0].keys())
        return []

    def __iter__(self):
        for row_data in self._rows:
            yield FakeDBResult(one=row_data)

    def __len__(self) -> int:
        if self._one is not None:
            return len(self._one)
        return len(self._rows)

    # ── .mappings() access (replaces FakeMappings) ───────────────────────────

    def mappings(self) -> FakeDBResult:
        return self

    # ── scalar access ────────────────────────────────────────────────────────

    def scalar(self) -> Any:
        return self._scalar_val if self._scalar_val is not None else 0

    def scalar_one_or_none(self) -> Any:
        return self._scalar_val

    # ── row access ───────────────────────────────────────────────────────────

    def one(self) -> FakeDBResult:
        return self

    def one_or_none(self) -> Optional[FakeDBResult]:
        return self if self._one is not None else None

    def all(self) -> list[FakeDBResult]:
        return [FakeDBResult(one=r) for r in self._rows]


class FakeExecute:
    """Base class for SQL-text-dispatched execute mocks.

    Subclass and override `_dispatch` to return appropriate data per SQL pattern,
    or use `with_handler` to attach a custom handler function.
    """

    def __init__(self, handler: Optional[Callable[[str, Any], FakeDBResult]] = None):
        self._handler = handler

    async def __call__(self, sql_str, params=None) -> FakeDBResult:
        text = str(sql_str)
        if self._handler:
            return self._handler(text, params)
        return self._dispatch(text, params)

    def _dispatch(self, text: str, params: Any) -> FakeDBResult:
        return FakeDBResult()


def fake_session(execute: Any = None) -> AsyncMock:
    """Create an `AsyncMock` spec'd to `AsyncSession` with a configurable `.execute`.

    Usage::

        session = fake_session()
        session = fake_session(FakeExecute(handler=my_handler))
    """
    session = AsyncMock(spec=AsyncSession)
    if execute is not None:
        session.execute = execute
    return session
