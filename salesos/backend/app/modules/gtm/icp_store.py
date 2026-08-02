"""STORY-11-01 — In-memory versioned ICPProfile store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.icp import (
    ICPError,
    ICPProfile,
    normalize_criteria,
    normalize_weights,
)
from app.modules.gtm.icp_engine import (
    ICPScoreResult,
    assert_weights_usable,
    score_company_against_profile,
)


@dataclass
class MemICPStore:
    """Tenant-scoped ICP profiles — reusable across sessions."""

    _by_id: dict[str, ICPProfile] = field(default_factory=dict)

    def create(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str = "",
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
        titles: list[str] | None = None,
        keywords: list[str] | None = None,
        weights: dict[str, float] | None = None,
        profile_id: str | None = None,
        is_active: bool = True,
    ) -> ICPProfile:
        tid = (tenant_id or "").strip()
        if not tid:
            raise ICPError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise ICPError("name required")

        criteria = normalize_criteria(
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
            titles=titles,
            keywords=keywords,
        )
        wraw = weights or {}
        w = normalize_weights(
            industry=wraw.get("industry"),
            city=wraw.get("city"),
            employees=wraw.get("employees"),
            titles=wraw.get("titles"),
            keywords=wraw.get("keywords"),
        )
        assert_weights_usable(w)

        rid = (profile_id or "").strip() or uuid.uuid4().hex[:12]
        if rid in self._by_id:
            raise ICPError("profile id already exists; use update")
        now = datetime.now(UTC).isoformat()
        row = ICPProfile(
            id=rid,
            tenant_id=tid,
            name=nm,
            description=(description or "").strip(),
            criteria=criteria,
            weights=w,
            schema_version=1,
            is_active=bool(is_active),
            created_at=now,
            updated_at=now,
        )
        self._by_id[row.id] = row
        return row

    def update(
        self,
        profile_id: str,
        *,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
        titles: list[str] | None = None,
        keywords: list[str] | None = None,
        weights: dict[str, float] | None = None,
        is_active: bool | None = None,
        bump_version: bool = True,
    ) -> ICPProfile:
        existing = self.get(profile_id, tenant_id=tenant_id)
        if existing is None:
            raise KeyError("icp profile not found")

        criteria = existing.criteria
        if any(
            x is not None
            for x in (
                industries,
                cities,
                employees_min,
                employees_max,
                titles,
                keywords,
            )
        ):
            criteria = normalize_criteria(
                industries=industries if industries is not None else criteria.industries,
                cities=cities if cities is not None else criteria.cities,
                employees_min=(
                    employees_min if employees_min is not None else criteria.employees_min
                ),
                employees_max=(
                    employees_max if employees_max is not None else criteria.employees_max
                ),
                titles=titles if titles is not None else criteria.titles,
                keywords=keywords if keywords is not None else criteria.keywords,
            )

        w = existing.weights
        if weights is not None:
            w = normalize_weights(
                industry=weights.get("industry", w.industry),
                city=weights.get("city", w.city),
                employees=weights.get("employees", w.employees),
                titles=weights.get("titles", w.titles),
                keywords=weights.get("keywords", w.keywords),
            )
            assert_weights_usable(w)

        nm = existing.name if name is None else (name or "").strip()
        if not nm:
            raise ICPError("name required")
        desc = existing.description if description is None else (description or "").strip()
        active = existing.is_active if is_active is None else bool(is_active)
        ver = existing.schema_version + 1 if bump_version else existing.schema_version
        now = datetime.now(UTC).isoformat()
        row = ICPProfile(
            id=existing.id,
            tenant_id=existing.tenant_id,
            name=nm,
            description=desc,
            criteria=criteria,
            weights=w,
            schema_version=ver,
            is_active=active,
            created_at=existing.created_at,
            updated_at=now,
        )
        self._by_id[row.id] = row
        return row

    def get(self, profile_id: str, *, tenant_id: str) -> ICPProfile | None:
        row = self._by_id.get(str(profile_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[ICPProfile]:
        tid = str(tenant_id)
        return sorted(
            [p for p in self._by_id.values() if p.tenant_id == tid],
            key=lambda p: p.updated_at or p.created_at or "",
            reverse=True,
        )

    def score(
        self,
        profile_id: str,
        *,
        tenant_id: str,
        company: dict,
    ) -> ICPScoreResult:
        row = self.get(profile_id, tenant_id=tenant_id)
        if row is None:
            raise KeyError("icp profile not found")
        return score_company_against_profile(row, company)


DEFAULT_ICP_STORE = MemICPStore()
