"""Tenant-safe projection for a user-visible Commercial Memory viewer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable


@dataclass(frozen=True)
class MemoryViewItem:
    memory_id: str
    entity_id: str
    summary: str
    source: str
    observed_at: datetime
    confidence: float
    outcome: str | None = None


def project_memory(items: Iterable[MemoryViewItem]) -> list[dict[str, Any]]:
    """Expose provenance and outcomes while excluding raw provider payloads."""
    return [
        {
            "memory_id": item.memory_id,
            "entity_id": item.entity_id,
            "summary": item.summary,
            "source": item.source,
            "observed_at": item.observed_at.astimezone(UTC).isoformat(),
            "confidence": max(0.0, min(1.0, item.confidence)),
            "outcome": item.outcome,
        }
        for item in sorted(items, key=lambda value: value.observed_at, reverse=True)
    ]
