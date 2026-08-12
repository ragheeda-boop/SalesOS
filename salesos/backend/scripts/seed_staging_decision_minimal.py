"""A-09 staging-only minimal Decision seed (no app Settings import).

Creates idempotent muhide tenant + admin + 5 companies for IL-2A evaluate path.
Requires DATABASE_URL (use Railway Postgres DATABASE_PUBLIC_URL from staging).
Refuse unless CONFIRM_STAGING_SEED=1 and ENV/RAILWAY_ENVIRONMENT_NAME is staging.

Never prints passwords or connection strings.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

TARGET_EMAIL = "ragheed.a@muhide.com"
TENANT_SLUG = "muhide"
TENANT_NAME = "Muhide"
# Staging-only default — change after first login; never logged.
DEFAULT_PASSWORD = "MuhideStagingSeed@2026!"

COMPANIES = [
    ("شركة تككو للحلول التقنية", "TechCo Solutions", "3010000101", "Riyadh", "technology"),
    ("شركة فن سيرف للتقنية المالية", "FinServe Technologies", "3010000102", "Jeddah", "fintech"),
    ("شركة هيلث بلاس للأنظمة الصحية", "HealthPlus Systems", "3010000103", "Dammam", "healthcare"),
    ("شركة ريتيل ماكس للذكاء الاصطناعي", "RetailMax AI", "3010000104", "Khobar", "retail"),
    ("شركة إديو جلوبال للتعليم", "EduGlobal Learning", "3010000105", "Riyadh", "education"),
]


def _guard() -> None:
    confirm = os.environ.get("CONFIRM_STAGING_SEED", "").strip().lower() in ("1", "true", "yes")
    env = (
        os.environ.get("RAILWAY_ENVIRONMENT_NAME")
        or os.environ.get("RAILWAY_ENVIRONMENT")
        or os.environ.get("ENV")
        or ""
    ).strip().lower()
    if not confirm:
        print("REFUSE: set CONFIRM_STAGING_SEED=1", file=sys.stderr)
        raise SystemExit(2)
    if env != "staging":
        print(f"REFUSE: expected staging environment label, got {env!r}", file=sys.stderr)
        raise SystemExit(2)
    if not os.environ.get("DATABASE_URL"):
        print("REFUSE: DATABASE_URL required", file=sys.stderr)
        raise SystemExit(2)


def _hash_password(password: str) -> str:
    # Match SalesOS identity hashing (passlib bcrypt) without importing Settings.
    from passlib.context import CryptContext

    return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)


async def _seed() -> dict[str, int]:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    password = (os.environ.get("MUHIDE_ADMIN_PASSWORD") or "").strip() or DEFAULT_PASSWORD
    pwd_hash = _hash_password(password)
    now = datetime.now(timezone.utc)
    stats = {
        "tenant_created": 0,
        "tenant_existing": 0,
        "user_created": 0,
        "user_existing": 0,
        "companies_created": 0,
        "companies_skipped": 0,
    }

    eng = create_async_engine(url, pool_pre_ping=True)
    async with eng.begin() as c:
        row = (
            await c.execute(
                text("select id from tenants where slug = :slug limit 1"),
                {"slug": TENANT_SLUG},
            )
        ).first()
        if row is None:
            tenant_id = uuid.uuid4()
            await c.execute(
                text(
                    """
                    insert into tenants (id, name, slug, domain, plan, is_active, created_at, updated_at)
                    values (:id, :name, :slug, :domain, :plan, true, :now, :now)
                    """
                ),
                {
                    "id": tenant_id,
                    "name": TENANT_NAME,
                    "slug": TENANT_SLUG,
                    "domain": "muhide.com",
                    "plan": "enterprise",
                    "now": now,
                },
            )
            stats["tenant_created"] = 1
            print(f"created tenant slug={TENANT_SLUG}")
        else:
            tenant_id = row[0]
            stats["tenant_existing"] = 1
            print(f"existing tenant slug={TENANT_SLUG}")

        urow = (
            await c.execute(
                text("select id from users where email = :email limit 1"),
                {"email": TARGET_EMAIL},
            )
        ).first()
        if urow is None:
            await c.execute(
                text(
                    """
                    insert into users (
                      id, email, password_hash, full_name, tenant_id, role,
                      is_active, is_verified, created_at, updated_at
                    ) values (
                      :id, :email, :password_hash, :full_name, :tenant_id, 'admin',
                      true, true, :now, :now
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "email": TARGET_EMAIL,
                    "password_hash": pwd_hash,
                    "full_name": "Ragheed Alharbi",
                    "tenant_id": tenant_id,
                    "now": now,
                },
            )
            stats["user_created"] = 1
            print(f"created user email={TARGET_EMAIL}")
        else:
            stats["user_existing"] = 1
            print(f"existing user email={TARGET_EMAIL}")

        for name_ar, name_en, cr, city, industry in COMPANIES:
            exists = (
                await c.execute(
                    text(
                        """
                        select id from companies
                        where tenant_id = :tid and cr_number = :cr
                        limit 1
                        """
                    ),
                    {"tid": tenant_id, "cr": cr},
                )
            ).first()
            if exists is not None:
                stats["companies_skipped"] += 1
                print(f"skip company cr={cr} name_en={name_en}")
                continue
            await c.execute(
                text(
                    """
                    insert into companies (
                      id, tenant_id, name_ar, name_en, cr_number, city, industry,
                      status, is_active, is_golden_record, confidence_score,
                      created_at, updated_at
                    ) values (
                      :id, :tid, :name_ar, :name_en, :cr, :city, :industry,
                      'active', true, true, 0.95, :now, :now
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "tid": tenant_id,
                    "name_ar": name_ar,
                    "name_en": name_en,
                    "cr": cr,
                    "city": city,
                    "industry": industry,
                    "now": now,
                },
            )
            stats["companies_created"] += 1
            print(f"created company cr={cr} name_en={name_en}")

        total = (
            await c.execute(
                text("select count(*) from companies where tenant_id = :tid"),
                {"tid": tenant_id},
            )
        ).scalar()
        stats["companies_total"] = int(total or 0)

    await eng.dispose()
    return stats


def main() -> int:
    _guard()
    stats = asyncio.run(_seed())
    print(
        "OK: staging decision seed "
        f"tenant_created={stats['tenant_created']} "
        f"user_created={stats['user_created']} "
        f"user_existing={stats['user_existing']} "
        f"companies_created={stats['companies_created']} "
        f"companies_skipped={stats['companies_skipped']} "
        f"companies_total={stats.get('companies_total', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
