"""STORY-11-02 — In-memory market sizing snapshots (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.market_sizing import (
    GOVERNMENT_DATASET_SCALE_HINT,
    CompanyRecord,
    MarketSizingError,
    MarketSizingSnapshot,
    normalize_criteria,
)
from app.modules.gtm.market_sizing_engine import (
    CompanyUniversePort,
    MemCompanyUniverse,
    compute_tam_sam_som,
)


def build_demo_government_universe() -> MemCompanyUniverse:
    """Deterministic fixture shaped like gov firmographics (not live 141221 rows)."""
    industries = ["technology", "construction", "healthcare", "retail", "energy"]
    cities = ["riyadh", "jeddah", "dammam", "khobar", "makkah"]
    rows: list[CompanyRecord] = []
    for i in range(250):
        rows.append(
            CompanyRecord(
                id=f"co-{i}",
                industry=industries[i % len(industries)],
                city=cities[i % len(cities)],
                employees_count=(i % 20) * 25 + 5,
                tenant_id="",  # shared government universe (not tenant-scoped)
            )
        )
    return MemCompanyUniverse(records=rows)


@dataclass
class MemMarketSizingStore:
    """Tenant-scoped TAM/SAM/SOM snapshots for CAP-096."""

    _by_id: dict[str, MarketSizingSnapshot] = field(default_factory=dict)
    _universe: CompanyUniversePort = field(default_factory=build_demo_government_universe)

    def bind_universe(self, universe: CompanyUniversePort) -> None:
        self._universe = universe

    def compute(
        self,
        *,
        tenant_id: str,
        name: str,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
        snapshot_id: str | None = None,
    ) -> MarketSizingSnapshot:
        tid = (tenant_id or "").strip()
        if not tid:
            raise MarketSizingError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise MarketSizingError("name required")

        criteria = normalize_criteria(
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
        )
        result = compute_tam_sam_som(criteria, self._universe, tenant_id=tid)
        rid = (snapshot_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant market sizing write blocked")

        snap = MarketSizingSnapshot(
            id=rid,
            tenant_id=tid,
            name=nm,
            criteria=criteria,
            tam=result.tam,
            sam=result.sam,
            som=result.som,
            universe_size=result.universe_size,
            dataset_scale_hint=GOVERNMENT_DATASET_SCALE_HINT,
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._by_id[snap.id] = snap
        return snap

    def get(self, snapshot_id: str, *, tenant_id: str) -> MarketSizingSnapshot | None:
        row = self._by_id.get(str(snapshot_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[MarketSizingSnapshot]:
        tid = str(tenant_id)
        return sorted(
            [s for s in self._by_id.values() if s.tenant_id == tid],
            key=lambda s: s.created_at or "",
            reverse=True,
        )


DEFAULT_MARKET_SIZING_STORE = MemMarketSizingStore()
