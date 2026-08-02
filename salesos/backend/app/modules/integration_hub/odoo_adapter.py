"""STORY-09-01..09-04 — OdooAdapter (partner, lead, message, helpdesk.ticket).

Vendor-specific code lives here only. Uses vault ``credential_ref`` +
non-secret config; never invents passwords. Injectable RPC for tests /
staging. Not Production GO.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

from app.modules.integration_hub.types import (
    ConnectionTestResult,
    IncrementalCursor,
    PullIncrementalResult,
    PullRecord,
    WriteBackRequest,
    WriteBackResult,
)


class OdooRpcClient(Protocol):
    """Minimal XML-RPC surface — real client wires staging credentials from vault."""

    async def ping(self, *, credential_ref: str, config: Mapping[str, Any]) -> None: ...

    async def search_read(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        domain: list[Any],
        fields: Sequence[str],
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]: ...

    async def write(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        external_id: str,
        values: Mapping[str, Any],
    ) -> str: ...

    async def create(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        values: Mapping[str, Any],
    ) -> str: ...


class InMemoryOdooRpc:
    """Certify / unit RPC — no network, no secrets."""

    def __init__(self, *, fail_ping: bool = False) -> None:
        self.fail_ping = fail_ping
        self._rows: dict[str, dict[str, dict[str, Any]]] = {}
        self._seq: dict[str, int] = {}
        self._clock = 0

    def _next_write_date(self) -> str:
        self._clock += 1
        # Monotonic ISO watermark so incremental cursors advance in tests.
        return f"2026-08-02T00:00:00.{self._clock:06d}+00:00"

    async def ping(self, *, credential_ref: str, config: Mapping[str, Any]) -> None:
        _ = config
        if not (credential_ref or "").strip():
            raise ConnectionError("credential_ref required")
        if self.fail_ping:
            raise ConnectionError("odoo sandbox unreachable")

    async def search_read(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        domain: list[Any],
        fields: Sequence[str],
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        _ = credential_ref, config, fields
        bucket = self._rows.get(model, {})
        ordered = sorted(bucket.values(), key=lambda r: str(r.get("write_date") or ""))
        # Domain support: [['write_date', '>', watermark], ['type', '=', 'opportunity']]
        for clause in domain:
            if not (isinstance(clause, list | tuple) and len(clause) == 3):
                continue
            field, op, value = clause[0], clause[1], clause[2]
            if field == "write_date" and op == ">":
                watermark = str(value)
                ordered = [r for r in ordered if str(r.get("write_date") or "") > watermark]
            elif op == "=":
                ordered = [r for r in ordered if r.get(field) == value]
        return list(ordered[offset : offset + limit])

    async def write(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        external_id: str,
        values: Mapping[str, Any],
    ) -> str:
        _ = credential_ref, config
        bucket = self._rows.setdefault(model, {})
        row = dict(bucket.get(external_id) or {"id": external_id})
        row.update(dict(values))
        row["id"] = external_id
        row["write_date"] = self._next_write_date()
        bucket[external_id] = row
        return external_id

    async def create(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        model: str,
        values: Mapping[str, Any],
    ) -> str:
        _ = credential_ref, config
        ext = str(values.get("id") or uuid.uuid4().int % 10_000_000)
        bucket = self._rows.setdefault(model, {})
        seq = self._seq.get(model, 0) + 1
        self._seq[model] = seq
        row = {
            **dict(values),
            "id": ext,
            "write_date": self._next_write_date(),
            "_seq": seq,
        }
        bucket[ext] = row
        return ext


_PARTNER_FIELDS = (
    "id",
    "name",
    "email",
    "phone",
    "is_company",
    "parent_id",
    "x_studio_cr_number",
    "write_date",
)

_OPPORTUNITY_FIELDS = (
    "id",
    "name",
    "type",
    "stage_id",
    "expected_revenue",
    "partner_id",
    "currency_id",
    "description",
    "write_date",
)

_MESSAGE_FIELDS = (
    "id",
    "subject",
    "body",
    "message_type",
    "model",
    "res_id",
    "author_id",
    "date",
    "write_date",
)

_TICKET_FIELDS = (
    "id",
    "name",
    "stage_id",
    "priority",
    "partner_id",
    "user_id",
    "description",
    "sla_deadline",
    "ticket_type",
    "write_date",
)


def _fields_for_model(model: str) -> tuple[str, ...]:
    key = (model or "").strip()
    if key == "crm.lead":
        return _OPPORTUNITY_FIELDS
    if key == "mail.message":
        return _MESSAGE_FIELDS
    if key == "helpdesk.ticket":
        return _TICKET_FIELDS
    return _PARTNER_FIELDS


class OdooAdapter:
    """SourceConnector for Odoo — partner, opportunity, notes, SupportTicket."""

    def __init__(
        self,
        *,
        rpc: OdooRpcClient | None = None,
        fail_connection: bool = False,
    ) -> None:
        self._rpc: OdooRpcClient = rpc or InMemoryOdooRpc(fail_ping=fail_connection)

    @property
    def connector_key(self) -> str:
        return "odoo"

    async def test_connection(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
    ) -> ConnectionTestResult:
        started = time.perf_counter()
        try:
            await self._rpc.ping(credential_ref=credential_ref, config=config)
        except Exception as exc:
            return ConnectionTestResult(
                ok=False,
                message=str(exc),
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        return ConnectionTestResult(
            ok=True,
            message="odoo connection ok",
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
        model_key = (model or "").strip() or "res.partner"
        lim = max(1, min(int(limit), 1000))
        domain: list[Any] = []
        if cursor and cursor.watermark:
            domain.append(["write_date", ">", cursor.watermark])
        # STORY-09-02: crm.lead opportunities only (exclude type=lead).
        if model_key == "crm.lead":
            domain.append(["type", "=", "opportunity"])
        rows = await self._rpc.search_read(
            credential_ref=credential_ref,
            config=config,
            model=model_key,
            domain=domain,
            fields=list(_fields_for_model(model_key)),
            limit=lim,
            offset=0,
        )
        records = tuple(
            PullRecord(
                external_id=str(row.get("id")),
                model=model_key,
                payload=dict(row),
                updated_at=_parse_dt(row.get("write_date")),
            )
            for row in rows
            if row.get("id") is not None
        )
        if not records:
            return PullIncrementalResult(records=(), next_cursor=cursor, exhausted=True)
        last_wd = records[-1].payload.get("write_date")
        if last_wd:
            next_c: IncrementalCursor | None = IncrementalCursor(watermark=str(last_wd))
        else:
            next_c = cursor
        return PullIncrementalResult(
            records=records,
            next_cursor=next_c,
            exhausted=len(records) < lim,
        )

    async def write_back(
        self,
        *,
        credential_ref: str,
        config: Mapping[str, Any],
        request: WriteBackRequest,
    ) -> WriteBackResult:
        model_key = (request.model or "").strip()
        if not model_key:
            return WriteBackResult(ok=False, external_id="", message="model required")
        try:
            if request.external_id:
                ext = await self._rpc.write(
                    credential_ref=credential_ref,
                    config=config,
                    model=model_key,
                    external_id=str(request.external_id),
                    values=request.payload,
                )
            else:
                ext = await self._rpc.create(
                    credential_ref=credential_ref,
                    config=config,
                    model=model_key,
                    values=request.payload,
                )
            return WriteBackResult(ok=True, external_id=str(ext), message="upserted")
        except Exception as exc:
            return WriteBackResult(ok=False, external_id="", message=str(exc))


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None
