#!/usr/bin/env python3
"""STORY-04-02 demo: provision a brand-new test tenant end-to-end (no UI).

Usage (Docker non-prod)::

    docker compose exec backend python scripts/provision_tenant.py \\
        --name "Acme Pilot" --slug acme-pilot --plan starter \\
        --plan-id plan_starter_v1 --region me-central-1

Idempotent: re-running with the same slug does not duplicate Studio config.
Does NOT claim Production GO. DEC-085 untouched.
"""
from __future__ import annotations

import argparse
import asyncio
import sys


async def _run(args: argparse.Namespace) -> int:
    from app.database import async_session
    from app.modules.admin.services import TenantProvisioningService

    async with async_session() as db:
        svc = TenantProvisioningService(db)
        result = await svc.provision_workflow(
            name=args.name,
            slug=args.slug,
            domain=args.domain,
            plan=args.plan,
            plan_id=args.plan_id,
            region=args.region,
            data_residency=args.data_residency,
            admin_email=args.admin_email,
            admin_password=args.admin_password,
            admin_full_name=args.admin_full_name,
        )
        await db.commit()

    print("[OK] provision_workflow")
    for key in (
        "tenant_id",
        "slug",
        "created",
        "idempotent",
        "provisioning_status",
        "admin_user_id",
    ):
        print(f"  {key}: {result.get(key)}")
    studio = result.get("studio_config") or {}
    print(f"  studio_config.seeded: {studio.get('seeded')}")
    print(f"  studio_config.idempotent: {studio.get('idempotent')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Idempotent tenant provisioning (STORY-04-02)")
    parser.add_argument("--name", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--plan", default="free")
    parser.add_argument("--plan-id", default=None, dest="plan_id")
    parser.add_argument("--region", default=None)
    parser.add_argument("--data-residency", default=None, dest="data_residency")
    parser.add_argument("--admin-email", default=None, dest="admin_email")
    parser.add_argument("--admin-password", default=None, dest="admin_password")
    parser.add_argument("--admin-full-name", default=None, dest="admin_full_name")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
