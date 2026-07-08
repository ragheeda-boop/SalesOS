import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.modules.company.models import Company
from app.modules.company.service import CompanyService


@pytest.mark.asyncio
async def test_create_company(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)

    company = await service.create_company(
        tenant_id=test_tenant,
        name_ar="شركة اختبار",
        name_en="Test Company",
        cr_number="1234567890",
        city="الرياض",
        region="Riyadh",
    )
    assert company.name_ar == "شركة اختبار"
    assert company.cr_number == "1234567890"
    assert company.city == "الرياض"
    assert company.status == "active"


@pytest.mark.asyncio
async def test_create_duplicate_company(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)

    await service.create_company(
        tenant_id=test_tenant,
        name_ar="الشركة الأولى",
        cr_number="CR-001",
    )
    with pytest.raises(DuplicateError):
        await service.create_company(
            tenant_id=test_tenant,
            name_ar="الشركة الثانية",
            cr_number="CR-001",
        )


@pytest.mark.asyncio
async def test_search_companies(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)

    await service.create_company(tenant_id=test_tenant, name_ar="شركة الأمل", cr_number="CR-100")
    await service.create_company(tenant_id=test_tenant, name_ar="شركة النور", cr_number="CR-200")
    await service.create_company(tenant_id=test_tenant, name_ar="مؤسسة السلام", cr_number="CR-300")

    results, total = await service.search_companies(
        tenant_id=test_tenant, query="شركة", page=1, page_size=10
    )
    assert total == 2
    assert len(results) == 2


@pytest.mark.asyncio
async def test_get_company_not_found(db_session: AsyncSession):
    service = CompanyService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_company("00000000-0000-0000-0000-000000000000")


@pytest.mark.asyncio
async def test_update_company(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)

    company = await service.create_company(
        tenant_id=test_tenant,
        name_ar="شركة التحديث",
        cr_number="CR-400",
    )
    updated = await service.update_company(
        str(company.id),
        {"name_ar": "شركة التحديث المعدلة", "status": "inactive"},
    )
    assert updated.name_ar == "شركة التحديث المعدلة"
    assert updated.status == "inactive"


@pytest.mark.asyncio
async def test_add_branch(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)

    company = await service.create_company(tenant_id=test_tenant, name_ar="شركة الفروع", cr_number="CR-500")
    branch = await service.add_branch(
        str(company.id),
        {"name_ar": "فرع الرياض", "city": "الرياض", "phone": "0112345678"},
    )
    assert branch.name_ar == "فرع الرياض"
    assert branch.company_id == company.id


@pytest.mark.asyncio
async def test_add_contact(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)

    company = await service.create_company(tenant_id=test_tenant, name_ar="شركة الاتصالات", cr_number="CR-600")
    contact = await service.add_contact(
        str(company.id),
        {"name": "أحمد محمد", "email": "ahmed@example.com", "position": "مدير مبيعات"},
    )
    assert contact.name == "أحمد محمد"
    assert contact.email == "ahmed@example.com"


# ── Company 360 Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_company_360_basic(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    from datetime import date
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة 360", cr_number="360-001",
        city="جدة",
    )
    company.industry = "تقنية"
    company.isic_code = "6201"
    company.is_golden_record = True
    company.confidence_score = 0.92
    await db_session.flush()

    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    assert result["company"].name_ar == "شركة 360"
    assert result["company"].industry == "تقنية"
    assert result["company"].is_golden_record is True
    assert result["company"].confidence_score == 0.92
    assert result["overview"]["total_contacts"] == 0
    assert result["overview"]["total_opportunities"] == 0
    assert result["overview"]["contacts_page"] == 1
    assert result["overview"]["contacts_total"] == 0
    assert result["overview"]["opportunities_page"] == 1
    assert result["overview"]["opportunities_total"] == 0
    assert result["overview"]["timeline_page"] == 1
    assert result["overview"]["timeline_total"] == 0
    assert "signals" in result
    assert len(result["contacts"]) == 0
    assert len(result["branches"]) == 0
    assert len(result["licenses"]) == 0


@pytest.mark.asyncio
async def test_company_360_with_contacts_and_branches(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة متكاملة", cr_number="360-002",
    )
    cid = str(company.id)
    await service.add_branch(cid, {"name_ar": "فرع الرياض", "city": "الرياض"})
    await service.add_branch(cid, {"name_ar": "فرع جدة", "city": "جدة"})
    await service.add_contact(cid, {"name": "أحمد", "email": "a@test.com", "position": "مدير"})
    await service.add_contact(cid, {"name": "سارة", "email": "s@test.com", "position": "محلل"})

    result = await service.get_company_360(cid, test_tenant, db=db_session)
    assert len(result["branches"]) == 2
    assert len(result["contacts"]) == 2
    assert result["overview"]["total_contacts"] == 2
    assert result["overview"]["contacts_total"] == 2
    assert result["contact_count"] == 2
    assert result["contacts_total"] == 2


@pytest.mark.asyncio
async def test_company_360_signals_no_contacts(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة بدون جهات اتصال", cr_number="360-003",
    )
    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    signals = result["signals"]
    assert signals["total"] >= 1
    no_contact_signals = [s for s in signals["items"] if s["type"] == "no_contacts"]
    assert len(no_contact_signals) == 1


@pytest.mark.asyncio
async def test_company_360_signals_expired(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    from datetime import date, timedelta
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة منتهية", cr_number="360-004",
    )
    company.expiry_date = date.today() - timedelta(days=30)
    await db_session.flush()

    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    signals = result["signals"]
    expired = [s for s in signals["items"] if s["type"] == "expired"]
    assert len(expired) == 1
    assert expired[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_company_360_signals_no_branches(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة بلا فروع", cr_number="360-005",
        city="جدة",
    )
    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    signals = result["signals"]
    no_branches = [s for s in signals["items"] if s["type"] == "no_branches"]
    assert len(no_branches) == 1
    assert no_branches[0]["severity"] == "info"


@pytest.mark.asyncio
async def test_company_360_signals_low_data_quality(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة", cr_number="CR-LOW",
    )
    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    signals = result["signals"]
    low_dq = [s for s in signals["items"] if s["type"] == "low_data_quality"]
    assert len(low_dq) == 1
    assert low_dq[0]["severity"] == "info"
    assert low_dq[0]["score"] < 50.0


@pytest.mark.asyncio
async def test_company_360_pagination(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة الباجينيشن", cr_number="360-006",
    )
    cid = str(company.id)
    for i in range(5):
        await service.add_contact(cid, {"name": f"جهة اتصال {i}", "email": f"c{i}@test.com"})

    result = await service.get_company_360(cid, test_tenant, db=db_session, page=1, page_size=2)
    assert len(result["contacts"]) == 2
    assert result["overview"]["contacts_total"] == 5
    assert result["overview"]["contacts_page"] == 1

    result_page2 = await service.get_company_360(cid, test_tenant, db=db_session, page=2, page_size=2)
    assert len(result_page2["contacts"]) == 2
    assert result_page2["overview"]["contacts_total"] == 5
    assert result_page2["overview"]["contacts_page"] == 2


@pytest.mark.asyncio
async def test_company_360_not_found(db_session: AsyncSession):
    service = CompanyService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_company_360(
            "00000000-0000-0000-0000-000000000000",
            "00000000-0000-0000-0000-000000000001",
            db=db_session,
        )
