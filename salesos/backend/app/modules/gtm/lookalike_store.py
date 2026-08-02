"""STORY-11-04 — In-memory lookalike models (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.lookalike import (
    LookalikeError,
    LookalikeModel,
    normalize_seed,
)
from app.modules.gtm.lookalike_engine import (
    MemOpportunityHistory,
    build_demo_opportunity_history,
    rank_lookalikes,
)


@dataclass
class MemLookalikeStore:
    """Tenant-scoped lookalike models for CAP-098."""

    _by_id: dict[str, LookalikeModel] = field(default_factory=dict)
    _history: MemOpportunityHistory = field(
        default_factory=lambda: build_demo_opportunity_history(tenant_id="")
    )

    def bind_history(self, history: MemOpportunityHistory) -> None:
        self._history = history

    def run(
        self,
        *,
        tenant_id: str,
        name: str,
        company_name: str,
        industry: str | None = None,
        city: str | None = None,
        employees_count: int | None = None,
        limit: int = 10,
        model_id: str | None = None,
    ) -> LookalikeModel:
        tid = (tenant_id or "").strip()
        if not tid:
            raise LookalikeError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise LookalikeError("name required")

        seed = normalize_seed(
            company_name=company_name,
            industry=industry,
            city=city,
            employees_count=employees_count,
        )
        hits, won_n, lost_n = rank_lookalikes(
            seed,
            self._history,
            tenant_id=tid,
            limit=limit,
        )
        rid = (model_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant lookalike write blocked")

        now = datetime.now(UTC).isoformat()
        row = LookalikeModel(
            id=rid,
            tenant_id=tid,
            name=nm,
            seed=seed,
            hits=hits,
            trained_on_won=won_n,
            trained_on_lost=lost_n,
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._by_id[row.id] = row
        return row

    def get(self, model_id: str, *, tenant_id: str) -> LookalikeModel | None:
        row = self._by_id.get(str(model_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[LookalikeModel]:
        tid = str(tenant_id)
        return sorted(
            [m for m in self._by_id.values() if m.tenant_id == tid],
            key=lambda m: m.updated_at or m.created_at or "",
            reverse=True,
        )


DEFAULT_LOOKALIKE_STORE = MemLookalikeStore()
