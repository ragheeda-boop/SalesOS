"""Phase 4A — persistent tenant-scoped ICP profiles (Postgres layer).

Schema derived 1:1 from app.modules.gtm.icp.ICPProfile / ICPCriteria /
ICPWeights so the existing normalize_* + assert_weights_usable path remains
the single validation authority. Isolation is enforced by DB RLS
(migration h2i3j4k5l6m8, canonical DEC-085 pattern) AND by pinning
app.tenant_id around every statement here — defence in depth, fail-closed.

Runtime wiring into the agents is intentionally NOT switched in this phase;
see docs/adr/0109-icp-persistence.md (DECISION REQUIRED).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from app.modules.gtm.icp import (
    ICPError,
    ICPProfile,
    normalize_criteria,
    normalize_weights,
)
from app.modules.gtm.icp_engine import assert_weights_usable


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _require_uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        raise ICPError(f"{field} must be a valid uuid")


class PostgresICPRepository:
    """Async store speaking the SAME vocabulary as MemICPStore.

    create/update/get/list_for_tenant keep identical semantics (including
    bump_version-on-update) so a future runtime swap needs no agent changes.
    """

    def __init__(self, session_factory=None):
        self._sessions = session_factory

    def _session_ctx(self):
        """Session factory honoring an injected one (dedicated-loop adapters);
        defaults to the global app session pool."""
        if self._sessions is not None:
            return self._sessions()
        from app.database import async_session

        return async_session()

    # ── validation helpers (single source of truth: gtm.icp) ──────────
    @staticmethod
    def _validated(
        *,
        tenant_id: str,
        name: str,
        description: str,
        industries=None,
        cities=None,
        employees_min=None,
        employees_max=None,
        titles=None,
        keywords=None,
        weights: dict | None = None,
    ) -> dict[str, Any]:
        if not (tenant_id or "").strip():
            raise ICPError("tenant_id required")
        if not (name or "").strip():
            raise ICPError("name required")
        crit = normalize_criteria(
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
            titles=titles,
            keywords=keywords,
        )
        wraw = weights or {}
        w = normalize_weights(
            industry=wraw.get("industry"),
            city=wraw.get("city"),
            employees=wraw.get("employees"),
            titles=wraw.get("titles"),
            keywords=wraw.get("keywords"),
        )
        assert_weights_usable(w)
        return {"criteria": crit.as_dict(), "weights": w.as_dict()}

    @staticmethod
    def _row_to_profile(row) -> ICPProfile:
        """Fail-safe mapper: malformed stored JSON raises ICPError instead of
        yielding a half-valid profile to any consumer."""
        try:
            crit_raw = row.criteria if isinstance(row.criteria, dict) else dict(row.criteria)
            w_raw = row.weights if isinstance(row.weights, dict) else dict(row.weights)
            # stored-shape guards: engine-level _norm_list tolerates iterables,
            # but persisted payloads must be well-formed lists/ints or the
            # record is corrupt → fail safe rather than half-validate.
            for key in ("industries", "cities", "titles", "keywords"):
                val = crit_raw.get(key)
                if val is not None and not isinstance(val, list):
                    raise ICPError(f"criteria.{key} must be a list")
            for key in ("employees_min", "employees_max"):
                val = crit_raw.get(key)
                if val is not None and not isinstance(val, int):
                    raise ICPError(f"criteria.{key} must be an int")
            criteria = normalize_criteria(
                industries=crit_raw.get("industries"),
                cities=crit_raw.get("cities"),
                employees_min=crit_raw.get("employees_min"),
                employees_max=crit_raw.get("employees_max"),
                titles=crit_raw.get("titles"),
                keywords=crit_raw.get("keywords"),
            )
            w = normalize_weights(
                industry=w_raw.get("industry"),
                city=w_raw.get("city"),
                employees=w_raw.get("employees"),
                titles=w_raw.get("titles"),
                keywords=w_raw.get("keywords"),
            )
            return ICPProfile(
                id=str(row.id),
                tenant_id=str(row.tenant_id),
                name=str(row.name),
                description=str(row.description or ""),
                criteria=criteria,
                weights=w,
                schema_version=int(row.schema_version),
                is_active=bool(row.is_active),
                created_at=str(row.created_at),
                updated_at=str(row.updated_at),
            )
        except ICPError:
            raise
        except Exception as exc:  # malformed jsonb shapes etc.
            raise ICPError(f"malformed stored ICP payload: {exc}") from exc

    async def _pin(self, db, tenant_id: str) -> None:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)}
        )

    # ── writes ────────────────────────────────────────────────────────
    async def create(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str = "",
        industries=None,
        cities=None,
        employees_min=None,
        employees_max=None,
        titles=None,
        keywords=None,
        weights: dict | None = None,
        profile_id: str | None = None,
        is_active: bool = True,
    ) -> ICPProfile:
        tid = _require_uuid(tenant_id, "tenant_id")
        v = self._validated(
            tenant_id=tid,
            name=name,
            description=description,
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
            titles=titles,
            keywords=keywords,
            weights=weights,
        )
        rid = (profile_id or "").strip() or uuid.uuid4().hex[:12]
        now = _now_iso()
        now_ts = datetime.fromisoformat(now)
        async with self._session_ctx() as db:
            await self._pin(db, tid)
            await db.execute(
                text(
                    "INSERT INTO icp_profiles (id, tenant_id, name, description, "
                    "criteria, weights, schema_version, is_active, created_at, updated_at) "
                    "VALUES (:i, CAST(:t AS uuid), :n, :d, CAST(:c AS jsonb), "
                    "CAST(:w AS jsonb), 1, :a, :ca, :ua)"
                ),
                {
                    "i": rid,
                    "t": tid,
                    "n": name.strip(),
                    "d": (description or "").strip(),
                    "c": json.dumps(v["criteria"]),
                    "w": json.dumps(v["weights"]),
                    "a": bool(is_active),
                    "ca": now_ts,
                    "ua": now_ts,
                },
            )
            await db.commit()
        prof = await self.get(rid, tenant_id=tid)
        if prof is None:  # pragma: no cover - defensive
            raise ICPError("inserted profile not visible after write")
        return prof

    async def update(self, profile_id: str, *, tenant_id: str, **patch) -> ICPProfile:
        existing = await self.get(profile_id, tenant_id=tenant_id)
        if existing is None:
            raise KeyError("icp profile not found")

        merged = {
            "industries": patch.get("industries", existing.criteria.industries),
            "cities": patch.get("cities", existing.criteria.cities),
            "employees_min": patch.get("employees_min", existing.criteria.employees_min),
            "employees_max": patch.get("employees_max", existing.criteria.employees_max),
            "titles": patch.get("titles", existing.criteria.titles),
            "keywords": patch.get("keywords", existing.criteria.keywords),
        }
        w_in = patch.get("weights")
        w_eff = (
            {
                "industry": w_in.get("industry", existing.weights.industry),
                "city": w_in.get("city", existing.weights.city),
                "employees": w_in.get("employees", existing.weights.employees),
                "titles": w_in.get("titles", existing.weights.titles),
                "keywords": w_in.get("keywords", existing.weights.keywords),
            }
            if w_in is not None
            else existing.weights.as_dict()  # absent weights = unchanged, never reset
        )
        v = self._validated(
            tenant_id=tenant_id,
            name=patch.get("name") or existing.name,
            description="",
            industries=merged["industries"],
            cities=merged["cities"],
            employees_min=merged["employees_min"],
            employees_max=merged["employees_max"],
            titles=merged["titles"],
            keywords=merged["keywords"],
            weights=w_eff,
        )
        bump = bool(patch.get("bump_version", True))
        ver = existing.schema_version + 1 if bump else existing.schema_version
        active = existing.is_active if patch.get("is_active") is None else bool(patch["is_active"])
        desc = (
            existing.description
            if patch.get("description") is None
            else str(patch["description"]).strip()
        )

        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text(
                    "UPDATE icp_profiles SET name=:n, description=:d, "
                    "criteria=CAST(:c AS jsonb), weights=CAST(:w AS jsonb), "
                    "schema_version=:v, "
                    "is_active=:a, updated_at=:ua WHERE id=:i"
                ),
                {
                    "n": str(patch.get("name") or existing.name),
                    "d": desc,
                    "c": json.dumps(v["criteria"]),
                    "w": json.dumps(v["weights"]),
                    "v": ver,
                    "a": active,
                    "ua": datetime.fromisoformat(_now_iso()),
                    "i": str(profile_id),
                },
            )
            if res.rowcount == 0:
                raise KeyError("icp profile not found")
            await db.commit()
        updated = await self.get(profile_id, tenant_id=tenant_id)
        if updated is None:  # pragma: no cover - defensive
            raise KeyError("icp profile not found")
        return updated

    # ── reads ─────────────────────────────────────────────────────────
    async def get(self, profile_id: str, *, tenant_id: str):
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text(
                    "SELECT id, tenant_id::text AS tenant_id, name, description, "
                    "criteria, weights, schema_version, is_active, "
                    "created_at::text AS created_at, updated_at::text AS updated_at "
                    "FROM icp_profiles WHERE id = :i"
                ),
                {"i": str(profile_id)},
            )
            row = res.first()
        return self._row_to_profile(row) if row else None

    async def delete(self, profile_id: str, *, tenant_id: str) -> bool:
        """Hard delete scoped by the tenant GUC; returns True if a row went."""
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text("DELETE FROM icp_profiles WHERE id = :i"),
                {"i": str(profile_id)},
            )
            await db.commit()
        return bool(res.rowcount)

    async def list_for_tenant(self, *, tenant_id: str) -> list[ICPProfile]:
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text(
                    "SELECT id, tenant_id::text AS tenant_id, name, description, "
                    "criteria, weights, schema_version, is_active, "
                    "created_at::text AS created_at, updated_at::text AS updated_at "
                    "FROM icp_profiles ORDER BY updated_at DESC"
                )
            )
            rows = res.all()
        return [self._row_to_profile(r) for r in rows]

    async def list_active(self, *, tenant_id: str) -> list[ICPProfile]:
        return [p for p in await self.list_for_tenant(tenant_id=tenant_id) if p.is_active]


def active_profiles_from(profiles: list[ICPProfile]) -> list[ICPProfile]:
    """Pure mirror of intelligence.agents.icp._active_profiles filter.

    Kept beside the repository so the future runtime swap preserves the exact
    contract the grounded ICP/recommendation agents rely on."""
    return [p for p in profiles if p.is_active]


_logger = logging.getLogger("salesos.icp.persistence")


class SyncICPStore:
    """Synchronous facade over PostgresICPRepository (ADR-0109 Option A).

    The frozen grounded agents consume the store synchronously
    (`_active_profiles(store, tenant)`), while this runtime is async and is
    often called from inside FastAPI's running loop — so coroutines execute on
    a private loop in a daemon thread. Read failures are contained to an empty
    result + warning log: agents then degrade via their honest no-profile /
    INSUFFICIENT contracts instead of raising. Write methods propagate errors.
    """

    _CALL_TIMEOUT_S = 15

    def __init__(self, repo: PostgresICPRepository | None = None):
        if repo is not None:
            self._repo = repo
            self._engine = None
        else:
            # Dedicated engine on the adapter's private loop: never share the
            # global app pool across event loops (asyncpg binds connections to
            # the loop that created them). NullPool → zero reuse surprises.
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
            from sqlalchemy.pool import NullPool

            from app.config import settings

            self._engine = create_async_engine(
                settings.app_database_url, poolclass=NullPool, pool_pre_ping=True
            )
            factory = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )
            self._repo = PostgresICPRepository(factory)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="icp-sync-adapter",
        )
        self._thread.start()

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(
            coro, self._loop
        ).result(timeout=self._CALL_TIMEOUT_S)

    def close(self) -> None:
        # dispose the engine while the loop is still running, then stop it
        if self._engine is not None:
            asyncio.run_coroutine_threadsafe(self._engine.dispose(), self._loop).result(
                timeout=10
            )
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)

    # ── reads (error-contained) ──────────────────────────────────────────

    def get(self, profile_id: str, *, tenant_id: str):
        try:
            return self._run(self._repo.get(profile_id, tenant_id=tenant_id))
        except Exception as exc:
            _logger.warning("SyncICPStore.get degraded to None: %s", exc)
            return None

    def list_for_tenant(self, *, tenant_id: str) -> list[ICPProfile]:
        try:
            return self._run(self._repo.list_for_tenant(tenant_id=tenant_id))
        except Exception as exc:
            _logger.warning("SyncICPStore.list_for_tenant degraded to []: %s", exc)
            return []

    def list_active(self, *, tenant_id: str) -> list[ICPProfile]:
        try:
            return self._run(self._repo.list_active(tenant_id=tenant_id))
        except Exception as exc:
            _logger.warning("SyncICPStore.list_active degraded to []: %s", exc)
            return []

    # ── writes (propagate) ───────────────────────────────────────────────

    def create(self, **kwargs) -> ICPProfile:
        return self._run(self._repo.create(**kwargs))

    def update(self, profile_id: str, tenant_id: str, /, **kwargs) -> ICPProfile:
        return self._run(
            self._repo.update(profile_id, tenant_id=tenant_id, **kwargs)
        )


_sync_store_lock = threading.Lock()
_sync_store_instance: SyncICPStore | None = None


def get_sync_icp_store() -> SyncICPStore:
    """Process-wide adapter singleton for agent registration paths."""
    global _sync_store_instance
    with _sync_store_lock:
        if _sync_store_instance is None:
            _sync_store_instance = SyncICPStore()
        return _sync_store_instance
