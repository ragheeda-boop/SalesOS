#!/usr/bin/env python3
"""Idempotent LOCAL demo_tenant + @salesos.io users (PENTEST_BRIEF §5.1).

Creates demo_tenant and documented demo accounts if absent.
Does NOT overwrite existing users or unrelated tenants.
Does NOT print passwords.

Usage (local compose only):
  docker compose exec -T backend python scripts/seed_demo_users.py

Refuse to run when ENV=production unless ALLOW_DEMO_SEED=1 (still local-only intent).
Never target production. Never commit secrets into evidence markdown.
"""
from __future__ import annotations

import asyncio
import os
import sys

# Passwords match salesos/docs/pentest/PENTEST_BRIEF.md §5.1 (local demo only).
# Prefer env overrides; never log plaintext.
DEMO_USERS: list[dict[str, str]] = [
    {
        "email": "admin@salesos.io",
        "password_env": "DEMO_ADMIN_PASSWORD",
        "password_default": "Admin@123!",
        "role": "admin",
        "full_name": "Ahmed Al-Sulami",
    },
    {
        "email": "manager@salesos.io",
        "password_env": "DEMO_MANAGER_PASSWORD",
        "password_default": "Manager@123!",
        "role": "manager",
        "full_name": "Noura Al-Qahtani",
    },
    {
        "email": "rep1@salesos.io",
        "password_env": "DEMO_REP_PASSWORD",
        "password_default": "Rep@123!",
        "role": "rep",
        "full_name": "Fahad Al-Otaibi",
    },
    {
        "email": "rep2@salesos.io",
        "password_env": "DEMO_REP_PASSWORD",
        "password_default": "Rep@123!",
        "role": "rep",
        "full_name": "Sara Al-Dosari",
    },
    {
        "email": "rep3@salesos.io",
        "password_env": "DEMO_REP_PASSWORD",
        "password_default": "Rep@123!",
        "role": "rep",
        "full_name": "Khalid Al-Mutairi",
    },
]

DEMO_TENANT_SLUG = "demo_tenant"
DEMO_TENANT_NAME = "SalesOS Demo"


def _guard_local_only() -> None:
    from app.config import settings

    env = (settings.env or "").strip().lower()
    allow = os.environ.get("ALLOW_DEMO_SEED", "").strip() in ("1", "true", "yes")
    if env == "production" and not allow:
        print(
            "REFUSE: ENV=production — set ALLOW_DEMO_SEED=1 only for approved non-prod copies.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    host = (settings.postgres_host or "").strip().lower()
    # Local compose uses service name "postgres" or localhost.
    local_hosts = {"postgres", "localhost", "127.0.0.1", "pgbouncer"}
    if host and host not in local_hosts and not allow:
        print(
            f"REFUSE: postgres_host={host!r} is not a known local compose host. "
            "Set ALLOW_DEMO_SEED=1 only for approved non-prod.",
            file=sys.stderr,
        )
        raise SystemExit(2)


async def _seed() -> dict[str, int]:
    from app.database import async_session
    from app.modules.identity.models import Tenant, User
    from app.modules.identity.repositories import TenantRepository, UserRepository
    from app.modules.identity.service import hash_password

    stats = {"tenant_created": 0, "tenant_existing": 0, "users_created": 0, "users_skipped": 0}

    async with async_session() as db:
        tenant_repo = TenantRepository(db)
        user_repo = UserRepository(db)

        tenant = await tenant_repo.get_by_slug(DEMO_TENANT_SLUG)
        if tenant is None:
            tenant = Tenant(
                name=DEMO_TENANT_NAME,
                slug=DEMO_TENANT_SLUG,
                plan="enterprise",
                is_active=True,
            )
            db.add(tenant)
            await db.flush()
            stats["tenant_created"] = 1
            print(f"created tenant slug={DEMO_TENANT_SLUG} id={tenant.id}")
        else:
            stats["tenant_existing"] = 1
            print(f"existing tenant slug={DEMO_TENANT_SLUG} id={tenant.id}")

        for spec in DEMO_USERS:
            email = spec["email"]
            existing = await user_repo.get_by_email(email)
            if existing is not None:
                stats["users_skipped"] += 1
                print(f"skip existing user email={email} role={existing.role}")
                continue

            password = os.environ.get(spec["password_env"]) or spec["password_default"]
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=spec["full_name"],
                tenant_id=tenant.id,
                role=spec["role"],
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            stats["users_created"] += 1
            print(f"created user email={email} role={spec['role']}")

        await db.commit()

    return stats


def main() -> int:
    _guard_local_only()
    stats = asyncio.run(_seed())
    print(
        "OK: seed complete "
        f"tenant_created={stats['tenant_created']} "
        f"tenant_existing={stats['tenant_existing']} "
        f"users_created={stats['users_created']} "
        f"users_skipped={stats['users_skipped']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
