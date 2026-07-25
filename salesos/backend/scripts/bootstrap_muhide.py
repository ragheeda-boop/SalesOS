import asyncio, uuid
from sqlalchemy import select
from app.modules.identity.models import User, Tenant
from app.database import async_session
from app.modules.identity.service import IdentityService

async def bootstrap():
    async with async_session() as db:
        svc = IdentityService(db=db)
        tenant_id = uuid.UUID('ba73a0e7-7a12-4f5d-9c8e-012345678901')
        
        t = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
        if not t:
            print("[FAIL] Tenant not found!")
            return
        print(f"[OK] Tenant: {t.name} (slug={t.slug})")
        
        users_data = [
            ('ragheed.a@muhide.com', 'Ragheed Al-Abdullah', 'Muhide2026!', 'admin'),
            ('sultan.a@muhide.com', 'Sultan Al-Abdullah', 'Muhide2026!', 'admin'),
        ]
        
        for email, full_name, password, role in users_data:
            existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if existing:
                existing.tenant_id = tenant_id
                existing.role = role
                existing.is_active = True
                existing.is_verified = True
                print(f"[UPDATED] {email} — tenant set to Muhide, role={role}")
            else:
                user = await svc.create_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    tenant_id=str(tenant_id),
                    role=role,
                )
                user.is_verified = True
                print(f"[CREATED] {email} (id={user.id}, role={role})")
        
        await db.commit()
        print("[OK] Users saved")
        
        result = await db.execute(
            select(User).where(User.tenant_id == tenant_id).order_by(User.email)
        )
        users = result.scalars().all()
        print(f"\n=== Muhide Users ({len(users)} total) ===")
        for u in users:
            print(f"  {u.email} | {u.full_name} | role={u.role} | active={u.is_active} | verified={u.is_verified}")

asyncio.run(bootstrap())
