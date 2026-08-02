"""STORY-11-03 — In-memory lead discovery runs (no Alembic / FORCE RLS).

Government universe first; Integration Hub FakeSourceConnector as provider fallback.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.lead_discovery import (
    LeadDiscoveryError,
    LeadDiscoveryRun,
    normalize_query,
)
from app.modules.gtm.lead_discovery_engine import discover_leads
from app.modules.gtm.market_sizing import GOVERNMENT_DATASET_SCALE_HINT
from app.modules.gtm.market_sizing_engine import MemCompanyUniverse
from app.modules.gtm.market_sizing_store import build_demo_government_universe
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.source_connector import SourceConnector
from app.modules.integration_hub.types import WriteBackRequest


async def seed_fake_provider_companies(
    adapter: FakeSourceConnector,
    *,
    rows: list[dict[str, object]] | None = None,
) -> FakeSourceConnector:
    """Seed FakeSourceConnector with company payloads for provider-fallback tests."""
    default_rows: list[dict[str, object]] = [
        {
            "external_id": "ext-tech-1",
            "name": "Provider Tech Riyadh",
            "industry": "technology",
            "city": "riyadh",
            "employees_count": 75,
        },
        {
            "external_id": "ext-tech-2",
            "name": "Provider Tech Jeddah",
            "industry": "technology",
            "city": "jeddah",
            "employees_count": 40,
        },
        {
            "external_id": "ext-con-1",
            "name": "Provider Construction",
            "industry": "construction",
            "city": "dammam",
            "employees_count": 200,
        },
    ]
    for row in rows if rows is not None else default_rows:
        ext_id = str(row.get("external_id") or "")
        payload = {k: v for k, v in row.items() if k != "external_id"}
        await adapter.write_back(
            credential_ref="vault://fake/lead-discovery",
            config={},
            request=WriteBackRequest(
                model="company",
                payload=payload,
                external_id=ext_id or None,
            ),
        )
    return adapter


@dataclass
class MemLeadDiscoveryStore:
    """Tenant-scoped discovery runs for CAP-097."""

    _by_id: dict[str, LeadDiscoveryRun] = field(default_factory=dict)
    _universe: MemCompanyUniverse = field(default_factory=build_demo_government_universe)
    _provider: SourceConnector | None = field(default=None)

    def bind_universe(self, universe: MemCompanyUniverse) -> None:
        self._universe = universe

    def bind_provider(self, provider: SourceConnector | None) -> None:
        self._provider = provider

    async def ensure_default_provider(self) -> SourceConnector:
        if self._provider is None:
            fake = FakeSourceConnector()
            await seed_fake_provider_companies(fake)
            self._provider = fake
        return self._provider

    async def discover(
        self,
        *,
        tenant_id: str,
        name: str,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
        limit: int | None = None,
        run_id: str | None = None,
        use_provider_fallback: bool = True,
    ) -> LeadDiscoveryRun:
        tid = (tenant_id or "").strip()
        if not tid:
            raise LeadDiscoveryError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise LeadDiscoveryError("name required")

        query = normalize_query(
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
            limit=limit,
        )
        provider: SourceConnector | None = None
        if use_provider_fallback:
            provider = await self.ensure_default_provider()

        leads, gov_n, prov_n, prov_key = await discover_leads(
            query=query,
            universe=self._universe,
            provider=provider,
            tenant_id=tid,
        )
        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant lead discovery write blocked")

        run = LeadDiscoveryRun(
            id=rid,
            tenant_id=tid,
            name=nm,
            query=query,
            leads=leads,
            government_hit_count=gov_n,
            provider_hit_count=prov_n,
            provider_key=prov_key,
            dataset_scale_hint=GOVERNMENT_DATASET_SCALE_HINT,
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=datetime.now(UTC).isoformat(),
        )
        if not run.government_first_ok:
            raise LeadDiscoveryError("government-first ordering invariant broken")
        self._by_id[run.id] = run
        return run

    def get(self, run_id: str, *, tenant_id: str) -> LeadDiscoveryRun | None:
        row = self._by_id.get(str(run_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[LeadDiscoveryRun]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.created_at or "",
            reverse=True,
        )


DEFAULT_LEAD_DISCOVERY_STORE = MemLeadDiscoveryStore()
