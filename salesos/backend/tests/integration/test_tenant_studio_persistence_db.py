"""PostgreSQL persistence and forced tenant-RLS proof for AI Studio documents."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.identity.models import Tenant
from app.modules.tenant_studio.postgres_store import PostgresTenantStudioStore


@pytest.mark.asyncio
async def test_prompt_and_policy_documents_persist_with_tenant_rls() -> None:
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
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        try:
            session.add_all(
                [
                    Tenant(id=tenant_a, name="Studio Tenant A", slug=f"studio-a-{uuid.uuid4()}"),
                    Tenant(id=tenant_b, name="Studio Tenant B", slug=f"studio-b-{uuid.uuid4()}"),
                ]
            )
            await session.flush()
            store = PostgresTenantStudioStore(session)
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a)},
            )

            prompt = {
                "id": "prompt-a",
                "tenant_id": str(tenant_a),
                "key": "discovery-summary",
                "active_version": "1.0.0",
                "versions": [{"version": "1.0.0", "template": "Summarize {{account}}"}],
                "schema_version": 1,
            }
            policy = {
                "id": "policy-a",
                "tenant_id": str(tenant_a),
                "name": "Default policy",
                "guardrails": {"allow_external_data": False},
                "data_class_rules": [],
                "schema_version": 1,
            }
            assert await store.create(
                tenant_id=str(tenant_a),
                document_type="prompt_library",
                document_key="prompt-a",
                logical_key="discovery-summary",
                payload=prompt,
            ) == prompt
            assert await store.create(
                tenant_id=str(tenant_a),
                document_type="ai_policies",
                document_key="policy-a",
                payload=policy,
            ) == policy

            updated_prompt = {**prompt, "active_version": "1.1.0", "schema_version": 2}
            assert await store.replace_if_version(
                tenant_id=str(tenant_a),
                document_type="prompt_library",
                document_key="prompt-a",
                payload=updated_prompt,
                expected_schema_version=1,
                logical_key="discovery-summary",
            ) == updated_prompt
            assert await store.replace_if_version(
                tenant_id=str(tenant_a),
                document_type="prompt_library",
                document_key="prompt-a",
                payload=prompt,
                expected_schema_version=1,
            ) is None

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b)},
            )
            assert await store.get(
                tenant_id=str(tenant_a),
                document_type="prompt_library",
                document_key="prompt-a",
            ) is None
            assert await store.list_for_tenant(
                tenant_id=str(tenant_a), document_type="ai_policies"
            ) == []
            assert await store.delete(
                tenant_id=str(tenant_a),
                document_type="prompt_library",
                document_key="prompt-a",
            ) is False

            assert await store.create(
                tenant_id=str(tenant_b),
                document_type="prompt_library",
                document_key="prompt-a",
                logical_key="discovery-summary",
                payload={**prompt, "tenant_id": str(tenant_b)},
            ) is not None
            assert await store.list_for_tenant(
                tenant_id=str(tenant_b), document_type="prompt_library"
            ) == [{**prompt, "tenant_id": str(tenant_b)}]
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
