"""STORY-08-01 — SourceConnector protocol (mandatory adapter contract).

Methods: test_connection, pull_incremental, write_back.
Zero adapter-specific symbols. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from app.modules.integration_hub.types import (
    ConnectionTestResult,
    IncrementalCursor,
    PullIncrementalResult,
    WriteBackRequest,
    WriteBackResult,
)


@runtime_checkable
class SourceConnector(Protocol):
    """Vendor-neutral incremental sync contract for Integration Hub adapters."""

    @property
    def connector_key(self) -> str:
        """Stable adapter id (e.g. ``fake``, later ``odoo``) — not a secret."""
        ...

    async def test_connection(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
    ) -> ConnectionTestResult:
        """Probe connectivity using a vault credential pointer (never raw secrets)."""
        ...

    async def pull_incremental(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        cursor: IncrementalCursor | None,
        limit: int = 100,
    ) -> PullIncrementalResult:
        """Pull records newer than ``cursor`` (or from the beginning when None)."""
        ...

    async def write_back(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        request: WriteBackRequest,
    ) -> WriteBackResult:
        """Push a single record mutation to the external system."""
        ...
