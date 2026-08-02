"""STORY-11-05 — In-memory enrichment runs (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.enrichment import (
    ENRICHABLE_FIELDS,
    EnrichmentError,
    EnrichmentResult,
    normalize_request,
)
from app.modules.gtm.enrichment_engine import (
    EnrichmentProvider,
    build_default_providers,
    run_waterfall,
)


@dataclass
class MemEnrichmentStore:
    """Tenant-scoped enrichment waterfall runs for CAP-099."""

    _by_id: dict[str, EnrichmentResult] = field(default_factory=dict)
    _providers: list[EnrichmentProvider] = field(default_factory=build_default_providers)

    def bind_providers(self, providers: list[EnrichmentProvider]) -> None:
        if len(providers) < 2:
            raise EnrichmentError("at least 2 enrichment providers required")
        self._providers = list(providers)

    def provider_keys(self) -> list[str]:
        return [p.provider_key for p in self._providers]

    async def enrich(
        self,
        *,
        tenant_id: str,
        company_name: str,
        domain: str | None = None,
        external_id: str | None = None,
        known: dict | None = None,
        provider_order: list[str] | None = None,
        run_id: str | None = None,
    ) -> EnrichmentResult:
        tid = (tenant_id or "").strip()
        if not tid:
            raise EnrichmentError("tenant_id required")

        request = normalize_request(
            company_name=company_name,
            domain=domain,
            external_id=external_id,
            known=known,
            provider_order=provider_order,
        )
        filled, hits, attempted, configured = await run_waterfall(request, self._providers)
        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant enrichment write blocked")

        missing_fields = [f for f in ENRICHABLE_FIELDS if f not in filled]
        result = EnrichmentResult(
            id=rid,
            tenant_id=tid,
            request=request,
            filled=filled,
            hits=hits,
            providers_attempted=attempted,
            providers_configured=configured,
            missing_fields=missing_fields,
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._by_id[result.id] = result
        return result

    def get(self, run_id: str, *, tenant_id: str) -> EnrichmentResult | None:
        row = self._by_id.get(str(run_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[EnrichmentResult]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.created_at or "",
            reverse=True,
        )


DEFAULT_ENRICHMENT_STORE = MemEnrichmentStore()
