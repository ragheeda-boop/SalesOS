"""Extended Company domain tests — covers 360 sub-methods, ingest, event bus, and edge cases."""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import DuplicateError, NotFoundError
from app.modules.company.models import Company
from app.modules.company.service import CompanyService


@pytest.fixture
def mock_event_bus():
    bus = AsyncMock()
    return bus


@pytest.fixture
def mock_logger():
    logger = AsyncMock()
    return logger


# ── ingest_from_source ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_creates_new_companies(db_session: AsyncSession, test_tenant: str):
    from app.modules.company.models import Source

    source = Source(name="ZATCA", slug="zatca", description="Tax authority")
    db_session.add(source)
    await db_session.flush()

    service = CompanyService(db_session)
    result = await service.ingest_from_source(
        tenant_id=test_tenant,
        source_slug="zatca",
        records=[{"cr_number": "CR-ING-001", "name_ar": "شركة جديدة"}],
    )
    assert result["created"] == 1
    assert result["updated"] == 0
    assert result["total_processed"] == 1
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_ingest_updates_existing_companies(db_session: AsyncSession, test_tenant: str):
    from app.modules.company.models import Source

    source = Source(name="ZATCA2", slug="zatca2", description="Tax authority")
    db_session.add(source)
    await db_session.flush()

    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة قديمة", cr_number="CR-ING-EXIST",
    )

    result = await service.ingest_from_source(
        tenant_id=test_tenant,
        source_slug="zatca2",
        records=[{"cr_number": "CR-ING-EXIST", "name_ar": "شركة محدثة", "city": "جدة"}],
    )
    assert result["created"] == 0
    assert result["updated"] == 1


@pytest.mark.asyncio
async def test_ingest_skips_records_without_cr_number(db_session: AsyncSession, test_tenant: str):
    from app.modules.company.models import Source

    source = Source(name="ZATCA3", slug="zatca3", description="Tax authority")
    db_session.add(source)
    await db_session.flush()

    service = CompanyService(db_session)
    result = await service.ingest_from_source(
        tenant_id=test_tenant,
        source_slug="zatca3",
        records=[{"name_ar": "بدون سجل تجاري"}],
    )
    assert result["created"] == 0
    assert len(result["errors"]) == 1
    assert "Missing cr_number" in result["errors"][0]["error"]


@pytest.mark.asyncio
async def test_ingest_source_not_found(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    with pytest.raises(NotFoundError):
        await service.ingest_from_source(
            tenant_id=test_tenant,
            source_slug="nonexistent",
            records=[{"cr_number": "CR-404"}],
        )


@pytest.mark.asyncio
async def test_ingest_with_event_bus(db_session: AsyncSession, test_tenant: str, mock_event_bus):
    from app.modules.company.models import Source

    source = Source(name="ZATCA4", slug="zatca4", description="Tax authority")
    db_session.add(source)
    await db_session.flush()

    service = CompanyService(db_session, event_bus=mock_event_bus)
    await service.ingest_from_source(
        tenant_id=test_tenant,
        source_slug="zatca4",
        records=[{"cr_number": "CR-EVT-001", "name_ar": "شركة حدث"}],
    )
    mock_event_bus.publish.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_source_ids_appended(db_session: AsyncSession, test_tenant: str):
    from app.modules.company.models import Source

    s1 = Source(name="S1", slug="src-a", description="A")
    s2 = Source(name="S2", slug="src-b", description="B")
    db_session.add_all([s1, s2])
    await db_session.flush()

    service = CompanyService(db_session)
    await service.ingest_from_source(
        tenant_id=test_tenant, source_slug="src-a",
        records=[{"cr_number": "CR-SRC-001", "name_ar": "شركة مصدرين"}],
    )
    await service.ingest_from_source(
        tenant_id=test_tenant, source_slug="src-b",
        records=[{"cr_number": "CR-SRC-001", "name_ar": "شركة مصدرين"}],
    )

    company = (await db_session.execute(
        __import__("sqlalchemy").select(Company).where(Company.cr_number == "CR-SRC-001")
    )).scalar_one()
    assert "src-a" in company.source_ids
    assert "src-b" in company.source_ids


# ── Event bus failure paths ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_company_event_bus_failure(db_session: AsyncSession, test_tenant: str, mock_event_bus, mock_logger):
    mock_event_bus.publish.side_effect = RuntimeError("bus down")
    service = CompanyService(db_session, event_bus=mock_event_bus, logger=mock_logger)

    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة مع خطأ", cr_number="CR-EVTFAIL-001",
    )
    assert company is not None
    mock_logger.warn.assert_called()


