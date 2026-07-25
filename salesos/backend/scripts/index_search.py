import asyncio, uuid, httpx, time
from app.database import async_session
from app.modules.company.models import Company
from sqlalchemy import select

MEILI_URL = "http://salesos-meilisearch:7700"
MEILI_KEY = "muhide-search-key-2026"
INDEX = "companies"

async def main():
    t0 = time.time()
    async with async_session() as db:
        total_r = await db.execute(select(Company.id))
        all_ids = [str(r[0]) for r in total_r.fetchall()]
        total = len(all_ids)
        print(f"DB companies: {total}")

        headers = {"Authorization": f"Bearer {MEILI_KEY}", "Content-Type": "application/json"}
        indexed = 0
        batch = 5000

        async with httpx.AsyncClient(timeout=60) as client:
            for i in range(0, total, batch):
                batch_ids = all_ids[i:i+batch]
                uuids = [uuid.UUID(bid) for bid in batch_ids]
                result = await db.execute(
                    select(Company.id, Company.name_ar, Company.name_en, Company.cr_number, Company.city, Company.status)
                    .where(Company.id.in_(uuids))
                )
                rows = result.fetchall()
                docs = [{
                    "id": str(r[0]),
                    "name_ar": r[1] or "",
                    "name_en": r[2] or "",
                    "cr_number": r[3] or "",
                    "city": r[4] or "",
                    "status": r[5] or "active",
                } for r in rows]
                if docs:
                    await client.post(f"{MEILI_URL}/indexes/{INDEX}/documents", headers=headers, json=docs)
                    indexed += len(docs)
                    if indexed % 25000 == 0:
                        elapsed = time.time() - t0
                        pct = round(indexed / total * 100, 1)
                        rate = round(indexed / elapsed)
                        print(f"  {indexed}/{total} ({pct}%) - {rate} docs/sec")

        # Settings
        await client.patch(f"{MEILI_URL}/indexes/{INDEX}/settings", headers=headers,
            json={"filterableAttributes": ["status", "city", "cr_number"]})

        # Verify
        stats = await client.get(f"{MEILI_URL}/indexes/{INDEX}/stats", headers=headers)
        meili_count = stats.json()["numberOfDocuments"]
        elapsed = time.time() - t0
        print(f"\nMeilisearch: {meili_count} documents")
        print(f"PostgreSQL:  {total}")
        print(f"MATCH: {meili_count == total}")
        print(f"Time: {round(elapsed)}s ({round(total/elapsed)} docs/sec)")

asyncio.run(main())
