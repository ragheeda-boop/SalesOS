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
    # New 360 sections
    assert "crm" in result
    assert result["crm"]["deals_total"] == 0
    assert result["crm"]["contacts_total"] == 0
    assert "timeline" in result
    assert result["timeline"]["count"] == 0
    assert "enrichment" in result
    assert result["enrichment"]["firmographics"]["industry"] == "تقنية"
    assert "entity_resolution" in result
    assert result["entity_resolution"]["is_golden_record"] is True
    assert "knowledge_graph" in result


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


@pytest.mark.asyncio
async def test_company_360_crm_section(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة CRM", cr_number="CRM-001",
    )
    cid = str(company.id)
    await service.add_contact(cid, {"name": "اتصال 1", "email": "c1@test.com"})
    await service.add_contact(cid, {"name": "اتصال 2", "email": "c2@test.com"})

    result = await service.get_company_360(cid, test_tenant, db=db_session)
    assert result["crm"]["contacts_total"] == 2
    assert len(result["crm"]["contacts"]) == 2
    assert result["crm"]["deals_total"] == 0
    assert result["crm"]["deals_value"] == 0.0


@pytest.mark.asyncio
async def test_company_360_entity_resolution_section(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة ER", cr_number="ER-001",
    )
    company.is_golden_record = True
    company.confidence_score = 0.95
    await db_session.flush()

    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    assert result["entity_resolution"]["is_golden_record"] is True
    assert result["entity_resolution"]["confidence_score"] == 0.95
    assert result["entity_resolution"]["source_count"] == 0


@pytest.mark.asyncio
async def test_company_360_enrichment_firmographics(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    from datetime import date
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة Firmo", cr_number="FIRMO-001",
        city="الرياض", region="Riyadh",
    )
    company.industry = "تقنية المعلومات"
    company.isic_code = "6201"
    company.isic_description = "برمجة الحاسوب"
    company.legal_form = "شركة مساهمة"
    company.employees_count = 150
    company.capital = 5000000.0
    company.incorporation_date = date(2020, 1, 15)
    company.activity_description = "تطوير البرمجيات"
    company.activity_code = "620101"
    company.source_ids = ["balady", "taqeem"]
    await db_session.flush()

    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    f = result["enrichment"]["firmographics"]
    assert f["industry"] == "تقنية المعلومات"
    assert f["isic_code"] == "6201"
    assert f["legal_form"] == "شركة مساهمة"
    assert f["employees_count"] == 150
    assert f["capital"] == 5000000.0
    assert f["city"] == "الرياض"
    assert result["enrichment"]["sources"] == ["balady", "taqeem"]


@pytest.mark.asyncio
async def test_company_360_knowledge_graph_empty(db_session: AsyncSession, test_tenant: str):
    service = CompanyService(db_session)
    company = await service.create_company(
        tenant_id=test_tenant, name_ar="شركة KG", cr_number="KG-001",
    )
    result = await service.get_company_360(str(company.id), test_tenant, db=db_session)
    assert result["knowledge_graph"]["relationships"] == []
    assert result["knowledge_graph"]["competitors"] == []
    assert result["knowledge_graph"]["partners"] == []
    assert result["knowledge_graph"]["hierarchy"]["parent_company"] is None


# ── B-3 Timeline Filter Tests ──────────────────────────────────────────


def _make_timeline_entry(session, entity_type, entity_id, event_type, created_at, domain=None, actor=None, tenant_id=None):
    from sqlalchemy import text as sa_text
    from datetime import timezone
    import uuid
    data = {"domain": domain} if domain else {}
    session.execute(
        sa_text("""
            INSERT INTO timeline_entries (id, entity_type, entity_id, event_type, data, actor, tenant_id, created_at)
            VALUES (:id, :et, :eid, :evt, :data, :actor, :tid, :ca)
        """),
        {
            "id": str(uuid.uuid4()),
            "et": entity_type, "eid": entity_id,
            "evt": event_type, "data": data,
            "actor": actor or "test", "tid": tenant_id or "test",
            "ca": created_at,
        },
    )


