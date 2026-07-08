"""Test event store and audit store directly."""
import asyncio, json, uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

async def test():
    engine = create_async_engine('postgresql+asyncpg://salesos:salesos_dev_password@postgres:5432/salesos')
    factory = async_sessionmaker(engine, class_=AsyncSession)

    # Test domain_events INSERT (the fixed version without ::jsonb)
    async with factory() as sess:
        try:
            await sess.execute(
                text("""
                    INSERT INTO domain_events (
                        event_id, event_type, event_version,
                        aggregate_id, aggregate_type, tenant_id,
                        occurred_at, data, metadata
                    ) VALUES (
                        :event_id, :event_type, :event_version,
                        :aggregate_id, :aggregate_type, :tenant_id,
                        :occurred_at, :data, :metadata
                    )
                """),
                {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "test.event",
                    "event_version": 1,
                    "aggregate_id": str(uuid.uuid4()),
                    "aggregate_type": "test",
                    "tenant_id": "c487a63b-5d47-46b3-9416-dbb854c6cfce",
                    "occurred_at": datetime.now(timezone.utc),
                    "data": json.dumps({"test": True}),
                    "metadata": json.dumps({}),
                },
            )
            await sess.commit()
            print("DOMAIN_EVENTS INSERT OK")
        except Exception as e:
            await sess.rollback()
            print(f"DOMAIN_EVENTS FAILED: {type(e).__name__}: {e}")

    # Test audit INSERT with CAST
    async with factory() as sess:
        try:
            await sess.execute(
                text("""
                    INSERT INTO audit.audit_log (
                        tenant_id, entity_type, entity_id, action, changes, performed_at
                    ) VALUES (
                        :tenant_id, :entity_type, :entity_id, :action,
                        CAST(:changes AS jsonb), :performed_at
                    )
                """),
                {
                    "tenant_id": "c487a63b-5d47-46b3-9416-dbb854c6cfce",
                    "entity_type": "test",
                    "entity_id": str(uuid.uuid4()),
                    "action": "test",
                    "changes": json.dumps({"test": True}),
                    "performed_at": datetime.now(timezone.utc),
                },
            )
            await sess.commit()
            print("AUDIT INSERT OK")
        except Exception as e:
            await sess.rollback()
            print(f"AUDIT FAILED: {type(e).__name__}: {e}")

    # Test activity_records INSERT
    async with factory() as sess:
        try:
            await sess.execute(
                text("""
                    INSERT INTO activity_records (
                        id, actor, action, entity_type, entity_id, tenant_id
                    ) VALUES (
                        :id, :actor, :action, :entity_type, :entity_id, :tenant_id
                    )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "actor": "test",
                    "action": "test",
                    "entity_type": "test",
                    "entity_id": str(uuid.uuid4()),
                    "tenant_id": "c487a63b-5d47-46b3-9416-dbb854c6cfce",
                },
            )
            await sess.commit()
            print("ACTIVITY_RECORDS INSERT OK")
        except Exception as e:
            await sess.rollback()
            print(f"ACTIVITY_RECORDS FAILED: {type(e).__name__}: {e}")

    await engine.dispose()

asyncio.run(test())
