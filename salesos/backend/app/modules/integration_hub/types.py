"""STORY-08-01 — SourceConnector shared DTOs (vendor-neutral)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class IncrementalCursor:
    """Opaque incremental watermark — adapters own the encoding."""

    watermark: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PullRecord:
    external_id: str
    model: str
    payload: dict[str, Any]
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PullIncrementalResult:
    records: tuple[PullRecord, ...]
    next_cursor: IncrementalCursor | None
    exhausted: bool


@dataclass(frozen=True)
class WriteBackRequest:
    model: str
    payload: dict[str, Any]
    external_id: str | None = None


@dataclass(frozen=True)
class WriteBackResult:
    ok: bool
    external_id: str
    message: str = ""


@dataclass(frozen=True)
class ConnectionTestResult:
    ok: bool
    message: str
    latency_ms: float | None = None
