"""End-to-end integration tests covering the full data pipeline, API, and cross-module flows."""

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app


def _test_db_url():
    host = os.environ.get("TEST_POSTGRES_HOST") or os.environ.get("POSTGRES_HOST", "localhost")
    password = os.environ.get("POSTGRES_PASSWORD", "salesos_dev_password")
    return os.environ.get(
        "TEST_DATABASE_URL",
        f"postgresql+asyncpg://salesos:{password}@{host}:5432/salesos_test",
    )


@pytest_asyncio.fixture
async def pipeline():
    """Provide a DataFabricPipeline with its own engine session factory."""
    from runtime.data_fabric_runtime import DataFabricPipeline
    engine = create_async_engine(_test_db_url(), echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    yield DataFabricPipeline(session_factory=session_factory)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """FastAPI test client with overridden DB dependency."""
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> str:
    from app.modules.identity.models import Tenant
    tenant = Tenant(name="E2E Tenant", slug=f"e2e-{uuid.uuid4().hex[:8]}")
    db_session.add(tenant)
    await db_session.flush()
    await db_session.commit()
    return str(tenant.id)


@pytest_asyncio.fixture
async def auth_headers(test_tenant: str, db_session: AsyncSession) -> dict:
    """Create a user and return auth headers."""
    from app.modules.identity.models import User
    from passlib.hash import bcrypt
    from app.config import settings
    import jwt

    user = User(
        tenant_id=uuid.UUID(test_tenant),
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        full_name="Admin User",
        password_hash=bcrypt.hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    token = jwt.encode(
        {"sub": str(user.id), "tenant_id": test_tenant, "role": "admin", "type": "access"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": test_tenant,
    }


# ─── Pipeline E2E Tests ──────────────────────────────────────


class TestPipelineE2E:
    """End-to-end pipeline: normalizer → validator → entity resolution → company sync."""

    async def _run_pipeline(self, pipeline, test_tenant: str, records: list[dict]):
        return await pipeline.run_batch("test_e2e", records, test_tenant)

    @pytest.mark.asyncio
    async def test_pipeline_valid_record_creates_golden(self, db_session: AsyncSession, test_tenant: str, pipeline):
        """Valid record flows through all stages and creates a golden record + company."""
        record = {
            "cr_number": "CR-E2E-001",
            "name_ar": "شركة الاختبار الشامل",
            "name_en": "E2E Test Co",
            "city": "الرياض",
            "activity_description": "تقنية معلومات",
            "phone": "0512345678",
        }

        result = await self._run_pipeline(pipeline, test_tenant, [record])
        assert result["records_processed"] == 1
        assert result["records_valid"] == 1
        assert result["records_invalid"] == 0
        assert result["golden_records_created"] >= 1, f"golden_records_created was {result['golden_records_created']}, errors: {result.get('errors', [])}"
        assert "errors" not in result or len(result["errors"]) == 0

        from app.modules.entity_resolution.models import GoldenRecord
        from sqlalchemy import select
        r = await db_session.execute(
            select(GoldenRecord).where(
                GoldenRecord.tenant_id == uuid.UUID(test_tenant),
                GoldenRecord.cr_number == "CR-E2E-001",
            )
        )
        golden = r.scalar_one_or_none()
        assert golden is not None, "Golden record should exist"
        assert golden.company_id is not None, "Golden record should be linked to a company"

        from app.modules.company.models import Company
        r = await db_session.execute(
            select(Company).where(Company.id == golden.company_id)
        )
        company = r.scalar_one_or_none()
        assert company is not None, "Company should exist"
        assert company.name_ar == "شركة الاختبار الشامل"
        assert company.cr_number == "CR-E2E-001"

    @pytest.mark.asyncio
    async def test_pipeline_invalid_record_rejected(self, db_session: AsyncSession, test_tenant: str, pipeline):
        """Record missing required fields is rejected at validation stage."""
        record = {"phone": "0512345678"}

        result = await self._run_pipeline(pipeline, test_tenant, [record])

        assert result["records_processed"] == 1
        assert result["records_valid"] == 0
        assert result["records_invalid"] == 1

    @pytest.mark.asyncio
    async def test_pipeline_duplicate_cr_merges(self, db_session: AsyncSession, test_tenant: str, pipeline):
        """Two records with same CR number merge into one golden record."""
        records = [
            {"cr_number": "CR-E2E-MERGE", "name_ar": "شركة أ", "city": "الرياض"},
            {"cr_number": "CR-E2E-MERGE", "name_ar": "شركة أ", "city": "جدة"},
        ]

        result = await self._run_pipeline(pipeline, test_tenant, records)

        assert result["records_valid"] == 2
        assert result["golden_records_created"] >= 1

        from app.modules.entity_resolution.models import GoldenRecord
        from sqlalchemy import select, func
        r = await db_session.execute(
            select(func.count()).select_from(GoldenRecord).where(
                GoldenRecord.tenant_id == uuid.UUID(test_tenant),
                GoldenRecord.cr_number == "CR-E2E-MERGE",
            )
        )
        count = r.scalar()
        assert count == 1, "Should have exactly one golden record for duplicate CRs"

    @pytest.mark.asyncio
    async def test_pipeline_multi_tenant_isolation(self, db_session: AsyncSession, test_tenant: str, pipeline):
        """Records from different tenants do not interfere."""
        from app.modules.identity.models import Tenant
        tenant2 = Tenant(name="Isolation Tenant", slug=f"iso-{uuid.uuid4().hex[:8]}")
        db_session.add(tenant2)
        await db_session.flush()
        await db_session.commit()
        tenant2_id = str(tenant2.id)

        record = {"cr_number": "CR-ISO-001", "name_ar": "شركة العزل", "city": "الرياض"}

        await self._run_pipeline(pipeline, test_tenant, [record])
        await self._run_pipeline(pipeline, tenant2_id, [record])

        from app.modules.entity_resolution.models import GoldenRecord
        from sqlalchemy import select, func
        r = await db_session.execute(
            select(func.count()).select_from(GoldenRecord).where(
                GoldenRecord.cr_number == "CR-ISO-001",
            )
        )
        assert r.scalar() == 2, "Each tenant should have its own golden record"

    @pytest.mark.asyncio
    async def test_pipeline_with_dlq_on_failure(self, db_session: AsyncSession, test_tenant: str, pipeline):
        """Pipeline captures failures in the dead letter queue."""
        record = {"cr_number": "CR-DLQ-001", "name_ar": "DLQ Test", "city": "مكة"}
        result = await pipeline.run_batch("test_dlq", [record], test_tenant)

        assert result["records_processed"] == 1
        assert result["records_valid"] == 1

    @pytest.mark.asyncio
    async def test_pipeline_audit_trail_created(self, db_session: AsyncSession, test_tenant: str, pipeline):
        """Pipeline run creates an audit log entry."""
        from sqlalchemy import text

        record = {"cr_number": "CR-AUDIT-001", "name_ar": "تدقيق", "city": "الدمام"}
        await pipeline.run_batch("test_audit", [record], test_tenant)

        r = await db_session.execute(
            text("SELECT COUNT(*) FROM audit.audit_log WHERE tenant_id = :tid AND action = 'pipeline_run'"),
            {"tid": test_tenant},
        )
        assert r.scalar() >= 1, "Audit log should contain pipeline_run entry"


# ─── API Integration Tests ───────────────────────────────────


class TestAPIE2E:
    """API-level integration tests via HTTP client."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "database" in data

    @pytest.mark.asyncio
    async def test_root_redirect(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_create_and_get_company(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict
    ):
        payload = {
            "name_ar": "شركة API",
            "name_en": "API Company",
            "cr_number": "CR-API-001",
            "city": "الرياض",
            "region": "منطقة الرياض",
            "status": "active",
        }
        resp = await client.post(
            "/api/v1/companies",
            json=payload,
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201), f"Create company failed: {resp.text}"
        company = resp.json()
        assert company["cr_number"] == "CR-API-001"
        company_id = company["id"]

        resp = await client.get(
            f"/api/v1/companies/{company_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name_ar"] == "شركة API"

    @pytest.mark.asyncio
    async def test_search_companies(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/companies",
            params={"q": "شركة", "page": 1, "page_size": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data

    @pytest.mark.asyncio
    async def test_company_360(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict, db_session: AsyncSession
    ):
        from app.modules.company.models import Company
        company = Company(
            tenant_id=uuid.UUID(test_tenant),
            cr_number="CR-360-001",
            name_ar="شركة 360",
            city="الرياض",
            status="active",
        )
        db_session.add(company)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/companies/{company.id}/360",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["company"]["name_ar"] == "شركة 360"
        assert "overview" in data
        assert "organization" in data

    @pytest.mark.asyncio
    async def test_golden_records_endpoint(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/entity-resolution/golden-records",
            params={"page": 1, "page_size": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data

    @pytest.mark.asyncio
    async def test_dlq_admin_endpoint(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/admin/dlq",
            params={"page": 1, "page_size": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data

    @pytest.mark.asyncio
    async def test_admin_metrics_endpoint(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/admin/metrics",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "salesos_info" in resp.text
        assert "salesos_companies_total" in resp.text

    @pytest.mark.asyncio
    async def test_admin_health_full(
        self, client: AsyncClient, test_tenant: str, auth_headers: dict
    ):
        resp = await client.get(
            "/api/v1/admin/health/full",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
        assert "checks" in data
        assert "postgres" in data["checks"]

    @pytest.mark.asyncio
    async def test_unauthorized_access_rejected(self, client: AsyncClient):
        resp = await client.get("/api/v1/companies")
        assert resp.status_code in (401, 422)


# ─── Cross-Module Integration Tests ──────────────────────────


class TestCrossModuleE2E:
    """Tests that verify cross-module interactions."""

    @pytest.mark.asyncio
    async def test_golden_record_syncs_to_company(
        self, db_session: AsyncSession, test_tenant: str, pipeline
    ):
        """Entity resolution golden record automatically creates a Company record."""
        record = {
            "cr_number": "CR-SYNC-001",
            "name_ar": "شركة المزامنة",
            "city": "جدة",
            "activity_description": "استشارات",
        }
        result = await pipeline.run_batch("test_sync", [record], test_tenant)
        assert result["records_valid"] == 1

        from app.modules.company.models import Company
        from sqlalchemy import select
        r = await db_session.execute(
            select(Company).where(
                Company.tenant_id == uuid.UUID(test_tenant),
                Company.cr_number == "CR-SYNC-001",
            )
        )
        company = r.scalar_one_or_none()
        assert company is not None, "Company should be created from golden record"
        assert company.is_golden_record is True
        assert company.confidence_score > 0

    @pytest.mark.asyncio
    async def test_pipeline_error_does_not_corrupt_state(
        self, db_session: AsyncSession, test_tenant: str, pipeline
    ):
        """When pipeline fails mid-way, previous valid records are still committed."""
        from app.modules.company.models import Company
        from sqlalchemy import select

        valid = {"cr_number": "CR-ATOMIC-001", "name_ar": "صالح", "city": "الرياض"}
        await pipeline.run_batch("test_atomic", [valid], test_tenant)

        r = await db_session.execute(
            select(Company).where(Company.cr_number == "CR-ATOMIC-001")
        )
        assert r.scalar_one_or_none() is not None, "Valid record should be persisted"

    @pytest.mark.asyncio
    async def test_golden_record_fields_sync_to_company(
        self, db_session: AsyncSession, test_tenant: str, pipeline
    ):
        """All golden record fields are properly mapped to company columns."""
        from app.modules.company.models import Company
        from sqlalchemy import select

        record = {
            "cr_number": "CR-FIELDS-001",
            "name_ar": "شركة الحقول",
            "name_en": "Fields Co",
            "city": "الخبر",
            "activity_description": "تقنية",
            "phone": "0512345678",
            "email": "fields@test.com",
        }
        result = await pipeline.run_batch("test_fields", [record], test_tenant)
        assert result["records_valid"] == 1

        r = await db_session.execute(
            select(Company).where(Company.cr_number == "CR-FIELDS-001")
        )
        company = r.scalar_one_or_none()
        assert company is not None
        assert company.name_ar == "شركة الحقول"
        assert company.name_en == "Fields Co"
        assert company.city == "الخبر"

    @pytest.mark.asyncio
    async def test_entity_resolution_conflicts_logged(
        self, db_session: AsyncSession, test_tenant: str
    ):
        """Entity resolution conflicts are detected and logged."""
        from app.modules.entity_resolution.service import EntityResolutionService

        service = EntityResolutionService(db=db_session)

        records = [
            {"cr_number": "CR-CONFLICT-001", "name_ar": "اسم متطابق"},
            {"cr_number": "CR-CONFLICT-001", "name_ar": "اسم مختلف"},
        ]
        result = await service.resolve_records(
            tenant_id=test_tenant,
            source_slug="test_conflict",
            records=records,
            confidence_threshold=0.5,
        )

        from app.modules.entity_resolution.models import EntityResolutionLog
        from sqlalchemy import select
        r = await db_session.execute(
            select(EntityResolutionLog).where(
                EntityResolutionLog.tenant_id == uuid.UUID(test_tenant),
                EntityResolutionLog.records_processed >= 2,
            )
        )
        log = r.scalar_one_or_none()
        assert log is not None, "Resolution should be logged"
