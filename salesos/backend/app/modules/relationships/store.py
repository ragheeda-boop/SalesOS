"""Postgres persistence for the Commercial Relationship Model.

Tenant-scoped typed relationship edges (reports_to, influences,
champion_for, blocks, introduced_by) persisted in
``commercial_relationship_edges`` (migration u1v2w3x4y5z6).

Isolation is enforced by DB RLS + FORCE RLS (canonical DEC-085 shape) AND by
pinning ``app.tenant_id`` around every statement here — defence in depth,
fail-closed, mirroring PostgresGtmStore / PostgresICPRepository.

Lifecycle: a row may be superseded (``superseded_at``). Re-creating an edge
with the same (edge_type, source, target) after supersession inserts a fresh
ACTIVE row (the partial unique index only guards non-superseded rows), so the
recorded history is never mutated.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.relationships.models import (
    EDGE_TYPE_SET,
    ENDPOINT_TYPE_SET,
    RelationshipEdge,
    normalize_edge,
)

ACTIVE_FILTER = "superseded_at IS NULL"
SUPERSEDED_FILTER = "superseded_at IS NOT NULL"


def _now() -> datetime:
    return datetime.now(UTC)


def _as_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 string for a timestamptz bind param (asyncpg rejects str)."""
    if value is None:
        return None
    return datetime.fromisoformat(value)


