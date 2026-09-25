"""Quick connectivity check against the test PostgreSQL."""
import asyncio
import asyncpg


async def main():
    PASSWORD = "salesos_dev_password"

    conn = await asyncpg.connect(
        user="salesos", password=PASSWORD, database="salesos",
        host="localhost", port=5432,
    )
    version = await conn.fetchval("SELECT version()")
    print(f"Connected: {version[:80]}")

    db_exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname='salesos_test'"
    )
    print(f"salesos_test exists: {db_exists}")

    if not db_exists:
        await conn.close()
        conn = await asyncpg.connect(
            user="salesos", password=PASSWORD, database="salesos",
            host="localhost", port=5432,
        )
        await conn.execute("CREATE DATABASE salesos_test OWNER salesos")
        print("Created salesos_test")

    await conn.close()

    conn = await asyncpg.connect(
        user="salesos", password=PASSWORD, database="salesos_test",
        host="localhost", port=5432,
    )
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    print(f"\nExisting tables in salesos_test: {len(tables)}")
    for t in tables:
        print(f"  {t['tablename']}")

    md_tables = [t for t in tables if t["tablename"].startswith("md_")]
    print(f"\nmd_* tables: {len(md_tables)}")
    await conn.close()


asyncio.run(main())
