"""Notion company import uses source IDs, tenant RLS, and no synthetic CR identity."""

from __future__ import annotations

import uuid

import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.company.models import Company
from app.modules.identity.models import Tenant
from app.modules.notion_sync.service import NotionSyncService


@pytest.mark.asyncio
async def test_notion_import_is_idempotent_and_does_not_fabricate_cr(monkeypatch) -> None:
    test_url = make_url(settings.app_database_url).set(database="salesos_test")
    engine = create_async_engine(
        test_url, pool_pre_ping=True, connect_args={"command_timeout": 10}
    )
    async with engine.connect() as connection:
        outer = await connection.begin()
        assert await connection.scalar(text("SELECT current_database()")) == "salesos_test"
        role = await connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        assert role.one() == (False, False)
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        tenant_id = uuid.uuid4()
        try:
            session.add(
                Tenant(id=tenant_id, name="Notion Import Tenant", slug=f"notion-{uuid.uuid4()}")
            )
            await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)},
            )

            page = {
                "id": "notion-page-001",
                "properties": {
                    "Name": {"type": "title", "title": [{"plain_text": "Nasma"}]},
                    "Name AR": {
                        "type": "rich_text",
                        "rich_text": [{"plain_text": "شركة نسمة"}],
                    },
                    "Name EN": {
                        "type": "rich_text",
                        "rich_text": [{"plain_text": "Nasma Company"}],
                    },
                    "Website": {"type": "url", "url": "https://nasma.example"},
                },
            }

            def handler(request: httpx.Request) -> httpx.Response:
                assert request.url.path == "/v1/databases/db-1/query"
                assert request.headers["Notion-Version"] == NotionSyncService.NOTION_VERSION
                return httpx.Response(200, json={"has_more": False, "results": [page]})

            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                service = NotionSyncService(session, client=client)
                first = await service.import_companies(
                    database_id="db-1", token="test-token", tenant_id=str(tenant_id)
                )
                second = await service.import_companies(
                    database_id="db-1", token="test-token", tenant_id=str(tenant_id)
                )

            assert first["entities_imported"] == 1
            assert first["errors"] == []
            assert second["entities_imported"] == 0
            assert second["entities_skipped"] == 1

            company = await session.scalar(
                select(Company).where(
                    Company.tenant_id == tenant_id,
                    Company.extra_metadata["notion_page_id"].as_string() == "notion-page-001",
                )
            )
            assert company is not None
            assert company.name_ar == "شركة نسمة"
            assert company.name_en == "Nasma Company"
            assert company.cr_number is None
            assert company.extra_metadata == {
                "source": "notion",
                "notion_database_id": "db-1",
                "notion_page_id": "notion-page-001",
            }
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
