#!/usr/bin/env python3
"""Idempotent seed: muhide tenant + ragheed.a@muhide.com + demo CRM companies.

Creates (if absent):
  - tenant slug=muhide
  - admin user ragheed.a@muhide.com
  - 5 demo companies in that tenant

Password:
  - env MUHIDE_ADMIN_PASSWORD (required when ENV=production)
  - else default local-only password (never log plaintext)

Usage:
  # Local compose
  docker compose exec -T backend python scripts/seed_muhide_account.py

  # Railway one-shot (from salesos/ with project linked)
  railway run --service SalesOS -- python scripts/seed_muhide_account.py

Refuse when ENV=production unless ALLOW_MUHIDE_SEED=1.
Never print passwords. Never commit secrets.
"""
from __future__ import annotations

import asyncio
import os
import sys

TARGET_EMAIL = "ragheed.a@muhide.com"
TENANT_SLUG = "muhide"
TENANT_NAME = "Muhide"
FULL_NAME = "Ragheed Alharbi"

COMPANIES = [
    {
        "name_ar": "شركة تككو للحلول التقنية",
        "name_en": "TechCo Solutions",
        "cr_number": "3010000101",
        "city": "Riyadh",
        "region": "Riyadh",
        "industry": "technology",
        "status": "active",
        "activity_description": "Enterprise SaaS and cloud infrastructure for MENA.",
        "website": "https://techco.sa",
        "email": "hello@techco.sa",
        "employees_count": 450,
    },
    {
        "name_ar": "شركة فن سيرف للتقنية المالية",
        "name_en": "FinServe Technologies",
        "cr_number": "3010000102",
        "city": "Jeddah",
        "region": "Makkah",
        "industry": "fintech",
        "status": "active",
        "activity_description": "Digital banking and payment processing platform.",
        "website": "https://finserve.sa",
        "email": "hello@finserve.sa",
        "employees_count": 320,
    },
    {
        "name_ar": "شركة هيلث بلاس للأنظمة الصحية",
        "name_en": "HealthPlus Systems",
        "cr_number": "3010000103",
        "city": "Dammam",
        "region": "Eastern",
        "industry": "healthcare",
        "status": "active",
        "activity_description": "EHR and telemedicine for Gulf hospitals and clinics.",
        "website": "https://healthplus.sa",
        "email": "hello@healthplus.sa",
        "employees_count": 280,
    },
    {
        "name_ar": "شركة ريتيل ماكس للذكاء الاصطناعي",
        "name_en": "RetailMax AI",
        "cr_number": "3010000104",
        "city": "Khobar",
        "region": "Eastern",
        "industry": "retail",
        "status": "active",
        "activity_description": "AI retail analytics and inventory optimization.",
        "website": "https://retailmax.sa",
        "email": "hello@retailmax.sa",
        "employees_count": 180,
    },
    {
        "name_ar": "شركة إديو جلوبال للتعليم",
        "name_en": "EduGlobal Learning",
        "cr_number": "3010000105",
        "city": "Riyadh",
        "region": "Riyadh",
        "industry": "education",
        "status": "active",
        "activity_description": "LMS and virtual classroom for educational institutions.",
        "website": "https://eduglobal.sa",
        "email": "hello@eduglobal.sa",
        "employees_count": 150,
    },
]


