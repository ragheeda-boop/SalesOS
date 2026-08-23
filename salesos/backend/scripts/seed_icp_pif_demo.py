#!/usr/bin/env python3
"""Idempotent demo ICP profile for tenant pif (Phase 4F data seed).

Usage (Docker):
  docker compose exec -T backend python scripts/seed_icp_pif_demo.py
  docker compose exec -T backend python scripts/seed_icp_pif_demo.py --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.database import async_session
from app.modules.gtm.icp_persistence import PostgresICPRepository

T_PIF = "a0000000-0000-4000-a000-000000000001"
DEMO_ID = "pif-icp-demo"
DEMO_NAME = "pif-enterprise-icp-demo"


async def _count_profiles(tenant_id: str) -> int:
    async with async_session() as db:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant_id}
        )
        res = await db.execute(text("SELECT COUNT(*) FROM icp_profiles"))
        return int(res.scalar_one())


async def seed() -> None:
    repo = PostgresICPRepository(None)
    existing = await repo.list_for_tenant(tenant_id=T_PIF)
    for p in existing:
        if p.name == DEMO_NAME or p.id == DEMO_ID:
            count = await _count_profiles(T_PIF)
            print(f"ICP profile already exists: id={p.id} name={p.name}")
            print(f"icp_profiles count for tenant pif: {count}")
            return

    created = await repo.create(
        tenant_id=T_PIF,
        profile_id=DEMO_ID,
        name=DEMO_NAME,
        description=(
            "Demo ICP for pif tenant — construction and financial services "
            "targets in Riyadh/Jeddah"
        ),
        industries=["construction", "financial-services", "financial"],
        cities=["Riyadh", "Jeddah"],
        employees_min=200,
        employees_max=50_000,
        titles=["CEO", "CFO", "VP Sales", "Head of Procurement", "Director of Finance"],
        keywords=["infrastructure", "digital transformation", "B2B"],
        weights={
            "industry": 2.0,
            "city": 1.5,
            "employees": 1.0,
            "titles": 1.5,
            "keywords": 0.5,
        },
        is_active=True,
    )
    count = await _count_profiles(T_PIF)
    print(
        f"Created ICP profile: id={created.id} name={created.name} "
        f"v={created.schema_version}"
    )
    print(f"icp_profiles count for tenant pif: {count}")


async def cleanup() -> None:
    repo = PostgresICPRepository(None)
    deleted = 0
    for p in await repo.list_for_tenant(tenant_id=T_PIF):
        if p.name == DEMO_NAME or p.id == DEMO_ID:
            await repo.delete(p.id, tenant_id=T_PIF)
            deleted += 1
            print(f"Deleted ICP profile: id={p.id}")
    count = await _count_profiles(T_PIF)
    print(f"Deleted {deleted} profile(s); icp_profiles count for tenant pif: {count}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    asyncio.run(cleanup() if args.cleanup else seed())


if __name__ == "__main__":
    main()
