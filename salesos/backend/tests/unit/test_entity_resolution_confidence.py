"""Unit tests for EntityResolutionService confidence scoring and conflict resolution logic."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.entity_resolution.service import (
    SOURCE_PRIORITY,
    EntityResolutionService,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    return EntityResolutionService(db=mock_db, event_bus=None, logger=None)


class TestComputeFieldConfidence:
    def test_balady_cr_number(self, service):
        score = service._compute_field_confidence("cr_number", "balady")
        assert score == 1.0  # 1.0 + 0.15 capped at 1.0

    def test_balady_name_ar(self, service):
        score = service._compute_field_confidence("name_ar", "balady")
        assert score == 1.0  # 1.0 + 0.05 capped at 1.0

    def test_balady_regular_field(self, service):
        score = service._compute_field_confidence("city", "balady")
        assert score == 1.0

    def test_ncnp_license_number(self, service):
        score = service._compute_field_confidence("license_number", "ncnp")
        assert score == 1.0  # 0.9 + 0.15 capped at 1.0

    def test_unknown_source(self, service):
        score = service._compute_field_confidence("name", "unknown_source")
        assert score == 0.5

    def test_company_name_boost(self, service):
        score = service._compute_field_confidence("company_name", "hubspot")
        assert score == 0.35  # 0.3 + 0.05

    def test_socpa_regular_field(self, service):
        score = service._compute_field_confidence("address", "socpa")
        assert score == 0.5

    def test_all_source_priorities_used(self, service):
        for source, priority in SOURCE_PRIORITY.items():
            score = service._compute_field_confidence("email", source)
            expected = priority / 100.0
            assert abs(score - expected) < 0.01


class TestComputeOverallConfidence:
    def test_empty_data(self, service):
        assert service._compute_overall_confidence({}) == 0.0

    def test_no_confidence_fields(self, service):
        data = {"name": {"value": "Test", "source": "balady"}}
        assert service._compute_overall_confidence(data) == 0.0

    def test_single_field(self, service):
        data = {
            "name": {"value": "Test", "source": "balady", "confidence": 0.8},
        }
        assert abs(service._compute_overall_confidence(data) - 0.8) < 0.01

    def test_multiple_fields_averaged(self, service):
        data = {
            "name": {"value": "A", "confidence": 0.8},
            "city": {"value": "B", "confidence": 0.6},
            "cr": {"value": "C", "confidence": 1.0},
        }
        avg = service._compute_overall_confidence(data)
        assert abs(avg - 0.8) < 0.01  # (0.8+0.6+1.0)/3 = 0.8

    def test_non_dict_entries_skipped(self, service):
        data = {
            "name": {"value": "Test", "confidence": 0.9},
            "tags": ["a", "b"],
        }
        assert abs(service._compute_overall_confidence(data) - 0.9) < 0.01


class TestSourcePriority:
    def test_balady_highest(self):
        assert SOURCE_PRIORITY["balady"] > SOURCE_PRIORITY["ncnp"]

    def test_hubspot_lowest(self):
        assert SOURCE_PRIORITY["hubspot"] < SOURCE_PRIORITY["apollo"]

    def test_all_sources_have_priority(self):
        expected_sources = {"balady", "ncnp", "taqeem", "rega", "najiz", "socpa", "apollo", "hubspot"}
        assert set(SOURCE_PRIORITY.keys()) == expected_sources


class TestResolveConflictStrategies:
    @pytest.mark.asyncio
    async def test_resolve_use_source_a(self, service, mock_db):
        conflict = MagicMock()
        conflict.status = "open"
        mock_result = MagicMock()
        mock_result.get.return_value = conflict
        service.conflict_repo = MagicMock()
        service.conflict_repo.get = AsyncMock(return_value=conflict)

        result = await service.resolve_conflict(
            str(uuid.uuid4()), "use_source_a"
        )
        assert result.status == "resolved"
        assert result.resolution_strategy == "use_source_a"

    @pytest.mark.asyncio
    async def test_resolve_use_source_b(self, service, mock_db):
        conflict = MagicMock()
        conflict.golden_record_id = uuid.uuid4()
        conflict.field_name = "name_ar"
        conflict.source_b_value = "New Name"
        conflict.source_b_source = "BALADY"

        golden = MagicMock()
        golden.data = {"name_ar": {"value": "Old Name", "source": "NCNP", "confidence": 0.7}}
        golden.confidence_score = 0.7

        service.conflict_repo = MagicMock()
        service.conflict_repo.get = AsyncMock(return_value=conflict)
        service.golden_repo = MagicMock()
        service.golden_repo.get = AsyncMock(return_value=golden)

        result = await service.resolve_conflict(
            str(uuid.uuid4()), "use_source_b",
            resolved_by=str(uuid.uuid4()),
        )
        assert result.status == "resolved"
        assert golden.data["name_ar"]["value"] == "New Name"

    @pytest.mark.asyncio
    async def test_resolve_merge_with_custom_value(self, service, mock_db):
        conflict = MagicMock()
        conflict.golden_record_id = uuid.uuid4()
        conflict.field_name = "name_ar"

        golden = MagicMock()
        golden.data = {"name_ar": {"value": "Old", "source": "NCNP", "confidence": 0.7}}
        golden.confidence_score = 0.7

        service.conflict_repo = MagicMock()
        service.conflict_repo.get = AsyncMock(return_value=conflict)
        service.golden_repo = MagicMock()
        service.golden_repo.get = AsyncMock(return_value=golden)

        result = await service.resolve_conflict(
            str(uuid.uuid4()), "merge", custom_value="Merged Name",
            resolved_by=str(uuid.uuid4()),
        )
        assert result.status == "resolved"
        assert golden.data["name_ar"]["value"] == "Merged Name"
        assert golden.data["name_ar"]["source"] == "manual_merge"

    @pytest.mark.asyncio
    async def test_resolve_custom_strategy(self, service, mock_db):
        conflict = MagicMock()
        conflict.golden_record_id = uuid.uuid4()
        conflict.field_name = "email"

        golden = MagicMock()
        golden.data = {"email": {"value": "old@example.com", "source": "NCNP"}}
        golden.confidence_score = 0.8

        service.conflict_repo = MagicMock()
        service.conflict_repo.get = AsyncMock(return_value=conflict)
        service.golden_repo = MagicMock()
        service.golden_repo.get = AsyncMock(return_value=golden)

        result = await service.resolve_conflict(
            str(uuid.uuid4()), "custom",
            custom_value="new@example.com",
            resolved_by=str(uuid.uuid4()),
        )
        assert result.status == "resolved"
        assert golden.data["email"]["value"] == "new@example.com"
        assert golden.data["email"]["source"] == "manual_custom"