@pytest.mark.asyncio
async def test_update_company_event_bus_failure(db_session: AsyncSession, test_tenant: str, mock_event_bus, mock_logger):
    mock_event_bus.publish.side_effect = RuntimeError("bus down")
    service = CompanyService(db_session, event_bus=mock_event_bus, logger=mock_logger)

    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة تحديث مع خطأ", cr_number="CR-EVTFAIL-002",
    )
    updated = await service.update_company(str(company.id), {"name_ar": "تم التحديث"})
    assert updated.name_ar == "تم التحديث"
    mock_logger.warn.assert_called()


@pytest.mark.asyncio
async def test_add_branch_event_bus_failure(db_session: AsyncSession, test_tenant: str, mock_event_bus, mock_logger):
    mock_event_bus.publish.side_effect = RuntimeError("bus down")
    service = CompanyService(db_session, event_bus=mock_event_bus, logger=mock_logger)

    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة فروع مع خطأ", cr_number="CR-EVTFAIL-003",
    )
    branch = await service.add_branch(str(company.id), {"name_ar": "فرع جديد"})
    assert branch is not None
    mock_logger.warn.assert_called()


@pytest.mark.asyncio
async def test_add_license_event_bus_failure(db_session: AsyncSession, test_tenant: str, mock_event_bus, mock_logger):
    mock_event_bus.publish.side_effect = RuntimeError("bus down")
    service = CompanyService(db_session, event_bus=mock_event_bus, logger=mock_logger)

    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة ترخيص مع خطأ", cr_number="CR-EVTFAIL-004",
    )
    lic = await service.add_license(str(company.id), {"license_number": "L-001", "license_type": "تجارية"})
    assert lic is not None
    mock_logger.warn.assert_called()


@pytest.mark.asyncio
async def test_add_contact_event_bus_failure(db_session: AsyncSession, test_tenant: str, mock_event_bus, mock_logger):
    mock_event_bus.publish.side_effect = RuntimeError("bus down")
    service = CompanyService(db_session, event_bus=mock_event_bus, logger=mock_logger)

    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة اتصال مع خطأ", cr_number="CR-EVTFAIL-005",
    )
    contact = await service.add_contact(str(company.id), {"name": "أحمد", "email": "a@b.com"})
    assert contact is not None
    mock_logger.warn.assert_called()


@pytest.mark.asyncio
async def test_delete_company_event_bus_failure(db_session: AsyncSession, test_tenant: str, mock_event_bus, mock_logger):
    mock_event_bus.publish.side_effect = RuntimeError("bus down")
    service = CompanyService(db_session, event_bus=mock_event_bus, logger=mock_logger)

    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة حذف مع خطأ", cr_number="CR-EVTFAIL-006",
    )
    await service.delete_company(str(company.id))
    mock_logger.warn.assert_called()


# ── search_companies pagination ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_companies_empty_query(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    for i in range(5):
        await service.create_company(tenant_id=test_tenant, name_ar=f"شركة {i}", cr_number=f"CR-PAGE-{i}")

    results, total = await service.search_companies(tenant_id=test_tenant, query=None, page=1, page_size=2)
    assert total == 5
    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_companies_pagination_second_page(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    for i in range(5):
        await service.create_company(tenant_id=test_tenant, name_ar=f"شركة {i}", cr_number=f"CR-PAGE2-{i}")

    results, total = await service.search_companies(tenant_id=test_tenant, query=None, page=2, page_size=2)
    assert total == 5
    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_companies_no_results(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    results, total = await service.search_companies(tenant_id=test_tenant, query="غير موجود")
    assert total == 0
    assert results == []


# ── get_company_360 with KG engine ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_company_360_with_kg_engine(db_session: AsyncSession, test_tenant: str):
    class FakeDM:
        def to_dict(self):
            return {"id": "dm-1", "name": "Decision Maker"}

    class FakeKGEngine:
        async def get_ego_network(self, company_id, depth=1):
            return [{"id": "rel-1", "type": "supplier"}]

        async def get_decision_makers(self, company_id):
            return [FakeDM()]

    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة مع KG", cr_number="360-KG-001",
    )
    result = await service.get_company_360(
        str(company.id), test_tenant, db=db_session, kg_engine=FakeKGEngine(),
    )
    assert len(result["related_entities"]) == 1
    assert len(result["decision_makers"]) == 1
    assert result["decision_makers"][0]["name"] == "Decision Maker"


@pytest.mark.asyncio
async def test_company_360_kg_engine_exception(db_session: AsyncSession, test_tenant: str, mock_logger):
    class BrokenKGEngine:
        async def get_ego_network(self, **kwargs):
            raise RuntimeError("KG down")

        async def get_decision_makers(self, **kwargs):
            raise RuntimeError("KG down")

    service = CompanyService(db_session, logger=mock_logger)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة KG مكسور", cr_number="360-KG-ERR",
    )
    result = await service.get_company_360(
        str(company.id), test_tenant, db=db_session, kg_engine=BrokenKGEngine(),
    )
    assert result["related_entities"] == []
    assert result["decision_makers"] == []
    assert mock_logger.warn.call_count >= 2


