"""Provision admin user ragheed.a@ratlfintech.com from existing muhide account.

Copies password_hash from ragheed.a@muhide.com (same password, no plaintext).
Places new user in the same tenant. Role=admin, verified, active.

Google OAuth: clones google_accounts / employee_oauth_tokens rows from the
source user IF present (encrypted tokens only). Does NOT invent tokens.

Refuse when ENV=production unless ALLOW_RATL_ADMIN_PROVISION=1.

Usage (Railway SSH / run):
  ALLOW_RATL_ADMIN_PROVISION=1 python scripts/provision_ratl_admin.py

Never print passwords or token material. Delete after use if temporary.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

SOURCE_EMAIL = "ragheed.a@muhide.com"
TARGET_EMAIL = "ragheed.a@ratlfintech.com"
FULL_NAME = "Ragheed Alharbi (RATL)"


def _guard() -> None:
    from app.config import settings

    env = (settings.env or "").strip().lower()
    allow = os.environ.get("ALLOW_RATL_ADMIN_PROVISION", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if env == "production" and not allow:
        print(
            "REFUSE: ENV=production — set ALLOW_RATL_ADMIN_PROVISION=1",
            file=sys.stderr,
        )
        raise SystemExit(2)


async def main() -> int:
    _guard()
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    raw = os.environ.get("DATABASE_URL") or ""
    if not raw:
        print("NO_DATABASE_URL")
        return 1
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(raw)
    async with engine.begin() as conn:
        src = (
            await conn.execute(
                text(
                    "select id::text, tenant_id::text, password_hash, full_name, role, "
                    "is_active, is_verified "
                    "from users where lower(email)=lower(:e) limit 1"
                ),
                {"e": SOURCE_EMAIL},
            )
        ).mappings().one_or_none()
        if not src:
            print("SOURCE_USER_MISSING")
            await engine.dispose()
            return 3

        print("SOURCE_FOUND True")
        print("SOURCE_ROLE", src["role"])
        print("SOURCE_TENANT_SET", bool(src["tenant_id"]))

        existing = (
            await conn.execute(
                text(
                    "select id::text, role, is_active, is_verified, tenant_id::text "
                    "from users where lower(email)=lower(:e) limit 1"
                ),
                {"e": TARGET_EMAIL},
            )
        ).mappings().one_or_none()

        now = datetime.now(timezone.utc)
        src_tid = uuid.UUID(str(src["tenant_id"]))
        src_uid = uuid.UUID(str(src["id"]))

        if existing:
            target_uuid = uuid.UUID(str(existing["id"]))
            await conn.execute(
                text(
                    "update users set "
                    "password_hash=:ph, role='admin', is_active=true, is_verified=true, "
                    "tenant_id=:tid, full_name=:fn, updated_at=:now, "
                    "failed_attempts=0, locked_until=null, deleted_at=null "
                    "where id=:id"
                ),
                {
                    "ph": src["password_hash"],
                    "tid": src_tid,
                    "fn": FULL_NAME,
                    "now": now,
                    "id": target_uuid,
                },
            )
            target_id = str(target_uuid)
            print("TARGET_ACTION updated")
        else:
            target_uuid = uuid.uuid4()
            target_id = str(target_uuid)
            await conn.execute(
                text(
                    "insert into users ("
                    "id, tenant_id, email, password_hash, full_name, role, "
                    "is_active, is_verified, failed_attempts, created_at, updated_at"
                    ") values ("
                    ":id, :tid, :email, :ph, :fn, 'admin', "
                    "true, true, 0, :now, :now"
                    ")"
                ),
                {
                    "id": target_uuid,
                    "tid": src_tid,
                    "email": TARGET_EMAIL,
                    "ph": src["password_hash"],
                    "fn": FULL_NAME,
                    "now": now,
                },
            )
            print("TARGET_ACTION created")

        print("TARGET_ID_SET", bool(target_id))
        print("TARGET_ROLE admin")
        print("PASSWORD_COPIED_FROM_SOURCE True")

        # Clone Google OAuth if source has rows
        has_ga = (
            await conn.execute(
                text(
                    "select exists (select 1 from information_schema.tables "
                    "where table_schema='public' and table_name='google_accounts')"
                )
            )
        ).scalar()
        oauth_cloned = 0
        if has_ga:
            ga_rows = (
                await conn.execute(
                    text(
                        "select * from google_accounts "
                        "where user_id=:u and tenant_id=:t"
                    ),
                    {"u": src_uid, "t": src_tid},
                )
            ).mappings().all()
            print("SOURCE_GOOGLE_ACCOUNTS", len(ga_rows))
            for g in ga_rows:
                exists_t = (
                    await conn.execute(
                        text(
                            "select id from google_accounts "
                            "where user_id=:u and tenant_id=:t limit 1"
                        ),
                        {"u": target_uuid, "t": src_tid},
                    )
                ).scalar()
                if exists_t:
                    await conn.execute(
                        text(
                            "update google_accounts set "
                            "email=:email, provider=:provider, "
                            "access_token_encrypted=:at, refresh_token_encrypted=:rt, "
                            "token_expiry=:tex, scope=:scope, google_user_id=:gid, "
                            "avatar_url=:av, history_id=:hid, calendar_sync_token=:cst, "
                            "is_active=:active, last_sync_at=:ls, updated_at=:now "
                            "where id=:id"
                        ),
                        {
                            "email": g["email"],
                            "provider": g["provider"],
                            "at": g["access_token_encrypted"],
                            "rt": g["refresh_token_encrypted"],
                            "tex": g["token_expiry"],
                            "scope": g["scope"],
                            "gid": g["google_user_id"],
                            "av": g["avatar_url"],
                            "hid": g["history_id"],
                            "cst": g.get("calendar_sync_token"),
                            "active": g["is_active"],
                            "ls": g["last_sync_at"],
                            "now": now,
                            "id": exists_t,
                        },
                    )
                else:
                    await conn.execute(
                        text(
                            "insert into google_accounts ("
                            "id, tenant_id, user_id, email, provider, "
                            "access_token_encrypted, refresh_token_encrypted, token_expiry, "
                            "scope, google_user_id, avatar_url, history_id, "
                            "calendar_sync_token, is_active, last_sync_at, created_at, updated_at"
                            ") values ("
                            ":id, :tid, :uid, :email, :provider, "
                            ":at, :rt, :tex, :scope, :gid, :av, :hid, :cst, :active, :ls, :now, :now"
                            ")"
                        ),
                        {
                            "id": uuid.uuid4(),
                            "tid": src_tid,
                            "uid": target_uuid,
                            "email": g["email"],
                            "provider": g["provider"],
                            "at": g["access_token_encrypted"],
                            "rt": g["refresh_token_encrypted"],
                            "tex": g["token_expiry"],
                            "scope": g["scope"],
                            "gid": g["google_user_id"],
                            "av": g["avatar_url"],
                            "hid": g["history_id"],
                            "cst": g.get("calendar_sync_token"),
                            "active": g["is_active"],
                            "ls": g["last_sync_at"],
                            "now": now,
                        },
                    )
                oauth_cloned += 1

        print("GOOGLE_OAUTH_CLONED", oauth_cloned)
        if oauth_cloned == 0:
            print(
                "GOOGLE_OAUTH_NOTE source has no google_accounts — "
                "target admin created; connect Google via UI Integrations"
            )

        # Verify
        ver = (
            await conn.execute(
                text(
                    "select role, is_active, is_verified, "
                    "(password_hash = :ph) as same_password "
                    "from users where id=:id"
                ),
                {"ph": src["password_hash"], "id": target_uuid},
            )
        ).mappings().one()
        print("VERIFY_ROLE", ver["role"])
        print("VERIFY_ACTIVE", ver["is_active"])
        print("VERIFY_VERIFIED", ver["is_verified"])
        print("VERIFY_SAME_PASSWORD_HASH", ver["same_password"])

        ga_t = (
            await conn.execute(
                text("select count(*) from google_accounts where user_id=:u"),
                {"u": target_uuid},
            )
        ).scalar()
        print("TARGET_GOOGLE_ACCOUNTS", ga_t)

    await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
