"""Postgres-backed evidence + signals store with RLS tenant isolation.

Replaces in-memory EvidenceStore for production use.
Pattern follows icp_persistence.py and signal_marketplace/runtime_bridge.py.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ChannelType,
    CompanyIntelSummary,
    EvidenceItem,
    EvidenceType,
    Signal,
    SignalConfidence,
    SignalType,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceWriteResult:
    """The persisted evidence identifier and whether this call inserted it."""

    evidence_id: str
    inserted: bool


def _fingerprint(company_name: str, source_url: str, evidence_type: str) -> str:
    """Deterministic dedup fingerprint."""
    raw = f"{company_name.lower().strip()}|{source_url.strip()}|{evidence_type}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _signal_fingerprint(company_name: str, signal_type: str, title: str) -> str:
    """Deterministic signal dedup fingerprint."""
    raw = f"{company_name.lower().strip()}|{signal_type}|{title.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class PostgresEvidenceStore:
    """Async Postgres store for evidence + signals.

    All queries set app.tenant_id GUC for RLS isolation.
    Dedup via unique fingerprint constraints.
    Freshness via expires_at + TTL indexes.
    """

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def _pin_tenant(self, session: AsyncSession, tenant_id: str) -> None:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": str(tenant_id)},
        )

    # ── Evidence ───────────────────────────────────────────────────

    async def add_evidence(
        self,
        tenant_id: str,
        item: EvidenceItem,
        ttl_days: int = 90,
    ) -> bool:
        """Insert evidence item. Returns True if inserted, False if dedup hit."""
        try:
            result = await self.save_evidence(tenant_id, item, ttl_days=ttl_days)
            return result.inserted
        except Exception:
            return False

    async def save_evidence(
        self,
        tenant_id: str,
        item: EvidenceItem,
        ttl_days: int = 90,
    ) -> EvidenceWriteResult:
        """Persist evidence and return the canonical row ID, including on dedup."""
        fp = _fingerprint(item.company_name, item.source_url, item.evidence_type.value)
        expires_at = datetime.now(UTC) + timedelta(days=ttl_days)

        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            try:
                result = await session.execute(
                    text(
                        """
                        INSERT INTO agent_evidence
                            (id, tenant_id, company_name, evidence_type, channel,
                             source_url, title, summary, raw_data, confidence,
                             fingerprint, collected_at, expires_at, metadata)
                        VALUES
                            (CAST(:evidence_id AS uuid), :tenant_id, :company_name,
                             :evidence_type, :channel, :source_url, :title, :summary,
                             :raw_data, :confidence, :fingerprint, :collected_at,
                             :expires_at, :metadata)
                        ON CONFLICT (tenant_id, company_name, source_url, evidence_type)
                        DO NOTHING
                        RETURNING id, TRUE AS inserted
                        """
                    ),
                    {
                        "evidence_id": item.id,
                        "tenant_id": tenant_id,
                        "company_name": item.company_name,
                        "evidence_type": item.evidence_type.value,
                        "channel": item.channel.value,
                        "source_url": item.source_url,
                        "title": item.title,
                        "summary": item.summary,
                        "raw_data": json.dumps(item.raw_data) if item.raw_data else None,
                        "confidence": item.confidence,
                        "fingerprint": fp,
                        "collected_at": item.collected_at,
                        "expires_at": expires_at,
                        "metadata": json.dumps(item.metadata),
                    },
                )
                row = result.one_or_none()
                if row is None:
                    result = await session.execute(
                        text(
                            """
                            SELECT id, FALSE AS inserted FROM agent_evidence
                            WHERE tenant_id = :tenant_id
                              AND company_name = :company_name
                              AND source_url = :source_url
                              AND evidence_type = :evidence_type
                            """
                        ),
                        {
                            "tenant_id": tenant_id,
                            "company_name": item.company_name,
                            "source_url": item.source_url,
                            "evidence_type": item.evidence_type.value,
                        },
                    )
                    row = result.one_or_none()
                if row is None:
                    raise RuntimeError("Evidence insert/dedup did not return a row")
                await session.commit()
                return EvidenceWriteResult(
                    evidence_id=str(row.id), inserted=bool(row.inserted)
                )
            except Exception:
                await session.rollback()
                logger.exception("add_evidence failed for %s", item.company_name)
                raise

    async def get_evidence(
        self,
        tenant_id: str,
        company_name: str,
        include_expired: bool = False,
    ) -> list[EvidenceItem]:
        """Get all evidence for a company (RLS-scoped)."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            where = "company_name = :company_name"
            if not include_expired:
                where += " AND (expires_at IS NULL OR expires_at > now())"
            rows = await session.execute(
                text(f"SELECT * FROM agent_evidence WHERE {where} ORDER BY collected_at DESC"),
                {"company_name": company_name},
            )
            return [self._row_to_evidence(r) for r in rows]

    async def prune_expired(self, tenant_id: str) -> int:
        """Delete expired evidence. Returns count removed."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            result = await session.execute(
                text("DELETE FROM agent_evidence WHERE expires_at IS NOT NULL AND expires_at < now()")
            )
            await session.commit()
            return result.rowcount or 0

    # ── Signals ────────────────────────────────────────────────────

    async def add_signal(
        self,
        tenant_id: str,
        signal: Signal,
        ttl_days: int = 180,
    ) -> bool:
        """Insert signal. Returns True if inserted, False if dedup hit."""
        fp = _signal_fingerprint(signal.company_name, signal.signal_type.value, signal.title)
        expires_at = datetime.now(UTC) + timedelta(days=ttl_days)

        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            try:
                result = await session.execute(
                    text(
                        """
                        WITH existing AS (
                            SELECT 1 FROM agent_signals
                            WHERE tenant_id = :tenant_id
                              AND company_name = :company_name
                              AND signal_type = :signal_type
                              AND title = :title
                        )
                        INSERT INTO agent_signals
                            (tenant_id, company_name, signal_type, confidence,
                             title, description, source_urls, evidence_ids,
                             fingerprint, detected_at, expires_at, metadata)
                        SELECT
                            :tenant_id, :company_name, :signal_type, :confidence,
                            :title, :description, :source_urls, :evidence_ids,
                            :fingerprint, :detected_at, :expires_at, :metadata
                        WHERE NOT EXISTS (SELECT 1 FROM existing)
                        """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "company_name": signal.company_name,
                        "signal_type": signal.signal_type.value,
                        "confidence": signal.confidence.value,
                        "title": signal.title,
                        "description": signal.description,
                        "source_urls": json.dumps(signal.source_urls),
                        "evidence_ids": json.dumps(signal.evidence_ids),
                        "fingerprint": fp,
                        "detected_at": signal.detected_at,
                        "expires_at": expires_at,
                        "metadata": json.dumps(signal.metadata),
                    },
                )
                await session.commit()
                return (result.rowcount or 0) > 0
            except Exception:
                await session.rollback()
                logger.exception("add_signal failed for %s", signal.company_name)
                return False

    async def get_signals(
        self,
        tenant_id: str,
        company_name: str,
        include_expired: bool = False,
    ) -> list[Signal]:
        """Get all signals for a company (RLS-scoped)."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            where = "company_name = :company_name"
            if not include_expired:
                where += " AND (expires_at IS NULL OR expires_at > now())"
            rows = await session.execute(
                text(f"SELECT * FROM agent_signals WHERE {where} ORDER BY detected_at DESC"),
                {"company_name": company_name},
            )
            return [self._row_to_signal(r) for r in rows]

    async def prune_expired_signals(self, tenant_id: str) -> int:
        """Delete expired signals. Returns count removed."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            result = await session.execute(
                text("DELETE FROM agent_signals WHERE expires_at IS NOT NULL AND expires_at < now()")
            )
            await session.commit()
            return result.rowcount or 0

    # ── Summary ────────────────────────────────────────────────────

    async def get_summary(
        self,
        tenant_id: str,
        company_name: str,
    ) -> CompanyIntelSummary:
        """Aggregated intelligence summary."""
        evidence = await self.get_evidence(tenant_id, company_name)
        signals = await self.get_signals(tenant_id, company_name)
        channels = list({e.channel.value for e in evidence})
        last = max((e.collected_at for e in evidence), default=None)
        return CompanyIntelSummary(
            company_name=company_name,
            evidence_count=len(evidence),
            signal_count=len(signals),
            evidence=evidence,
            signals=signals,
            channels_searched=channels,
            last_researched=last,
        )

    async def list_companies(self, tenant_id: str) -> list[str]:
        """List all companies with stored intelligence (RLS-scoped)."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            rows = await session.execute(
                text(
                    "SELECT DISTINCT company_name FROM agent_evidence "
                    "UNION SELECT DISTINCT company_name FROM agent_signals "
                    "ORDER BY company_name"
                )
            )
            return [r[0] for r in rows]

    async def clear(self, tenant_id: str, company_name: str | None = None) -> int:
        """Clear evidence/signals. Returns count removed."""
        async with self._session_factory() as session:
            await self._pin_tenant(session, tenant_id)
            total = 0
            if company_name:
                r1 = await session.execute(
                    text("DELETE FROM agent_evidence WHERE company_name = :c"),
                    {"c": company_name},
                )
                r2 = await session.execute(
                    text("DELETE FROM agent_signals WHERE company_name = :c"),
                    {"c": company_name},
                )
                total = (r1.rowcount or 0) + (r2.rowcount or 0)
            else:
                r1 = await session.execute(text("DELETE FROM agent_evidence"))
                r2 = await session.execute(text("DELETE FROM agent_signals"))
                total = (r1.rowcount or 0) + (r2.rowcount or 0)
            await session.commit()
            return total

    # ── Row mappers ────────────────────────────────────────────────

    @staticmethod
    def _row_to_evidence(row: Any) -> EvidenceItem:
        raw = row.raw_data
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass  # keep as string
        meta = row.metadata
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        ch = row.channel
        try:
            ch_enum = ChannelType(ch)
        except ValueError:
            ch_enum = ChannelType.WEB
        return EvidenceItem(
            id=str(row.id),
            company_name=row.company_name,
            evidence_type=EvidenceType(row.evidence_type),
            channel=ch_enum,
            source_url=row.source_url or "",
            title=row.title or "",
            summary=row.summary or "",
            confidence=row.confidence or 0.0,
            collected_at=row.collected_at,
            metadata=meta or {},
        )

    @staticmethod
    def _row_to_signal(row: Any) -> Signal:
        src = row.source_urls
        if isinstance(src, str):
            try:
                src = json.loads(src)
            except (json.JSONDecodeError, TypeError):
                src = []
        ev = row.evidence_ids
        if isinstance(ev, str):
            try:
                ev = json.loads(ev)
            except (json.JSONDecodeError, TypeError):
                ev = []
        meta = row.metadata
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        return Signal(
            id=str(row.id),
            company_name=row.company_name,
            signal_type=SignalType(row.signal_type),
            confidence=SignalConfidence(row.confidence),
            title=row.title or "",
            description=row.description or "",
            source_urls=src or [],
            evidence_ids=ev or [],
            detected_at=row.detected_at,
            metadata=meta or {},
        )
