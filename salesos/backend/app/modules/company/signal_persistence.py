"""Track F2: Company signal persistence — upsert, dedup, lifecycle.

Provides a persistence layer for company signals detected by the
company service. Handles idempotent upsert with first_seen / last_seen
tracking, status lifecycle, and tenant-scoped reads.

Design constraints:
- Signals are always computed first (fail-graceful), then persisted.
- If persistence fails, the transient compute result is returned.
- Dedup key: (tenant_id, company_id, signal_type) via UNIQUE constraint.
- first_seen_at is set on creation; last_seen_at is updated on every touch.
"""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Lifecycle states ─────────────────────────────────────────────
STATUS_ACTIVE = "active"
STATUS_ACKNOWLEDGED = "acknowledged"
STATUS_RESOLVED = "resolved"
STATUS_EXPIRED = "expired"

_LIFECYCLE = {STATUS_ACTIVE, STATUS_ACKNOWLEDGED, STATUS_RESOLVED, STATUS_EXPIRED}


async def upsert_signals(
    db: AsyncSession,
    *,
    tenant_id: str,
    company_id: str,
    signals: list[dict[str, Any]],
) -> int:
    """Persist detected signals for a company. Returns count persisted.

    Each signal dict must contain at least: type, severity, title.
    Optional: description, source, confidence_score, metadata.

    Uses INSERT ... ON CONFLICT to handle dedup:
    - New signal: insert with first_seen_at = now, last_seen_at = now
    - Existing signal: update last_seen_at, title, description, severity,
      metadata. first_seen_at is preserved.
    """
    if not signals:
        return 0

    now = datetime.now(UTC)
    persisted = 0

    for sig in signals:
        signal_type = sig.get("type", "unknown")
        title = sig.get("title", signal_type)
        severity = sig.get("severity", "info")
        description = sig.get("description")
        source = sig.get("source", "heuristic")
        confidence = sig.get("confidence_score")
        metadata = {k: v for k, v in sig.items()
                    if k not in ("type", "severity", "title", "description",
                                 "source", "confidence_score")}

        try:
            await db.execute(
                text("""
                    INSERT INTO company_signals
                        (tenant_id, company_id, signal_type, title, description,
                         severity, source, status, confidence_score,
                         first_seen_at, last_seen_at, metadata)
                    VALUES
                        (:tid, :cid, :stype, :title, :desc,
                         :sev, :src, :status, :conf,
                         :now, :now, :meta)
                    ON CONFLICT (tenant_id, company_id, signal_type)
                    DO UPDATE SET
                        last_seen_at = :now,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        severity = EXCLUDED.severity,
                        metadata = EXCLUDED.metadata,
                        updated_at = :now
                """),
                {
                    "tid": tenant_id,
                    "cid": company_id,
                    "stype": signal_type,
                    "title": title,
                    "desc": description,
                    "sev": severity,
                    "src": source,
                    "status": STATUS_ACTIVE,
                    "conf": confidence,
                    "now": now,
                    "meta": str(metadata) if metadata else "{}",
                },
            )
            persisted += 1
        except Exception as exc:
            logger.warning(
                "signal_persistence.upsert_failed",
                extra={"tenant_id": tenant_id, "company_id": company_id,
                       "signal_type": signal_type, "error": str(exc)},
            )

    await db.commit()
    return persisted


async def read_signals(
    db: AsyncSession,
    *,
    tenant_id: str,
    company_id: str,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Read persisted signals for a company. Returns list of dicts."""
    where = "WHERE tenant_id = :tid AND company_id = :cid"
    params: dict[str, Any] = {"tid": tenant_id, "cid": company_id, "limit": limit}

    if status:
        where += " AND status = :status"
        params["status"] = status

    try:
        result = await db.execute(
            text(f"""
                SELECT id, signal_type, title, description, severity,
                       source, status, confidence_score,
                       first_seen_at, last_seen_at, resolved_at,
                       metadata, created_at
                FROM company_signals
                {where}
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'positive' THEN 4
                        WHEN 'info' THEN 5
                        ELSE 6
                    END,
                    last_seen_at DESC
                LIMIT :limit
            """),
            params,
        )
        rows = result.mappings().all()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.warning(
            "signal_persistence.read_failed",
            extra={"tenant_id": tenant_id, "company_id": company_id,
                   "error": str(exc)},
        )
        return []


async def expire_stale_signals(
    db: AsyncSession,
    *,
    tenant_id: str,
    stale_days: int = 30,
) -> int:
    """Mark signals as expired if not seen in stale_days. Returns count."""
    try:
        result = await db.execute(
            text("""
                UPDATE company_signals
                SET status = :expired, updated_at = now(), resolved_at = now()
                WHERE tenant_id = :tid
                  AND status = :active
                  AND last_seen_at < now() - (:days || ' days')::interval
            """),
            {"expired": STATUS_EXPIRED, "tid": tenant_id,
             "active": STATUS_ACTIVE, "days": stale_days},
        )
        await db.commit()
        return result.rowcount
    except Exception as exc:
        logger.warning(
            "signal_persistence.expire_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )
        return 0


async def acknowledge_signal(
    db: AsyncSession,
    *,
    tenant_id: str,
    signal_id: str,
) -> bool:
    """Mark a signal as acknowledged. Returns True on success."""
    try:
        result = await db.execute(
            text("""
                UPDATE company_signals
                SET status = :status, updated_at = now()
                WHERE id = :sid AND tenant_id = :tid
            """),
            {"status": STATUS_ACKNOWLEDGED, "sid": signal_id, "tid": tenant_id},
        )
        await db.commit()
        return result.rowcount > 0
    except Exception:
        return False


async def resolve_signal(
    db: AsyncSession,
    *,
    tenant_id: str,
    signal_id: str,
) -> bool:
    """Mark a signal as resolved. Returns True on success."""
    try:
        result = await db.execute(
            text("""
                UPDATE company_signals
                SET status = :status, resolved_at = now(), updated_at = now()
                WHERE id = :sid AND tenant_id = :tid
            """),
            {"status": STATUS_RESOLVED, "sid": signal_id, "tid": tenant_id},
        )
        await db.commit()
        return result.rowcount > 0
    except Exception:
        return False


def signals_to_response(signals: list[dict]) -> dict:
    """Convert persisted signals to the CompanySignals response format."""
    items = []
    for s in signals:
        items.append({
            "id": str(s.get("id", "")),
            "type": s.get("signal_type", "unknown"),
            "severity": s.get("severity", "info"),
            "title": s.get("title", ""),
            "description": s.get("description"),
            "source": s.get("source", "heuristic"),
            "status": s.get("status", "active"),
            "confidence_score": s.get("confidence_score"),
            "first_seen_at": s.get("first_seen_at").isoformat() if s.get("first_seen_at") else None,
            "last_seen_at": s.get("last_seen_at").isoformat() if s.get("last_seen_at") else None,
        })
    return {"items": items, "total": len(items)}
