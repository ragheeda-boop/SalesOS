"""Tests for Entity Resolution Repositories."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entity_resolution.models import (
    EntityResolutionConflict,
    EntityResolutionLog,
    GoldenRecord,
)
from app.modules.entity_resolution.repositories import (
    ConflictRepository,
    GoldenRecordRepository,
)


@pytest.mark.asyncio
async def test_golden_record_repo_create(db_session: AsyncSession, test_tenant: str):
    repo = GoldenRecordRepository(db_session)
    golden = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-REPO-01",
        data={"name_ar": {"value": "RepoTest", "source": "BALADY", "confidence": 1.0}},
        confidence_score=1.0,
        source_ids=["balady"],
        is_active=True,
    )
    await repo.save(golden)
    assert golden.id is not None

    fetched = await repo.get(golden.id)
    assert fetched.cr_number == "CR-REPO-01"
    assert fetched.data["name_ar"]["value"] == "RepoTest"


@pytest.mark.asyncio
async def test_golden_record_repo_get_by_cr_number(db_session: AsyncSession, test_tenant: str):
    repo = GoldenRecordRepository(db_session)
    golden = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-REPO-02",
        data={},
        confidence_score=0.0,
        source_ids=["balady"],
    )
    await repo.save(golden)

    found = await repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-REPO-02")
    assert found is not None
    assert found.id == golden.id

    not_found = await repo.get_by_cr_number(uuid.UUID(test_tenant), "CR-NONEXISTENT")
    assert not_found is None


@pytest.mark.asyncio
async def test_golden_record_repo_find_by_tenant(db_session: AsyncSession, test_tenant: str, test_tenant_2: str):
    repo = GoldenRecordRepository(db_session)
    for i in range(3):
        g = GoldenRecord(
            tenant_id=uuid.UUID(test_tenant),
            cr_number=f"CR-FBT-{i}",
            data={},
            confidence_score=0.5,
            source_ids=["balady"],
        )
        await repo.save(g)

    # Create one in another tenant
    g_other = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant_2),
        cr_number="CR-OTHER",
        data={},
        confidence_score=0.5,
        source_ids=["balady"],
    )
    await repo.save(g_other)

    records, total = await repo.find_by_tenant(uuid.UUID(test_tenant))
    assert total == 3
    assert len(records) == 3

    records_other, total_other = await repo.find_by_tenant(uuid.UUID(test_tenant_2))
    assert total_other == 1
    assert len(records_other) == 1


@pytest.mark.asyncio
async def test_golden_record_repo_count_by_tenant(db_session: AsyncSession, test_tenant: str):
    repo = GoldenRecordRepository(db_session)
    assert await repo.count_by_tenant(uuid.UUID(test_tenant)) == 0

    g = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-COUNT",
        data={},
        confidence_score=0.5,
        source_ids=["balady"],
    )
    await repo.save(g)
    assert await repo.count_by_tenant(uuid.UUID(test_tenant)) == 1


@pytest.mark.asyncio
async def test_golden_record_repo_find_by_confidence_range(db_session: AsyncSession, test_tenant: str):
    repo = GoldenRecordRepository(db_session)
    for i, conf in enumerate([0.3, 0.6, 0.9]):
        g = GoldenRecord(
            tenant_id=uuid.UUID(test_tenant),
            cr_number=f"CR-CONF-{i}",
            data={},
            confidence_score=conf,
            source_ids=["balady"],
        )
        await repo.save(g)

    results = await repo.find_by_confidence_range(uuid.UUID(test_tenant), 0.5, 1.0)
    assert len(results) == 2
    assert all(r.confidence_score >= 0.5 for r in results)


@pytest.mark.asyncio
async def test_golden_record_repo_delete(db_session: AsyncSession, test_tenant: str):
    repo = GoldenRecordRepository(db_session)
    g = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-DEL",
        data={},
        confidence_score=0.5,
        source_ids=["balady"],
    )
    await repo.save(g)
    g_id = g.id

    await repo.delete(g_id)
    with pytest.raises(Exception):
        await repo.get(g_id)


@pytest.mark.asyncio
async def test_conflict_repo_create(db_session: AsyncSession, test_tenant: str):
    # First create a golden record to reference
    golden_repo = GoldenRecordRepository(db_session)
    golden = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-CONFLICT",
        data={},
        confidence_score=0.5,
        source_ids=["balady"],
    )
    await golden_repo.save(golden)

    conflict_repo = ConflictRepository(db_session)
    conflict = EntityResolutionConflict(
        tenant_id=uuid.UUID(test_tenant),
        golden_record_id=golden.id,
        field_name="name_ar",
        source_a_value="Old Name",
        source_a_source="BALADY",
        source_b_value="New Name",
        source_b_source="HUBSPOT",
        status="open",
    )
    await conflict_repo.save(conflict)
    assert conflict.id is not None

    fetched = await conflict_repo.get(conflict.id)
    assert fetched.field_name == "name_ar"
    assert fetched.status == "open"


@pytest.mark.asyncio
async def test_conflict_repo_find_open_by_golden_record(db_session: AsyncSession, test_tenant: str):
    golden_repo = GoldenRecordRepository(db_session)
    golden = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-FOBGR",
        data={},
        confidence_score=0.5,
        source_ids=["balady"],
    )
    await golden_repo.save(golden)

    conflict_repo = ConflictRepository(db_session)
    for i in range(2):
        c = EntityResolutionConflict(
            tenant_id=uuid.UUID(test_tenant),
            golden_record_id=golden.id,
            field_name=f"field_{i}",
            source_a_value=f"A_{i}",
            source_a_source="BALADY",
            source_b_value=f"B_{i}",
            source_b_source="HUBSPOT",
            status="open",
        )
        await conflict_repo.save(c)

    open_conflicts = await conflict_repo.find_open_by_golden_record(golden.id)
    assert len(open_conflicts) == 2


@pytest.mark.asyncio
async def test_conflict_repo_count_open(db_session: AsyncSession, test_tenant: str):
    golden_repo = GoldenRecordRepository(db_session)
    golden = GoldenRecord(
        tenant_id=uuid.UUID(test_tenant),
        cr_number="CR-COUNT-CONF",
        data={},
        confidence_score=0.5,
        source_ids=["balady"],
    )
    await golden_repo.save(golden)

    conflict_repo = ConflictRepository(db_session)
    assert await conflict_repo.count_open(uuid.UUID(test_tenant)) == 0

    c = EntityResolutionConflict(
        tenant_id=uuid.UUID(test_tenant),
        golden_record_id=golden.id,
        field_name="name_ar",
        source_a_value="A",
        source_a_source="BALADY",
        source_b_value="B",
        source_b_source="HUBSPOT",
        status="open",
    )
    await conflict_repo.save(c)
    assert await conflict_repo.count_open(uuid.UUID(test_tenant)) == 1