class RelationshipStore:
    """Async Postgres-backed store for tenant-scoped relationship edges."""

    def __init__(self, *, session_factory=None):
        self._sessions = session_factory

    # ── session / GUC (canonical DEC-085 defence in depth) ───────────────
    def _session_ctx(self):
        if self._sessions is not None:
            return self._sessions()
        from app.database import async_session

        return async_session()

    @staticmethod
    async def _pin(db, tenant_id: str) -> None:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": str(tenant_id)},
        )

    # ── row mapping ───────────────────────────────────────────────────────
    @staticmethod
    def _row_to_edge(row) -> RelationshipEdge:
        return RelationshipEdge(
            id=str(row.id),
            tenant_id=str(row.tenant_id),
            edge_type=str(row.edge_type),
            source_type=str(row.source_type),
            source_id=str(row.source_id),
            target_type=str(row.target_type),
            target_id=str(row.target_id),
            basis=str(row.basis),
            evidence=[dict(e) for e in (row.evidence or [])],
            confidence=float(row.confidence) if row.confidence is not None else None,
            observed_at=row.observed_at.isoformat() if row.observed_at else None,
            superseded_at=row.superseded_at.isoformat() if row.superseded_at else None,
            created_by=str(row.created_by or ""),
            created_at=row.created_at.isoformat() if row.created_at else "",
        )

    _SELECT_COLS = (
        "id, tenant_id, edge_type, source_type, source_id, "
        "target_type, target_id, basis, evidence, confidence, "
        "observed_at, superseded_at, created_by, created_at"
    )

    # ── create (idempotent) ───────────────────────────────────────────────
    async def create(
        self,
        *,
        tenant_id: str,
        edge_type: str,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        basis: str = "unknown",
        evidence: list[dict[str, Any]] | None = None,
        confidence: float | None = None,
        observed_at: str | None = None,
        created_by: str = "",
        edge_id: str | None = None,
    ) -> RelationshipEdge:
        edge = normalize_edge(
            tenant_id=tenant_id,
            edge_type=edge_type,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            basis=basis,
            evidence=evidence,
            confidence=confidence,
            observed_at=observed_at,
            created_by=created_by,
            edge_id=edge_id,
        )
        now = _now()
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            try:
                await db.execute(
                    text(
                        f"INSERT INTO commercial_relationship_edges "
                        f"({self._SELECT_COLS}) "
                        f"VALUES (:id, CAST(:t AS uuid), :et, :st, :sid, :tt, :tid, "
                        f":b, CAST(:ev AS jsonb), :conf, :obs, NULL, :cb, :ca)"
                    ),
                    {
                        "id": edge.id,
                        "t": tenant_id,
                        "et": edge.edge_type,
                        "st": edge.source_type,
                        "sid": edge.source_id,
                        "tt": edge.target_type,
                        "tid": edge.target_id,
                        "b": edge.basis,
                        "ev": json.dumps(edge.evidence),
                        "conf": edge.confidence,
                        "obs": _as_datetime(edge.observed_at),
                        "cb": edge.created_by,
                        "ca": now,
                    },
                )
                await db.commit()
            except IntegrityError as exc:
                # Duplicate ACTIVE edge or hidden cross-tenant row — RLS hides
                # other tenants, so we surface the existing visible row (or a
                # cross-tenant write-block) instead of a raw 500.
                await db.rollback()
                # rollback() ends the transaction and discards the
                # transaction-local app.tenant_id GUC — re-pin or the recovery
                # SELECT below would be filtered to zero rows by FORCE RLS.
                await self._pin(db, tenant_id)
                res = await db.execute(
                    text(
                        f"SELECT {self._SELECT_COLS} FROM commercial_relationship_edges "
                        f"WHERE tenant_id = CAST(:t AS uuid) AND edge_type = :et "
                        f"AND source_type = :st AND source_id = :sid "
                        f"AND target_type = :tt AND target_id = :tid "
                        f"AND {ACTIVE_FILTER}"
                    ),
                    {
                        "t": tenant_id,
                        "et": edge.edge_type,
                        "st": edge.source_type,
                        "sid": edge.source_id,
                        "tt": edge.target_type,
                        "tid": edge.target_id,
                    },
                )
                row = res.first()
                if row is not None:
                    return self._row_to_edge(row)
                # Under RLS the row is invisible → cross-tenant collision.
                await db.rollback()
                raise PermissionError("cross-tenant relationship write blocked") from exc
        return edge

    # ── reads ─────────────────────────────────────────────────────────────
    async def get(self, edge_id: str, *, tenant_id: str) -> RelationshipEdge | None:
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text(
                    f"SELECT {self._SELECT_COLS} FROM commercial_relationship_edges "
                    "WHERE id = :i AND tenant_id = CAST(:t AS uuid)"
                ),
                {"i": str(edge_id), "t": tenant_id},
            )
            row = res.first()
        return self._row_to_edge(row) if row is not None else None

    async def list(
        self,
        *,
        tenant_id: str,
        edge_type: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        include_superseded: bool = False,
        limit: int = 500,
    ) -> list[RelationshipEdge]:
        where = ["tenant_id = CAST(:t AS uuid)"]
        params: dict[str, Any] = {"t": tenant_id}
        if edge_type:
            etype = str(edge_type).strip()
            if etype not in EDGE_TYPE_SET:
                raise ValueError(
                    f"invalid edge_type '{etype}'; expected one of {sorted(EDGE_TYPE_SET)}"
                )
            where.append("edge_type = :et")
            params["et"] = etype
        if source_type:
            stype = str(source_type).strip().lower()
            if stype not in ENDPOINT_TYPE_SET:
                raise ValueError(f"invalid source_type '{stype}'; expected person|company")
            where.append("source_type = :st")
            params["st"] = stype
        if source_id:
            where.append("source_id = :sid")
            params["sid"] = str(source_id)
        if target_type:
            ttype = str(target_type).strip().lower()
            if ttype not in ENDPOINT_TYPE_SET:
                raise ValueError(f"invalid target_type '{ttype}'; expected person|company")
            where.append("target_type = :tt")
            params["tt"] = ttype
        if target_id:
            where.append("target_id = :tid")
            params["tid"] = str(target_id)
        if not include_superseded:
            where.append(ACTIVE_FILTER)
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text(
                    f"SELECT {self._SELECT_COLS} FROM commercial_relationship_edges "
                    "WHERE " + " AND ".join(where)
                    + " ORDER BY created_at DESC LIMIT :lim"
                ),
                {**params, "lim": int(limit)},
            )
            rows = res.all()
        return [self._row_to_edge(r) for r in rows]

    # ── lifecycle: supersede ──────────────────────────────────────────────
    async def supersede(self, edge_id: str, *, tenant_id: str) -> RelationshipEdge | None:
        now = _now()
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            res = await db.execute(
                text(
                    "UPDATE commercial_relationship_edges SET superseded_at = :sa, "
                    "updated_at = :ua "
                    "WHERE id = :i AND tenant_id = CAST(:t AS uuid) "
                    f"AND {ACTIVE_FILTER} "
                    "RETURNING "
                    + self._SELECT_COLS
                ),
                {"sa": now, "ua": now, "i": str(edge_id), "t": tenant_id},
            )
            row = res.first()
            await db.commit()
        return self._row_to_edge(row) if row is not None else None

    # ── summary convenience (no cross-tenant aggregation, always pinned) ──
    async def count_active(self, *, tenant_id: str, edge_type: str | None = None) -> int:
        etype = str(edge_type or "").strip() or None
        if etype is not None and etype not in EDGE_TYPE_SET:
            raise ValueError(
                f"invalid edge_type '{etype}'; expected one of {sorted(EDGE_TYPE_SET)}"
            )
        async with self._session_ctx() as db:
            await self._pin(db, tenant_id)
            if etype is not None:
                res = await db.execute(
                    text(
                        "SELECT count(*) FROM commercial_relationship_edges "
                        "WHERE tenant_id = CAST(:t AS uuid) AND edge_type = :et "
                        f"AND {ACTIVE_FILTER}"
                    ),
                    {"t": tenant_id, "et": etype},
                )
            else:
                res = await db.execute(
                    text(
                        "SELECT count(*) FROM commercial_relationship_edges "
                        "WHERE tenant_id = CAST(:t AS uuid) AND "
                        + ACTIVE_FILTER
                    ),
                    {"t": tenant_id},
                )
            row = res.first()
        return int(row[0]) if row is not None else 0