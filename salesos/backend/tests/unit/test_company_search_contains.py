"""Tests for CompanySearchRepository — 'contains' filter (ilike).

Validates that dict filters with {"contains": value} produce ilike
conditions, not silent pass-through (the bug fixed 2026-08-21).
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domains.search.contracts.models import SearchQuery, SearchSort


# ── Helpers ──────────────────────────────────────────────────────────────


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


def _patch_company_model():
    """Return a mock Company class with expected column attributes."""
    model = MagicMock()
    model.tenant_id = MagicMock()
    model.tenant_id.__eq__ = lambda self, other: True
    for col in (
        "name_ar",
        "name_en",
        "cr_number",
        "city",
        "region",
        "status",
        "activity_description",
        "legal_form",
        "confidence_score",
        "created_at",
        "updated_at",
    ):
        setattr(model, col, MagicMock())
        getattr(model, col).ilike = MagicMock(return_value=MagicMock())
        getattr(model, col).__eq__ = MagicMock(return_value=MagicMock())
    return model


# ── Tests ────────────────────────────────────────────────────────────────


class TestContainsFilter:
    """Verify 'contains' dict filter produces ilike, not == ."""

    @patch("app.modules.company.search_repository.Company", new_callable=_patch_company_model)
    def test_contains_cr_number(self, MockCompany):
        from app.modules.company.search_repository import CompanySearchRepository

        repo = CompanySearchRepository.__new__(CompanySearchRepository)
        repo._Company = MockCompany
        repo.db = MagicMock()

        query = _make_query(filters={"cr_number": {"contains": "12345"}})
        stmt = repo._build_base(query)

        MockCompany.cr_number.ilike.assert_called_with("%12345%")

    @patch("app.modules.company.search_repository.Company", new_callable=_patch_company_model)
    def test_contains_city(self, MockCompany):
        from app.modules.company.search_repository import CompanySearchRepository

        repo = CompanySearchRepository.__new__(CompanySearchRepository)
        repo._Company = MockCompany
        repo.db = MagicMock()

        query = _make_query(filters={"city": {"contains": "الرياض"}})
        stmt = repo._build_base(query)

        MockCompany.city.ilike.assert_called_with("%الرياض%")

    @patch("app.modules.company.search_repository.Company", new_callable=_patch_company_model)
    def test_contains_region(self, MockCompany):
        from app.modules.company.search_repository import CompanySearchRepository

        repo = CompanySearchRepository.__new__(CompanySearchRepository)
        repo._Company = MockCompany
        repo.db = MagicMock()

        query = _make_query(filters={"region": {"contains": "شرق"}})
        stmt = repo._build_base(query)

        MockCompany.region.ilike.assert_called_with("%شرق%")

    @patch("app.modules.company.search_repository.Company", new_callable=_patch_company_model)
    def test_eq_filter_still_works(self, MockCompany):
        from app.modules.company.search_repository import CompanySearchRepository

        repo = CompanySearchRepository.__new__(CompanySearchRepository)
        repo._Company = MockCompany
        repo.db = MagicMock()

        query = _make_query(filters={"status": {"eq": "active"}})
        stmt = repo._build_base(query)

        MockCompany.status.__eq__.assert_called()

    @patch("app.modules.company.search_repository.Company", new_callable=_patch_company_model)
    def test_string_value_uses_exact_match(self, MockCompany):
        from app.modules.company.search_repository import CompanySearchRepository

        repo = CompanySearchRepository.__new__(CompanySearchRepository)
        repo._Company = MockCompany
        repo.db = MagicMock()

        query = _make_query(filters={"status": "active"})
        stmt = repo._build_base(query)

        MockCompany.status.__eq__.assert_called_with("active")