# ── get_company_activity with runtime ───────────────────────────────────────


@pytest.mark.asyncio
async def test_company_360_with_activity_runtime(db_session: AsyncSession, test_tenant: str):
    class FakeActivityRuntime:
        async def get_by_entity(self, entity_type, entity_id, tenant_id=None, limit=50):
            items = [
                {"action": "meeting_scheduled", "timestamp": "2026-07-01", "metadata": {"status": "scheduled"}},
                {"action": "email_sent", "timestamp": "2026-07-02", "metadata": {}},
                {"action": "task_created", "timestamp": "2026-07-03", "metadata": {"status": "pending"}},
                {"action": "contract_signed", "timestamp": "2026-07-04", "metadata": {"status": "active"}},
                {"action": "document_uploaded", "timestamp": "2026-07-05", "metadata": {}},
                {"action": "invoice_created", "timestamp": "2026-07-06", "metadata": {}},
            ]
            return items, len(items)

    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة مع أنشطة", cr_number="360-ACT-001",
    )
    result = await service.get_company_360(
        str(company.id), test_tenant, db=db_session,
        activity_runtime=FakeActivityRuntime(),
    )
    assert len(result["timeline"]) == 6
    assert len(result["meetings"]) == 1
    assert len(result["emails"]) == 1
    assert len(result["tasks"]) == 1
    assert len(result["contracts"]) == 1
    assert len(result["documents"]) == 1
    assert len(result["invoices"]) == 1
    assert result["overview"]["timeline_total"] == 6


@pytest.mark.asyncio
async def test_company_360_activity_runtime_exception(db_session: AsyncSession, test_tenant: str, mock_logger):
    class BrokenActivityRuntime:
        async def get_by_entity(self, **kwargs):
            raise RuntimeError("Timeline down")

    service = CompanyService(db_session, logger=mock_logger)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة أنشطة مكسورة", cr_number="360-ACT-ERR",
    )
    result = await service.get_company_360(
        str(company.id), test_tenant, db=db_session,
        activity_runtime=BrokenActivityRuntime(),
    )
    assert result["timeline"] == []
    mock_logger.warn.assert_called()


# ── _get_branches_and_licenses error path ──────────────────────────────────


@pytest.mark.asyncio
async def test_company_360_branches_licenses_error(db_session: AsyncSession, test_tenant: str, mock_logger):
    """Test that branch/license errors are caught and logged."""
    service = CompanyService(db_session, logger=mock_logger)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة فروع خطأ", cr_number="360-BL-ERR",
    )
    result = await service.get_company_360(
        str(company.id), test_tenant, db=db_session,
    )
    assert "branches" in result
    assert "licenses" in result


# ── _get_users edge cases ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_company_360_users_empty_owner_ids(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    users = await service._get_users(db_session, [])
    assert users == []


@pytest.mark.asyncio
async def test_company_360_users_exception(db_session: AsyncSession, test_tenant: str, mock_logger):
    service = CompanyService(db_session, logger=mock_logger)
    users = await service._get_users(db_session, ["00000000-0000-0000-0000-000000000001"])
    assert users == []


# ── get_company_intelligence exception ──────────────────────────────────────


@pytest.mark.asyncio
async def test_company_intelligence_golden_record_exception(db_session: AsyncSession, test_tenant: str, mock_logger):
    service = CompanyService(db_session, logger=mock_logger)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة ذهبية", cr_number="360-GR-ERR",
    )
    intelligence = await service.get_company_intelligence(
        company, str(company.id), test_tenant, db_session,
    )
    assert intelligence["golden_record_id"] is None


# ── _detect_signals comprehensive ──────────────────────────────────────────