def _guard() -> None:
    from app.config import settings

    env = (settings.env or "").strip().lower()
    allow = os.environ.get("ALLOW_MUHIDE_SEED", "").strip().lower() in ("1", "true", "yes")
    if env == "production" and not allow:
        print(
            "REFUSE: ENV=production — set ALLOW_MUHIDE_SEED=1 to seed muhide account.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _password() -> str:
    from app.config import settings

    pwd = (os.environ.get("MUHIDE_ADMIN_PASSWORD") or "").strip()
    env = (settings.env or "").strip().lower()
    if pwd:
        return pwd
    if env == "production":
        print(
            "REFUSE: MUHIDE_ADMIN_PASSWORD required when ENV=production.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    # Local-only default — change after first login.
    return "MuhideAdmin@2026!"


async def _seed() -> dict[str, int]:
    from app.database import async_session
    from app.modules.company.models import Company
    from app.modules.identity.models import Tenant, User
    from app.modules.identity.repositories import TenantRepository, UserRepository
    from app.modules.identity.service import hash_password
    from sqlalchemy import select, func

    stats = {
        "tenant_created": 0,
        "tenant_existing": 0,
        "user_created": 0,
        "user_existing": 0,
        "user_role_upgraded": 0,
        "companies_created": 0,
        "companies_skipped": 0,
    }
    password = _password()

    async with async_session() as db:
        tenant_repo = TenantRepository(db)
        user_repo = UserRepository(db)

        tenant = await tenant_repo.get_by_slug(TENANT_SLUG)
        if tenant is None:
            tenant = Tenant(
                name=TENANT_NAME,
                slug=TENANT_SLUG,
                domain="muhide.com",
                plan="enterprise",
                is_active=True,
            )
            db.add(tenant)
            await db.flush()
            stats["tenant_created"] = 1
            print(f"created tenant slug={TENANT_SLUG} id={tenant.id}")
        else:
            stats["tenant_existing"] = 1
            print(f"existing tenant slug={TENANT_SLUG} id={tenant.id}")

        user = await user_repo.get_by_email(TARGET_EMAIL)
        if user is None:
            user = User(
                email=TARGET_EMAIL,
                password_hash=hash_password(password),
                full_name=FULL_NAME,
                tenant_id=tenant.id,
                role="admin",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            stats["user_created"] = 1
            print(f"created user email={TARGET_EMAIL} role=admin")
        else:
            stats["user_existing"] = 1
            # Ensure same tenant + admin so companies are visible/creatable.
            changed = False
            if user.tenant_id != tenant.id:
                user.tenant_id = tenant.id
                changed = True
            if user.role != "admin":
                user.role = "admin"
                stats["user_role_upgraded"] = 1
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if not user.is_verified:
                user.is_verified = True
                changed = True
            # Optional password reset when MUHIDE_RESET_PASSWORD=1
            if os.environ.get("MUHIDE_RESET_PASSWORD", "").strip().lower() in ("1", "true", "yes"):
                user.password_hash = hash_password(password)
                changed = True
                print("password reset applied (MUHIDE_RESET_PASSWORD=1)")
            if changed:
                await db.flush()
            print(f"existing user email={TARGET_EMAIL} role={user.role} tenant_id={user.tenant_id}")

        for spec in COMPANIES:
            existing = await db.execute(
                select(Company.id).where(
                    Company.tenant_id == tenant.id,
                    Company.cr_number == spec["cr_number"],
                )
            )
            if existing.scalar_one_or_none() is not None:
                stats["companies_skipped"] += 1
                print(f"skip company cr={spec['cr_number']} name_en={spec['name_en']}")
                continue

            company = Company(
                tenant_id=tenant.id,
                name_ar=spec["name_ar"],
                name_en=spec["name_en"],
                cr_number=spec["cr_number"],
                city=spec.get("city"),
                region=spec.get("region"),
                industry=spec.get("industry"),
                status=spec.get("status", "active"),
                activity_description=spec.get("activity_description"),
                website=spec.get("website"),
                email=spec.get("email"),
                employees_count=spec.get("employees_count"),
                is_active=True,
                is_golden_record=True,
                confidence_score=0.95,
                tags=["seed", "muhide"],
            )
            db.add(company)
            stats["companies_created"] += 1
            print(f"created company cr={spec['cr_number']} name_en={spec['name_en']}")

        await db.commit()

        count = await db.execute(
            select(func.count()).select_from(Company).where(Company.tenant_id == tenant.id)
        )
        stats["companies_total"] = int(count.scalar() or 0)

    return stats


def main() -> int:
    _guard()
    stats = asyncio.run(_seed())
    print(
        "OK: muhide seed complete "
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
