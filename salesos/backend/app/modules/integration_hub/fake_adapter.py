"""STORY-08-01 — In-memory FakeSourceConnector (certification reference).

Proves the interface is implementable with zero framework changes.
No network, no Odoo, no Stripe secrets. Not Production GO.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.modules.integration_hub.types import (
    ConnectionTestResult,
    IncrementalCursor,
    PullIncrementalResult,
    PullRecord,
    WriteBackRequest,
    WriteBackResult,
)


class FakeSourceConnector:
    """Reference adapter: dict store keyed by model → external_id."""

    def __init__(self, *, fail_connection: bool = False) -> None:
        self._fail_connection = fail_connection
        self._store: dict[str, dict[str, dict[str, Any]]] = {}
        self._seq: dict[str, int] = {}

    @property
    def connector_key(self) -> str:
        return "fake"

    async def test_connection(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
    ) -> ConnectionTestResult:
        _ = config
        started = time.perf_counter()
        if not (credential_ref or "").strip():
            return ConnectionTestResult(
                ok=False,
                message="credential_ref required",
                latency_ms=0.0,
            )
        if self._fail_connection:
            return ConnectionTestResult(
                ok=False,
                message="fake adapter forced failure",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        return ConnectionTestResult(
            ok=True,
            message="fake connection ok",
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    async def pull_incremental(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        cursor: IncrementalCursor | None,
        limit: int = 100,
    ) -> PullIncrementalResult:
        _ = credential_ref, config
        model_key = (model or "").strip()
        if not model_key:
            raise ValueError("model is required")
        lim = max(1, min(int(limit), 1000))
        after = int(cursor.watermark) if cursor and cursor.watermark.isdigit() else 0
        bucket = self._store.get(model_key, {})
        ordered = sorted(
            bucket.values(),
            key=lambda row: int(row.get("_seq", 0)),
        )
        selected = [row for row in ordered if int(row.get("_seq", 0)) > after][:lim]
        records = tuple(
            PullRecord(
                external_id=str(row["external_id"]),
                model=model_key,
                payload={k: v for k, v in row.items() if not k.startswith("_")},
                updated_at=row.get("_updated_at"),
            )
            for row in selected
        )
        if not records:
            return PullIncrementalResult(records=(), next_cursor=cursor, exhausted=True)
        last_seq = int(selected[-1]["_seq"])
        exhausted = len(selected) < lim or last_seq >= max(int(r.get("_seq", 0)) for r in ordered)
        return PullIncrementalResult(
            records=records,
            next_cursor=IncrementalCursor(watermark=str(last_seq)),
            exhausted=exhausted,
        )

    async def write_back(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        request: WriteBackRequest,
    ) -> WriteBackResult:
        _ = credential_ref, config
        model_key = (request.model or "").strip()
        if not model_key:
            return WriteBackResult(ok=False, external_id="", message="model required")
        bucket = self._store.setdefault(model_key, {})
        ext_id = (request.external_id or "").strip() or str(uuid.uuid4())
        seq = self._seq.get(model_key, 0) + 1
        self._seq[model_key] = seq
        row = {
            **dict(request.payload),
            "external_id": ext_id,
            "_seq": seq,
            "_updated_at": datetime.now(UTC),
        }
        bucket[ext_id] = row
        return WriteBackResult(ok=True, external_id=ext_id, message="upserted")
