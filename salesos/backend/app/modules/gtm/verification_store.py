"""STORY-11-06 — In-memory contact verification runs (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.verification import (
    VerificationError,
    VerificationResult,
    normalize_request,
)
from app.modules.gtm.verification_engine import (
    MemVerificationConnector,
    VerificationConnector,
    run_verification,
)


@dataclass
class MemVerificationStore:
    """Tenant-scoped verification results for CAP-100."""

    _by_id: dict[str, VerificationResult] = field(default_factory=dict)
    _connectors: dict[str, VerificationConnector] = field(default_factory=dict)
    _default_key: str = "fake_verify"

    def __post_init__(self) -> None:
        if not self._connectors:
            default = MemVerificationConnector(key=self._default_key)
            self._connectors = {default.connector_key: default}

    def bind_connector(self, connector: VerificationConnector, *, default: bool = False) -> None:
        self._connectors[connector.connector_key] = connector
        if default or len(self._connectors) == 1:
            self._default_key = connector.connector_key

    def connector_keys(self) -> list[str]:
        return sorted(self._connectors.keys())

    def _resolve(self, provider_key: str) -> VerificationConnector:
        key = (provider_key or "").strip() or self._default_key
        conn = self._connectors.get(key)
        if conn is None:
            raise VerificationError(f"unknown verification connector: {key}")
        return conn

    async def verify(
        self,
        *,
        tenant_id: str,
        email: str | None = None,
        phone: str | None = None,
        provider_key: str | None = None,
        run_id: str | None = None,
    ) -> VerificationResult:
        tid = (tenant_id or "").strip()
        if not tid:
            raise VerificationError("tenant_id required")

        request = normalize_request(
            email=email,
            phone=phone,
            provider_key=provider_key,
        )
        connector = self._resolve(request.provider_key)
        verdicts = await run_verification(request, connector)

        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant verification write blocked")

        result = VerificationResult(
            id=rid,
            tenant_id=tid,
            request=request,
            verdicts=list(verdicts),
            provider_key=connector.connector_key,
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._by_id[result.id] = result
        return result

    def get(self, run_id: str, *, tenant_id: str) -> VerificationResult | None:
        row = self._by_id.get(str(run_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[VerificationResult]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.created_at or "",
            reverse=True,
        )


DEFAULT_VERIFICATION_STORE = MemVerificationStore()
