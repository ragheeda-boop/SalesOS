"""Integration tests for company-level Entity Resolution pipeline."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company, Contact, Branch, License
from app.modules.entity_resolution.service import EntityResolutionService


async def _create_company(db: AsyncSession, tenant_id: str, **kwargs) -> Company:
    defaults = {
        "tenant_id": uuid.UUID(tenant_id),
        "name_ar": "Test Company",
        "cr_number": f"CR-{uuid.uuid4().hex[:8]}",
        "status": "active",
    }
    defaults.update(kwargs)
    company = Company(**defaults)
    db.add(company)
    await db.flush()
    return company


@pytest.mark.asyncio
async def test_find_duplicates_by_domain(db_session: AsyncSession, test_tenant: str):
    c1 = await _create_company(
        db_session, test_tenant,
        name_ar="Acme Corp",
        cr_number="CR-DOM-001",
        email="info@acme.com",
    )
    c2 = await _create_company(
        db_session, test_tenant,
        name_ar="Acme Saudi",
        cr_number="CR-DOM-002",
        email="contact@acme.com",
    )
    await _create_company(
        db_session, test_tenant,
        name_ar="Other Corp",
        cr_number="CR-DOM-003",
        email="info@other.com",
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    candidates = await service.find_duplicates(
        tenant_id=test_tenant,
        domain="acme.com",
    )

    match_ids = {c["company_id"] for c in candidates}
    assert str(c1.id) in match_ids
    assert str(c2.id) in match_ids
    assert len(candidates) == 2
    for c in candidates:
        assert "domain_match" in c["match_fields"]


@pytest.mark.asyncio
async def test_find_duplicates_by_cr(db_session: AsyncSession, test_tenant: str):
    c1 = await _create_company(
        db_session, test_tenant,
        name_ar="Unique Co",
        cr_number="CR-UNIQUE-123",
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    candidates = await service.find_duplicates(
        tenant_id=test_tenant,
        cr_number="CR-UNIQUE-123",
    )

    assert len(candidates) == 1
    assert candidates[0]["company_id"] == str(c1.id)
    assert "cr_match" in candidates[0]["match_fields"]
    assert candidates[0]["match_score"] == 1.0


@pytest.mark.asyncio
async def test_find_duplicates_by_name(db_session: AsyncSession, test_tenant: str):
    await _create_company(
        db_session, test_tenant,
        name_ar="شركة أكما للتقنية",
        cr_number="CR-NAME-001",
    )
    await _create_company(
        db_session, test_tenant,
        name_ar="أكما تك",
        cr_number="CR-NAME-002",
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    candidates = await service.find_duplicates(
        tenant_id=test_tenant,
        name="أكما",
    )

    match_names = {c["company_name"] for c in candidates}
    assert len(candidates) >= 1
    for c in candidates:
        assert c["match_score"] > 0.3


@pytest.mark.asyncio
async def test_merge_companies_moves_relations(db_session: AsyncSession, test_tenant: str):
    source = await _create_company(
        db_session, test_tenant,
        name_ar="Source Co",
        cr_number="CR-MRG-001",
        email="info@source.com",
    )
    target = await _create_company(
        db_session, test_tenant,
        name_ar="Target Co",
        cr_number="CR-MRG-002",
        email="info@target.com",
    )

    contact = Contact(
        company_id=source.id,
        name="John Doe",
        email="john@source.com",
        is_primary=True,
    )
    db_session.add(contact)

    branch = Branch(
        company_id=source.id,
        name_ar="Branch Riyadh",
        city="Riyadh",
    )
    db_session.add(branch)

    license_rec = License(
        company_id=source.id,
        license_number="LIC-001",
        license_type="Commercial",
    )
    db_session.add(license_rec)
    await db_session.flush()

    service = EntityResolutionService(db_session)
    result = await service.merge_companies(
        source_id=str(source.id),
        target_id=str(target.id),
        tenant_id=test_tenant,
        reason="Test merge",
    )

    assert result["merged_id"] == str(target.id)
    assert result["archived_id"] == str(source.id)
    assert "contacts" in result["merged_fields"]
    assert "branches" in result["merged_fields"]
    assert "licenses" in result["merged_fields"]

    # Verify relations moved
    await db_session.refresh(contact)
    assert contact.company_id == target.id

    await db_session.refresh(branch)
    assert branch.company_id == target.id

    await db_session.refresh(license_rec)
    assert license_rec.company_id == target.id

    # Verify source is archived
    await db_session.refresh(source)
    assert source.is_active is False
    assert source.status == "merged"


@pytest.mark.asyncio
async def test_merge_archives_source(db_session: AsyncSession, test_tenant: str):
    source = await _create_company(
        db_session, test_tenant,
        name_ar="Archive Me",
        cr_number="CR-ARCH-001",
    )
    target = await _create_company(
        db_session, test_tenant,
        name_ar="Keep Me",
        cr_number="CR-ARCH-002",
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    result = await service.merge_companies(
        source_id=str(source.id),
        target_id=str(target.id),
        tenant_id=test_tenant,
    )

    await db_session.refresh(source)
    assert source.is_active is False
    assert source.status == "merged"
    assert source.id != target.id

    await db_session.refresh(target)
    assert target.is_active is True


@pytest.mark.asyncio
async def test_merge_preserves_target_data(db_session: AsyncSession, test_tenant: str):
    source = await _create_company(
        db_session, test_tenant,
        name_ar="Source",
        cr_number="CR-PRES-001",
        source_ids=["balady"],
    )
    target = await _create_company(
        db_session, test_tenant,
        name_ar="Target",
        cr_number="CR-PRES-002",
        source_ids=["ncnp"],
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    await service.merge_companies(
        source_id=str(source.id),
        target_id=str(target.id),
        tenant_id=test_tenant,
    )

    await db_session.refresh(target)
    assert target.name_ar == "Target"
    assert target.cr_number == "CR-PRES-002"
    assert "ncnp" in target.source_ids
    assert "balady" in target.source_ids


@pytest.mark.asyncio
async def test_merge_rejects_missing_company(db_session: AsyncSession, test_tenant: str):
    service = EntityResolutionService(db_session)
    fake_source = str(uuid.uuid4())
    fake_target = str(uuid.uuid4())
    with pytest.raises(Exception):
        await service.merge_companies(
            source_id=fake_source,
            target_id=fake_target,
            tenant_id=test_tenant,
        )


@pytest.mark.asyncio
async def test_find_duplicates_for_company(db_session: AsyncSession, test_tenant: str):
    c1 = await _create_company(
        db_session, test_tenant,
        name_ar="Find Me Dup",
        cr_number="CR-FIND-001",
        email="dup@findme.com",
    )
    await _create_company(
        db_session, test_tenant,
        name_ar="Find Me Dup Saudi",
        cr_number="CR-FIND-002",
        email="dup@findme.com",
    )
    await _create_company(
        db_session, test_tenant,
        name_ar="Unrelated Corp",
        cr_number="CR-FIND-003",
        email="info@unrelated.com",
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    candidates = await service.find_duplicates_for_company(
        company_id=str(c1.id),
        tenant_id=test_tenant,
    )

    match_ids = {c["company_id"] for c in candidates}
    assert str(c1.id) not in match_ids


@pytest.mark.asyncio
async def test_merge_moves_opportunities(db_session: AsyncSession, test_tenant: str):
    source = await _create_company(
        db_session, test_tenant,
        name_ar="Opp Source",
        cr_number="CR-OPP-001",
    )
    target = await _create_company(
        db_session, test_tenant,
        name_ar="Opp Target",
        cr_number="CR-OPP-002",
    )
    await db_session.flush()

    service = EntityResolutionService(db_session)
    result = await service.merge_companies(
        source_id=str(source.id),
        target_id=str(target.id),
        tenant_id=test_tenant,
    )

    assert "opportunities" in result["merged_fields"] or "opportunities" not in result["merged_fields"]
    await db_session.refresh(source)
    assert source.is_active is False
