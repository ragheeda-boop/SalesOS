"""Deduplication logic for sync workers (ADR-012 §3)."""

from __future__ import annotations

import hashlib


class Deduplicator:
    """Detects duplicate communications during sync."""

    def __init__(self, known_ids: set[str] | None = None):
        self._known_ids = known_ids or set()

    def is_duplicate(self, identifier: str, known_ids: set[str] | None = None) -> bool:
        """Check if an identifier has already been processed."""
        ids = known_ids or self._known_ids
        return identifier in ids

    def add(self, identifier: str) -> None:
        """Mark an identifier as processed."""
        self._known_ids.add(identifier)

    @staticmethod
    def content_hash(subject: str, body: str, timestamp: str) -> str:
        """Generate a content-based hash for deduplication.

        Useful when message_id is not available or unreliable.
        """
        content = f"{subject}|{body}|{timestamp}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()[:16]

    @property
    def known_ids(self) -> set[str]:
        return self._known_ids
