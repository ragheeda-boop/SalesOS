"""Conflict resolution logic for sync workers (ADR-012 §3)."""

from __future__ import annotations

from intelligence.activity_intelligence.contracts.models import RawCalendarEvent


class ConflictResolver:
    """Resolves update conflicts during synchronization.

    Strategy: Last-write-wins (LWW) based on updated_at timestamps.
    """

    def has_conflict(
        self,
        raw_event: RawCalendarEvent,
        known_ids: set[str],
    ) -> bool:
        """Check if a raw event conflicts with an already-synced event.

        Currently implements LWW: no conflict if already processed.
        Future: compare timestamps and metadata for true conflicts.
        """
        # If already known, this is an update, not a conflict
        if raw_event.event_id in known_ids:
            return False

        # No conflict by default — we accept the latest data
        return False

    def resolve(
        self,
        local_version: dict,
        remote_version: dict,
    ) -> dict:
        """Resolve conflict between local and remote versions.

        Last-write-wins by default.
        Local `updated_at` wins over remote `updated_at`.
        """
        local_ts = local_version.get("updated_at", "")
        remote_ts = remote_version.get("updated_at", "")

        if local_ts >= remote_ts:
            return local_version
        return remote_version
