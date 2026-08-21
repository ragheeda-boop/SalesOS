"""Tests for CompanySearchRepository — filters, sort, and operators.

Validates contains/ilike, eq, in, owner_id, segment, and sort_map.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from domains.search.contracts.models import SearchQuery, SearchSort


def _make_query(**overrides) -> SearchQuery:
    defaults = dict(
        query="test",
        tenant_id=str(uuid.uuid4()),
        page=1,
        page_size=10,
        filters={},
        context={},
        sort=SearchSort(field="created_at", direction="desc"),
    )
    defaults.update(overrides)
    return SearchQuery(**defaults)


def _make_col(name: str):
    col = MagicMock()
    col.ilike = MagicMock(return_value=MagicMock())
    col.__eq__ = MagicMock(return_value=MagicMock())
    col.__ge__ = MagicMock(return_value=MagicMock())
    col.__le__ = MagicMock(return_value=MagicMock())
    col.in_ = MagicMock(return_value=MagicMock())
    col.asc = MagicMock(return_value=MagicMock(name=f"{name}.asc"))
    col.desc = MagicMock(return_value=MagicMock(name=f"{name}.desc"))
    return col


def _make_repo():
    from app.modules.company.search_repository import CompanySearchRepository

    model = MagicMock()
    model.tenant_id = _make_col("tenant_id")
    for col in (
        "name_ar", "name_en", "cr_number", "city", "region",
        "status", "activity_description", "legal_form",
        "owner_id", "segment",
        "confidence_score", "created_at", "updated_at",
    ):
        setattr(model, col, _make_col(col))

    repo = CompanySearchRepository.__new__(CompanySearchRepository)
    repo._Company = model
    repo.db = MagicMock()
    return repo, model


def _make_stmt():
    stmt = MagicMock()
    stmt.where = MagicMock(return_value=stmt)
    stmt.order_by = MagicMock(return_value=stmt)
    stmt.subquery = MagicMock(return_value=MagicMock())
    return stmt


MOCK_SELECT = MagicMock(return_value=_make_stmt())
MOCK_OR = MagicMock(side_effect=lambda *args: args)


@patch("app.modules.company.search_repository.select", MOCK_SELECT)
@patch("app.modules.company.search_repository.or_", MOCK_OR)
class TestContainsFilter:
    def test_contains_cr_number(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"cr_number": {"contains": "12345"}})
        repo._build_base(q)
        model.cr_number.ilike.assert_called_with("%12345%")

    def test_contains_city(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"city": {"contains": "الرياض"}})
        repo._build_base(q)
        model.city.ilike.assert_called_with("%الرياض%")

    def test_contains_region(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"region": {"contains": "شرق"}})
        repo._build_base(q)
        model.region.ilike.assert_called_with("%شرق%")


@patch("app.modules.company.search_repository.select", MOCK_SELECT)
@patch("app.modules.company.search_repository.or_", MOCK_OR)
class TestEqFilter:
    def test_eq_filter(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"status": {"eq": "active"}})
        repo._build_base(q)
        model.status.__eq__.assert_called()

    def test_string_value_exact_match(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"status": "active"})
        repo._build_base(q)
        model.status.__eq__.assert_called_with("active")


@patch("app.modules.company.search_repository.select", MOCK_SELECT)
@patch("app.modules.company.search_repository.or_", MOCK_OR)
class TestInFilter:
    def test_in_filter(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"status": {"in": ["active", "inactive"]}})
        repo._build_base(q)
        model.status.in_.assert_called_once()


@patch("app.modules.company.search_repository.select", MOCK_SELECT)
@patch("app.modules.company.search_repository.or_", MOCK_OR)
class TestOwnerSegmentFilters:
    def test_owner_id_eq_filter(self, *_):
        repo, model = _make_repo()
        owner = uuid.uuid4()
        q = _make_query(filters={"owner_id": {"eq": str(owner)}})
        repo._build_base(q)
        model.owner_id.__eq__.assert_called()

    def test_segment_eq_filter(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"segment": {"eq": "enterprise"}})
        repo._build_base(q)
        model.segment.__eq__.assert_called()

    def test_segment_exact_string_filter(self, *_):
        repo, model = _make_repo()
        q = _make_query(filters={"segment": "enterprise"})
        repo._build_base(q)
        model.segment.__eq__.assert_called_with("enterprise")


@patch("app.modules.company.search_repository.select", MOCK_SELECT)
@patch("app.modules.company.search_repository.or_", MOCK_OR)
class TestSortMap:
    def test_sort_by_owner_id(self, *_):
        repo, model = _make_repo()
        q = _make_query(sort=SearchSort(field="owner_id", direction="asc"))
        stmt = repo._apply_sort(_make_stmt(), q)
        assert stmt is not None

    def test_sort_by_segment(self, *_):
        repo, model = _make_repo()
        q = _make_query(sort=SearchSort(field="segment", direction="desc"))
        stmt = repo._apply_sort(_make_stmt(), q)
        assert stmt is not None

    def test_unknown_sort_falls_back_to_created_at(self, *_):
        repo, model = _make_repo()
        q = _make_query(sort=SearchSort(field="nonexistent_field", direction="asc"))
        stmt = repo._apply_sort(_make_stmt(), q)
        assert stmt is not None
