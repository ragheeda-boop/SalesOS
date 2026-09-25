"""Encrypted memory persistence, opt-out deletion, and forced tenant RLS proof."""

from __future__ import annotations

import uuid

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.modules.identity.models import Tenant
from app.modules.tenant_studio.ai_memory import AiMemoryError
from app.modules.tenant_studio.postgres_ai_memory_store import PostgresAiMemoryStore


@pytest.mark.asyncio
async def test_memory_is_encrypted_persistent_tenant_scoped_and_deleted_on_opt_out(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        settings, "ai_memory_encryption_key", Fernet.generate_key().decode("ascii")
    )
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
                    Tenant(id=tenant_a, name="Memory Tenant A", slug=f"memory-a-{uuid.uuid4()}"),
                    Tenant(id=tenant_b, name="Memory Tenant B", slug=f"memory-b-{uuid.uuid4()}"),
                ]
            )
            await session.flush()
            store = PostgresAiMemoryStore(session)

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a)},
            )
            disabled = await store.get_settings(tenant_id=str(tenant_a))
            assert disabled.enabled is False
            with pytest.raises(AiMemoryError, match="opt-in"):
                await store.append_turn(
                    tenant_id=str(tenant_a),
                    conversation_id="demo",
                    role="user",
                    content="sensitive turn",
                )

            enabled = await store.set_settings(
                tenant_id=str(tenant_a), enabled=True, max_turns=2, retention_hours=1
            )
            assert enabled.enabled is True
            await store.append_turn(
                tenant_id=str(tenant_a),
                conversation_id="demo",
                role="user",
                content="sensitive first turn",
            )
            saved = await store.append_turn(
                tenant_id=str(tenant_a),
                conversation_id="demo",
                role="assistant",
                content="second turn",
            )
            await store.append_turn(
                tenant_id=str(tenant_a),
                conversation_id="demo",
                role="user",
                content="third turn replaces oldest",
            )
            assert [turn.content for turn in saved.turns] == [
                "sensitive first turn",
                "second turn",
            ]
            reread = await store.get_conversation(tenant_id=str(tenant_a), conversation_id="demo")
            assert reread is not None
            assert [turn.content for turn in reread.turns] == [
                "second turn",
                "third turn replaces oldest",
            ]
            assert reread.schema_version == 3

            raw = await session.execute(
                text(
                    "SELECT encrypted_turns::text FROM tenant_ai_memory_conversations "
                    "WHERE tenant_id = :tenant_id AND conversation_id = 'demo'"
                ),
                {"tenant_id": tenant_a},
            )
            raw_payload = raw.scalar_one()
            assert "third turn replaces oldest" not in raw_payload
            assert "fernet-tenant-v1" in raw_payload

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_b)},
            )
            assert await store.get_conversation(
                tenant_id=str(tenant_a), conversation_id="demo"
            ) is None
            assert await store.delete_conversation(
                tenant_id=str(tenant_a), conversation_id="demo"
            ) is False

            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_a)},
            )
            opted_out = await store.set_settings(
                tenant_id=str(tenant_a), enabled=False, max_turns=2, retention_hours=1
            )
            assert opted_out.enabled is False
            assert await store.list_for_tenant(tenant_id=str(tenant_a)) == []
            assert await store.get_conversation(
                tenant_id=str(tenant_a), conversation_id="demo"
            ) is None
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
