"""STORY-09-01 residual / EPIC-09 — unlinked cr_number badge list.

Surfaces Golden-Record join failures loudly for Studio Monitor (ARB silent-skip
risk). No new Alembic / FORCE RLS. No invented secrets. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.modules.integration_hub.cr_number_join import CrJoinResult
from app.modules.integration_hub.partner_sync import PartnerSyncBatchResult

KIND_UNLINKED_BADGE = "unlinked_badge"
BadgeStatus = Literal["unlinked", "invalid_cr"]


@dataclass(frozen=True)
class UnlinkedBadgeItem:
    external_id: str
    status: BadgeStatus
    cr_number: str | None = None
    message: str = ""
    model: str = "res.partner"
    sync_run_id: str | None = None
    recorded_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": KIND_UNLINKED_BADGE,
            "external_id": self.external_id,
            "status": self.status,
            "cr_number": self.cr_number,
            "message": self.message,
            "model": self.model,
            "sync_run_id": self.sync_run_id,
            "recorded_at": self.recorded_at,
        }


@dataclass
class MemUnlinkedBadgeStore:
    """In-memory badge ledger keyed by tenant + connection (unit / CAP-028)."""

    by_key: dict[str, list[UnlinkedBadgeItem]] = field(default_factory=dict)

    @staticmethod
    def _key(tenant_id: str, connection_id: str) -> str:
        return f"{tenant_id}:{connection_id}"

    def record(
        self,
        *,
        tenant_id: str,
        connection_id: str,
        items: Sequence[UnlinkedBadgeItem],
    ) -> None:
        key = self._key(str(tenant_id), str(connection_id))
        bucket = list(self.by_key.get(key) or [])
        seen = {(b.external_id, b.cr_number, b.status) for b in bucket}
        for item in items:
            sig = (item.external_id, item.cr_number, item.status)
            if sig in seen:
                continue
            seen.add(sig)
            bucket.append(item)
        self.by_key[key] = bucket

    def list_for_connection(
        self,
        *,
        tenant_id: str,
        connection_id: str,
        limit: int = 100,
    ) -> list[UnlinkedBadgeItem]:
        key = self._key(str(tenant_id), str(connection_id))
        rows = list(self.by_key.get(key) or [])
        lim = max(1, min(int(limit), 500))
        return rows[-lim:][::-1]  # newest-last storage → newest-first return


def badge_items_from_join_results(
    joins: Sequence[CrJoinResult],
    *,
    model: str = "res.partner",
    sync_run_id: str | None = None,
    recorded_at: datetime | None = None,
) -> list[UnlinkedBadgeItem]:
    at = (recorded_at or datetime.now(UTC)).isoformat()
    out: list[UnlinkedBadgeItem] = []
    for join in joins:
        if join.status not in ("unlinked", "invalid_cr"):
            continue
        out.append(
            UnlinkedBadgeItem(
                external_id=str(join.external_id),
                status=join.status,  # type: ignore[arg-type]
                cr_number=join.cr_number,
                message=join.message,
                model=model,
                sync_run_id=sync_run_id,
                recorded_at=at,
            )
        )
    return out


def badge_items_from_partner_batch(
    batch: PartnerSyncBatchResult,
    *,
    model: str = "res.partner",
    sync_run_id: str | None = None,
    recorded_at: datetime | None = None,
) -> list[UnlinkedBadgeItem]:
    return badge_items_from_join_results(
        [*batch.unlinked, *batch.invalid],
        model=model,
        sync_run_id=sync_run_id,
        recorded_at=recorded_at,
    )


def badge_dicts_for_error_log(items: Sequence[UnlinkedBadgeItem]) -> list[dict[str, Any]]:
    return [i.as_dict() for i in items]


def collect_unlinked_badges_from_error_logs(
    runs: Sequence[Any],
    *,
    limit: int = 100,
) -> list[UnlinkedBadgeItem]:
    """Extract unlinked_badge entries from SyncRun.error_log (newest first)."""
    lim = max(1, min(int(limit), 500))
    collected: list[UnlinkedBadgeItem] = []
    seen: set[tuple[str, str | None, str]] = set()
    for run in runs:
        sync_run_id = str(getattr(run, "id", "") or "") or None
        model = str(getattr(run, "model", "") or "res.partner")
        started = getattr(run, "started_at", None)
        recorded_at = started.isoformat() if hasattr(started, "isoformat") else None
        for raw in list(getattr(run, "error_log", None) or []):
            if not isinstance(raw, Mapping):
                continue
            if str(raw.get("kind") or "") != KIND_UNLINKED_BADGE:
                continue
            status = str(raw.get("status") or "")
            if status not in ("unlinked", "invalid_cr"):
                continue
            external_id = str(raw.get("external_id") or "")
            cr = raw.get("cr_number")
            cr_s = str(cr) if cr is not None else None
            sig = (external_id, cr_s, status)
            if not external_id or sig in seen:
                continue
            seen.add(sig)
            collected.append(
                UnlinkedBadgeItem(
                    external_id=external_id,
                    status=status,  # type: ignore[arg-type]
                    cr_number=cr_s,
                    message=str(raw.get("message") or ""),
                    model=str(raw.get("model") or model),
                    sync_run_id=str(raw.get("sync_run_id") or sync_run_id or "") or None,
                    recorded_at=str(raw.get("recorded_at") or recorded_at or "") or None,
                )
            )
            if len(collected) >= lim:
                return collected
    return collected
