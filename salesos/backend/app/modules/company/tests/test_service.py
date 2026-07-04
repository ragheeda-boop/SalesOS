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