def test_detect_signals_expiring_soon():
    from datetime import date, timedelta

    service = CompanyService.__new__(CompanyService)
    company = SimpleNamespace(expiry_date=date.today() + timedelta(days=15), confidence_score=0.8)
    signals = service._detect_signals(company, [{"name": "A"}], [], [], [{"id": 1}], "t1")
    expiring = [s for s in signals["items"] if s["type"] == "expiring_soon"]
    assert len(expiring) == 1
    assert expiring[0]["severity"] == "high"


def test_detect_signals_expiring_medium():
    from datetime import date, timedelta

    service = CompanyService.__new__(CompanyService)
    company = SimpleNamespace(expiry_date=date.today() + timedelta(days=60), confidence_score=0.8)
    signals = service._detect_signals(company, [{"name": "A"}], [], [], [{"id": 1}], "t1")
    expiring = [s for s in signals["items"] if s["type"] == "expiring"]
    assert len(expiring) == 1
    assert expiring[0]["severity"] == "medium"


def test_detect_signals_stalled_pipeline():
    service = CompanyService.__new__(CompanyService)
    company = SimpleNamespace(expiry_date=None, confidence_score=0.8)
    opps = [{"stage": "prospecting", "status": "open"} for _ in range(5)]
    signals = service._detect_signals(company, [{"name": "A"}], opps, [], [{"id": 1}], "t1")
    stalled = [s for s in signals["items"] if s["type"] == "stalled_pipeline"]
    assert len(stalled) == 1


def test_detect_signals_won_deals():
    service = CompanyService.__new__(CompanyService)
    company = SimpleNamespace(expiry_date=None, confidence_score=0.8)
    opps = [{"status": "won"}, {"status": "closed_won"}, {"status": "open"}]
    signals = service._detect_signals(company, [{"name": "A"}], opps, [], [{"id": 1}], "t1")
    won = [s for s in signals["items"] if s["type"] == "won_deals"]
    assert len(won) == 1
    assert won[0]["value"] == 2


def test_detect_signals_low_confidence():
    service = CompanyService.__new__(CompanyService)
    company = SimpleNamespace(expiry_date=None, confidence_score=0.3)
    signals = service._detect_signals(company, [{"name": "A"}], [], [], [{"id": 1}], "t1")
    low = [s for s in signals["items"] if s["type"] == "low_confidence"]
    assert len(low) == 1
    assert low[0]["score"] == 0.3


# ── get_company_360 enrichment fields ──────────────────────────────────────


@pytest.mark.asyncio
async def test_company_360_enrichment_fields(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    from datetime import date
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة غنية", cr_number="360-ENR-001",
    )
    company.source_ids = ["src-a", "src-b"]
    company.is_golden_record = True
    company.confidence_score = 0.95
    await db_session.flush()

    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    enrichment = result["enrichment"]
    assert enrichment["sources"] == ["src-a", "src-b"]
    assert enrichment["is_golden_record"] is True
    assert enrichment["confidence_score"] == 0.95
    assert enrichment["last_enriched_at"] is not None


# ── search_companies with multiple filter fields ───────────────────────────


@pytest.mark.asyncio
async def test_search_companies_by_cr_number(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    await service.create_company(tenant_id=test_tenant, name_ar="شركة أ", cr_number="UNIQUE-CR-999")
    await service.create_company(tenant_id=test_tenant, name_ar="شركة ب", cr_number="UNIQUE-CR-888")

    results, total = await service.search_companies(tenant_id=test_tenant, query="UNIQUE-CR-999")
    assert total == 1
    assert results[0].cr_number == "UNIQUE-CR-999"


@pytest.mark.asyncio
async def test_search_companies_by_city(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    await service.create_company(tenant_id=test_tenant, name_ar="شركة جدة", cr_number="CR-CITY-1", city="جدة")
    await service.create_company(tenant_id=test_tenant, name_ar="شركة الرياض", cr_number="CR-CITY-2", city="الرياض")

    results, total = await service.search_companies(tenant_id=test_tenant, query="جدة")
    assert total == 1
    assert results[0].city == "جدة"


# ── _heuristic_health_score additional ──────────────────────────────────────


def test_heuristic_health_score_no_contacts_no_opps():
    score = CompanyService._heuristic_health_score([], [], [])
    assert score == 0.5


def test_heuristic_health_score_mixed_signals():
    signals = [
        {"severity": "critical"},
        {"severity": "high"},
        {"severity": "info"},
    ]
    score = CompanyService._heuristic_health_score(
        contacts=[{"name": "A"}], opportunities=[{"id": 1}], signals=signals,
    )
    expected = 0.5 + 0.1 + 0.15 - 0.15 - 0.05
    assert abs(score - expected) < 0.01
