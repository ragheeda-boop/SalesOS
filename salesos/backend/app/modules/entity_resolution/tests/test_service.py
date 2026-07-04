"""Tests for Entity Resolution Service."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sdk.exceptions import ObjectNotFoundError
from app.modules.entity_resolution.service import EntityResolutionService
from app.modules.entity_resolution.repositories import GoldenRecordRepository, ConflictRepository
from app.modules.entity_resolution.models import GoldenRecord


@pytest.mark.asyncio
async def test_service_instantiation(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    assert service.golden_repo is not None
    assert service.conflict_repo is not None
    assert service.company_repo is not None
    assert service.db is db_session


@pytest.mark.asyncio
async def test_resolve_records_creates_golden_record(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    records = [{"cr_number": "CR-001", "name_ar": "TestCo", "city": "Riyadh"}]
    result = await service.resolve_records(tenant_id=test_tenant, source_slug="balady", records=records)
    assert result["records_processed"] == 1
    assert result["records_created"] == 1
    assert result["records_matched"] == 0
    golden_repo = GoldenRecordRepository(db_session)
    golden = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-001")
    assert golden is not None
    assert golden.cr_number == "CR-001"
    assert golden.confidence_score > 0
    assert "balady" in golden.source_ids


@pytest.mark.asyncio
async def test_resolve_records_matches_existing(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    r1 = await service.resolve_records(test_tenant, "balady", [{"cr_number": "CR-MATCH", "name_ar": "Original", "city": "Jeddah"}])
    assert r1["records_created"] == 1
    r2 = await service.resolve_records(test_tenant, "ncnp", [{"cr_number": "CR-MATCH", "name_ar": "Updated", "phone": "0123456789"}])
    assert r2["records_matched"] == 1
    assert r2["records_merged"] == 1
    golden_repo = GoldenRecordRepository(db_session)
    golden = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-MATCH")
    assert golden is not None
    assert golden.data["phone"]["value"] == "0123456789"


@pytest.mark.asyncio
async def test_resolve_records_higher_priority_overwrites(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    await service.resolve_records(test_tenant, "hubspot", [{"cr_number": "CR-PRIO", "name_ar": "LowPriority"}])
    r2 = await service.resolve_records(test_tenant, "balady", [{"cr_number": "CR-PRIO", "name_ar": "HighPriority"}])
    assert r2["records_matched"] == 1
    golden_repo = GoldenRecordRepository(db_session)
    golden = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-PRIO")
    assert golden.data["name_ar"]["value"] == "HighPriority"
    assert golden.data["name_ar"]["source"] == "BALADY"


@pytest.mark.asyncio
async def test_resolve_records_skips_missing_cr(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    records = [{"name_ar": "No CR"}, {"cr_number": "CR-SKIP", "name_ar": "Has CR"}]
    result = await service.resolve_records(test_tenant, "rega", records)
    assert result["records_processed"] == 1
    assert result["records_created"] == 1
    assert len(result["errors"]) == 1
    assert "Missing cr_number" in result["errors"][0]["error"]


@pytest.mark.asyncio
async def test_resolve_records_tenant_isolation(db_session: AsyncSession, test_tenant: str, test_tenant_2: str):
    service = EntityResolutionService(db_session)
    records = [{"cr_number": "CR-ISO", "name_ar": "Company"}]
    r1 = await service.resolve_records(test_tenant, "balady", records)
    assert r1["records_created"] == 1
    r2 = await service.resolve_records(test_tenant_2, "balady", records)
    assert r2["records_created"] == 1
    golden_repo = GoldenRecordRepository(db_session)
    g1 = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-ISO")
    g2 = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant_2), "CR-ISO")
    assert g1 is not None
    assert g2 is not None
    assert g1.id != g2.id


@pytest.mark.asyncio
async def test_get_golden_record(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    await service.resolve_records(test_tenant, "najiz", [{"cr_number": "CR-GET", "name_ar": "GetTest"}])
    golden_repo = GoldenRecordRepository(db_session)
    golden = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-GET")
    result = await service.get_golden_record(str(golden.id))
    assert result is not None
    assert result.id == golden.id
    assert result.cr_number == "CR-GET"


@pytest.mark.asyncio
async def test_get_golden_record_not_found(db_session: AsyncSession):
    service = EntityResolutionService(db_session)
    fake_id = uuid.uuid4()
    with pytest.raises(ObjectNotFoundError):
        await service.get_golden_record(str(fake_id))


@pytest.mark.asyncio
async def test_get_golden_by_cr(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    await service.resolve_records(test_tenant, "apollo", [{"cr_number": "CR-FIND", "name_ar": "FindTest"}])
    result = await service.get_golden_by_cr(test_tenant, "CR-FIND")
    assert result is not None
    assert result.cr_number == "CR-FIND"


@pytest.mark.asyncio
async def test_get_golden_by_cr_not_found(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    result = await service.get_golden_by_cr(test_tenant, "CR-NONEXISTENT")
    assert result is None


@pytest.mark.asyncio
async def test_list_golden_records_pagination(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    for i in range(3):
        await service.resolve_records(test_tenant, "balady", [{"cr_number": f"CR-LIST-{i}", "name_ar": f"Company {i}"}])
    records, total = await service.list_golden_records(test_tenant, page=1, page_size=10)
    assert total == 3
    assert len(records) == 3
    records_p1, total = await service.list_golden_records(test_tenant, page=1, page_size=2)
    assert total == 3
    assert len(records_p1) == 2
    records_p2, total = await service.list_golden_records(test_tenant, page=2, page_size=2)
    assert total == 3
    assert len(records_p2) == 1


@pytest.mark.asyncio
async def test_list_conflicts(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    await service.resolve_records(test_tenant, "balady", [{"cr_number": "CR-CONF", "name_ar": "First"}])
    await service.resolve_records(test_tenant, "hubspot", [{"cr_number": "CR-CONF", "name_ar": "Second"}])
    conflicts, total = await service.list_conflicts(test_tenant)
    assert total >= 1
    assert conflicts[0].status == "open"


@pytest.mark.asyncio
async def test_resolve_conflict_use_source_b(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    await service.resolve_records(test_tenant, "balady", [{"cr_number": "CR-RES", "name_ar": "ValueA"}])
    await service.resolve_records(test_tenant, "hubspot", [{"cr_number": "CR-RES", "name_ar": "ValueB"}])
    golden_repo = GoldenRecordRepository(db_session)
    golden = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-RES")
    assert golden.data["name_ar"]["value"] == "ValueA"
    conflicts, _ = await service.list_conflicts(test_tenant)
    conflict = [c for c in conflicts if c.golden_record_id == golden.id][0]
    resolved = await service.resolve_conflict(conflict_id=str(conflict.id), strategy="use_source_b", resolved_by=test_tenant)
    assert resolved.status == "resolved"
    golden_after = await golden_repo.get(uuid.UUID(str(golden.id)))
    assert golden_after.data["name_ar"]["value"] == "ValueB"


@pytest.mark.asyncio
async def test_resolve_conflict_merge(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    await service.resolve_records(test_tenant, "balady", [{"cr_number": "CR-MRG", "name_ar": "First"}])
    await service.resolve_records(test_tenant, "hubspot", [{"cr_number": "CR-MRG", "name_ar": "Second"}])
    golden_repo = GoldenRecordRepository(db_session)
    golden = await golden_repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-MRG")
    conflicts, _ = await service.list_conflicts(test_tenant)
    conflict = [c for c in conflicts if c.golden_record_id == golden.id][0]
    resolved = await service.resolve_conflict(conflict_id=str(conflict.id), strategy="merge", custom_value="Merged", resolved_by=test_tenant)
    assert resolved.status == "resolved"
    golden_after = await golden_repo.get(uuid.UUID(str(golden.id)))
    assert golden_after.data["name_ar"]["value"] == "Merged"
    assert golden_after.data["name_ar"]["source"] == "manual_merge"


@pytest.mark.asyncio
async def test_get_stats(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    stats = await service.get_stats(test_tenant)
    assert stats["total_golden_records"] == 0
    assert stats["open_conflicts"] == 0
    await service.resolve_records(test_tenant, "balady", [{"cr_number": "CR-STAT", "name_ar": "StatsCo"}])
    stats = await service.get_stats(test_tenant)
    assert stats["total_golden_records"] == 1
    await service.resolve_records(test_tenant, "hubspot", [{"cr_number": "CR-STAT", "name_ar": "Different"}])
    stats = await service.get_stats(test_tenant)
    assert stats["total_golden_records"] == 1
    assert stats["open_conflicts"] >= 1


@pytest.mark.asyncio
async def test_field_confidence_computation():
    service = EntityResolutionService.__new__(EntityResolutionService)
    assert service._compute_field_confidence("cr_number", "balady") == 1.0
    assert service._compute_field_confidence("name_ar", "balady") == 1.0
    assert service._compute_field_confidence("city", "balady") == 1.0
    assert service._compute_field_confidence("cr_number", "hubspot") == pytest.approx(0.45, rel=1e-6)
    assert service._compute_field_confidence("name_ar", "hubspot") == pytest.approx(0.35, rel=1e-6)
    assert service._compute_field_confidence("city", "hubspot") == pytest.approx(0.3, rel=1e-6)


@pytest.mark.asyncio
async def test_overall_confidence_computation():
    service = EntityResolutionService.__new__(EntityResolutionService)
    data = {"name_ar": {"confidence": 1.0}, "city": {"confidence": 0.8}, "phone": {"confidence": 0.6}}
    assert service._compute_overall_confidence(data) == pytest.approx(0.8, rel=1e-6)
    assert service._compute_overall_confidence({}) == 0.0