@pytest.mark.asyncio
async def test_timeline_runtime_get_timeline_with_domain(db_session: AsyncSession):
    from runtime.timeline_runtime import TimelineRuntime
    from datetime import datetime, timezone

    async def session_factory():
        return db_session

    tl = TimelineRuntime(session_factory=session_factory)
    now = datetime.now(timezone.utc)

    await tl.record("company", "comp-1", "email.sent", {"domain": "crm", "subject": "Hello"}, tenant_id="t1")
    await tl.record("company", "comp-1", "email.opened", {"domain": "crm", "subject": "Hello"}, tenant_id="t1")
    await tl.record("company", "comp-1", "enrich.completed", {"domain": "enrichment", "source": "balady"}, tenant_id="t1")
    await tl.record("company", "comp-1", "meeting.held", {"domain": "crm", "title": "QBR"}, tenant_id="t1")

    # Filter by domain
    crm_events, total = await tl.get_timeline("company", "comp-1", domain="crm")
    assert total == 3
    assert len(crm_events) == 3

    enrich_events, total2 = await tl.get_timeline("company", "comp-1", domain="enrichment")
    assert total2 == 1
    assert len(enrich_events) == 1


@pytest.mark.asyncio
async def test_timeline_runtime_filter_by_event_type(db_session: AsyncSession):
    from runtime.timeline_runtime import TimelineRuntime
    from datetime import datetime, timezone

    async def session_factory():
        return db_session

    tl = TimelineRuntime(session_factory=session_factory)
    await tl.record("company", "comp-2", "email.sent", {"domain": "crm"}, tenant_id="t1")
    await tl.record("company", "comp-2", "meeting.held", {"domain": "crm"}, tenant_id="t1")
    await tl.record("company", "comp-2", "call.held", {"domain": "crm"}, tenant_id="t1")

    events, total = await tl.get_timeline("company", "comp-2", event_types=["email.sent", "meeting.held"])
    assert total == 2
    assert len(events) == 2


@pytest.mark.asyncio
async def test_timeline_runtime_keyset_cursor(db_session: AsyncSession):
    from runtime.timeline_runtime import TimelineRuntime
    from datetime import datetime, timezone
    import json

    async def session_factory():
        return db_session

    tl = TimelineRuntime(session_factory=session_factory)
    for i in range(5):
        await tl.record("company", "comp-3", f"event.{i}", {"domain": "crm"}, tenant_id="t1")

    page1, total = await tl.get_timeline("company", "comp-3", limit=2)
    assert total == 5
    assert len(page1) == 2

    last = page1[-1]
    cursor = json.dumps({"created_at": last.get("created_at"), "id": str(last.get("id", ""))})
    page2, total2 = await tl.get_timeline("company", "comp-3", limit=2, cursor=cursor)
    assert total2 == 5
    assert len(page2) == 2


# ── B-2 Knowledge Graph Insights Tests ─────────────────────────────────


@pytest.mark.asyncio
async def test_kg_engine_get_company_insights_basic(db_session: AsyncSession, test_tenant: str):
    from runtime.knowledge_graph_runtime import KnowledgeGraphEngine, EdgeType
    from sqlalchemy import text as sa_text

    async def session_factory():
        return db_session

    kg = KnowledgeGraphEngine(session_factory=session_factory, logger=None)
    kg.metrics.neo4j_available = False

    # Create test companies
    import uuid
    c1 = str(uuid.uuid4())
    c2 = str(uuid.uuid4())
    c3 = str(uuid.uuid4())

    for cid, name_ar, name_en, industry, city in [
        (c1, "شركة أ", "Company A", "تقنية", "الرياض"),
        (c2, "شركة ب", "Company B", "تقنية", "الرياض"),
        (c3, "شركة ج", "Company C", "مقاولات", "جدة"),
    ]:
        await db_session.execute(
            sa_text("""
                INSERT INTO companies (id, tenant_id, name_ar, name_en, industry, city, is_active)
                VALUES (:id, :tid, :name_ar, :name_en, :industry, :city, true)
            """),
            {"id": cid, "tid": test_tenant, "name_ar": name_ar, "name_en": name_en, "industry": industry, "city": city},
        )
    await db_session.commit()

    # Create competitor edges
    await kg._create_edge_sql(c1, c2, EdgeType.COMPETITOR_OF, {"reason": "same_industry"})

    insights = await kg.get_company_insights(c1, test_tenant)
    assert insights["company_id"] == c1
    assert len(insights["competitors"]["direct"]) == 1
    assert len(insights["competitors"]["indirect"]) >= 0
    assert insights["competitors"]["direct"][0]["name_en"] == "Company B"
    assert insights["market_position"]["direct_competitors"] == 1
    assert insights["market_position"]["total_companies_in_industry"] >= 1
    assert "competitive_intensity" in insights["relationship_strength_scores"]
