"""TEMP probe: isolate Tenant flush hang vs Tenant.users lazy strategy.

Run: python -u /app/scripts/_tmp_tenant_flush_probe.py [selectin|noload|raise_on_sql|select]
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime

LAZY = sys.argv[1] if len(sys.argv) > 1 else "selectin"
OUT = f"/tmp/tenant_flush_{LAZY}.txt"

with open(OUT, "w", encoding="utf-8") as _boot:
    _boot.write(f"BOOT lazy={LAZY} pid={os.getpid()}\n")
sys.stdout.write(f"BOOT lazy={LAZY}\n")
sys.stdout.flush()

sys.stdout.write("IMPORTING sqlalchemy\n")
sys.stdout.flush()
with open(OUT, "a", encoding="utf-8") as _f:
    _f.write("IMPORTING sqlalchemy\n")

from sqlalchemy import Boolean, DateTime, ForeignKey, String, event, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

sys.stdout.write("IMPORTED sqlalchemy\n")
sys.stdout.flush()
with open(OUT, "a", encoding="utf-8") as _f:
    _f.write("IMPORTED sqlalchemy\n")


def log(msg: str) -> None:
    line = msg + "\n"
    sys.stdout.write(line)
    sys.stdout.flush()
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(line)


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_residency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provisioning_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict | None] = mapped_column(type_=JSONB, default=dict)
    features: Mapped[dict | None] = mapped_column(type_=JSONB, default=dict)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", lazy=LAZY)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name_ar: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    department: Mapped[str | None] = mapped_column(String(100))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(30))
    preferences: Mapped[dict | None] = mapped_column(type_=JSONB, default=dict)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")


async def run() -> None:
    sql_seen: list[str] = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        s = " ".join(str(statement).split())[:220]
        sql_seen.append(s)
        log(f"SQL: {s}")

    event.listen(Tenant, "before_insert", lambda *a, **k: log("EVENT before_insert"))
    event.listen(Tenant, "after_insert", lambda *a, **k: log("EVENT after_insert"))

    url = os.environ.get("DATABASE_URL") or (
        "postgresql+asyncpg://salesos:salesos_dev_password@postgres:5432/salesos"
    )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    log(f"PROBE lazy={LAZY} url_host={url.split('@')[-1]}")
    engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    tid = uuid.uuid4()

    async with Session() as db:
        await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tid)})
        log("GUC set")
        db.add(Tenant(id=tid, name="probe", slug=str(tid)[:8], plan="free"))
        log("BEFORE flush")
        try:
            await asyncio.wait_for(db.flush(), timeout=6.0)
            log("AFTER flush OK")
            log(f"RESULT=OK insert_seen={any('INSERT INTO tenants' in s for s in sql_seen)}")
        except TimeoutError:
            body = open(OUT, encoding="utf-8").read()
            log("TIMEOUT on flush")
            log(
                "RESULT=TIMEOUT "
                f"insert_seen={any('INSERT INTO tenants' in s for s in sql_seen)} "
                f"before_insert={'EVENT before_insert' in body} "
                f"after_insert={'EVENT after_insert' in body}"
            )
        except Exception as exc:
            log(f"ERROR {type(exc).__name__}: {exc}")
            log(f"RESULT=ERROR insert_seen={any('INSERT INTO tenants' in s for s in sql_seen)}")
        try:
            await db.rollback()
        except Exception:
            pass
    await engine.dispose()
    log("DONE")


if __name__ == "__main__":
    asyncio.run(run())
