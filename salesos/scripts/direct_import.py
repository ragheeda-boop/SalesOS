import sys, os, json, time, uuid
import asyncio
from decimal import Decimal

# Hard-code constants
SOURCE_SLUG = "gov-merge-2026-07"
TENANT_ID = "00000000-0000-0000-0000-000000000001"
JSON_PATH = "/app/data/import/salesos_import.json"
BATCH_SIZE = 1000

sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://salesos:salesos_dev_password@postgres:5432/salesos",
)

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    from app.modules.company.models import Company, Source

    async with async_session() as db:
        # Verify source exists
        result = await db.execute(select(Source).where(Source.slug == SOURCE_SLUG))
        source = result.scalar_one_or_none()
        if not source:
            print(f"ERROR: Source {SOURCE_SLUG} not found")
            return
        print(f"Source found: {source.name}")

        # Pre-load all existing company CR numbers
        print("Loading existing CR numbers...")
        all_crs = set()
        for rec in data:
            cr = rec.get("cr_number")
            if cr:
                all_crs.add(cr)
        print(f"Unique CRs in file: {len(all_crs)}")

        result = await db.execute(
            select(Company.cr_number).where(
                Company.tenant_id == uuid.UUID(TENANT_ID),
                Company.cr_number.in_(list(all_crs)),
            )
        )
        existing_crs = set(row[0] for row in result.all())
        print(f"Existing CRs in DB: {len(existing_crs)}")

        created = 0
        updated = 0
        errors = 0
        error_samples = []
        start = time.time()

        company_fields = {
            c.name for c in Company.__table__.columns
            if c.name not in ("id", "created_at", "updated_at", "deleted_at")
        }

        for batch_start in range(0, len(data), BATCH_SIZE):
            batch = data[batch_start:batch_start + BATCH_SIZE]
            batch_created = 0
            batch_updated = 0
            batch_errors = 0

            for record in batch:
                try:
                    cr_number = record.get("cr_number")
                    if not cr_number:
                        batch_errors += 1
                        if len(error_samples) < 5:
                            error_samples.append(f"Missing cr_number: {json.dumps(record, ensure_ascii=False)[:200]}")
                        continue

                    if cr_number in existing_crs:
                        # Update existing
                        stmt = (
                            Company.__table__.update()
                            .where(
                                Company.tenant_id == uuid.UUID(TENANT_ID),
                                Company.cr_number == cr_number,
                            )
                            .values(**{k: v for k, v in record.items() if k in company_fields and v is not None})
                        )
                        await db.execute(stmt)
                        batch_updated += 1
                    else:
                        # Insert new
                        insert_data = {k: v for k, v in record.items() if k in company_fields and v is not None}
                        insert_data["tenant_id"] = uuid.UUID(TENANT_ID)
                        insert_data["id"] = uuid.uuid4()
                        stmt = Company.__table__.insert().values(**insert_data)
                        await db.execute(stmt)
                        existing_crs.add(cr_number)
                        batch_created += 1
                except Exception as e:
                    batch_errors += 1
                    if len(error_samples) < 20:
                        error_samples.append(f"[{cr_number}] {str(e)[:200]}")

            await db.commit()

            created += batch_created
            updated += batch_updated
            errors += batch_errors

            pct = (batch_start + len(batch)) / len(data) * 100
            elapsed = time.time() - start
            rate = (created + updated) / max(1, elapsed)
            print(f"[{pct:.1f}%] Batch {batch_start//BATCH_SIZE + 1}: +{batch_created} ~{batch_updated} !{batch_errors} | Total: {created+updated} | {rate:.0f} rec/s")

        elapsed = time.time() - start
        print(f"\n=== IMPORT COMPLETE ===")
        print(f"Time: {elapsed:.0f}s ({ (created+updated)/max(1,elapsed):.0f} rec/s)")
        print(f"Created: {created}")
        print(f"Updated: {updated}")
        print(f"Errors:  {errors}")
        print(f"Total:   {created + updated + errors}")

        if error_samples:
            print(f"\nError samples:")
            for e in error_samples:
                print(f"  {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
