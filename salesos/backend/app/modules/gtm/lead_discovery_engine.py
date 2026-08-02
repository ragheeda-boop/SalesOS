"""STORY-11-03 — Lead Discovery engine (gov-first + provider fallback).

Government-dataset-shaped universe first; Integration Hub SourceConnector
fills remaining slots. Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from app.modules.gtm.lead_discovery import (
    SOURCE_GOVERNMENT,
    DiscoveredLead,
    LeadDiscoveryError,
    LeadDiscoveryQuery,
    provider_source_label,
)
from app.modules.gtm.market_sizing import CompanyRecord
from app.modules.gtm.market_sizing_engine import MemCompanyUniverse
from app.modules.integration_hub.source_connector import SourceConnector


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _company_name(row: CompanyRecord) -> str:
    return f"Company {row.id}"


def _row_matches(
    row: CompanyRecord,
    query: LeadDiscoveryQuery,
) -> bool:
    if query.industries and _norm(row.industry) not in query.industries:
        return False
    if query.cities and _norm(row.city) not in query.cities:
        return False
    if query.employees_min is not None or query.employees_max is not None:
        emp = row.employees_count
        if emp is None:
            return False
        if query.employees_min is not None and emp < query.employees_min:
            return False
        if query.employees_max is not None and emp > query.employees_max:
            return False
    return True


def search_government(
    universe: MemCompanyUniverse,
    query: LeadDiscoveryQuery,
    *,
    tenant_id: str | None = None,
) -> list[DiscoveredLead]:
    """Return government-source hits (ordered by record id) up to query.limit."""
    if not isinstance(query, LeadDiscoveryQuery):
        raise LeadDiscoveryError("query required")
    hits: list[DiscoveredLead] = []
    for row in universe.records:
        if tenant_id and row.tenant_id and row.tenant_id != tenant_id:
            continue
        if not _row_matches(row, query):
            continue
        hits.append(
            DiscoveredLead(
                id=f"gov:{row.id}",
                company_name=_company_name(row),
                industry=_norm(row.industry),
                city=_norm(row.city),
                employees_count=row.employees_count,
                source=SOURCE_GOVERNMENT,
                external_id=str(row.id),
            )
        )
        if len(hits) >= query.limit:
            break
    return hits


def _payload_matches(payload: dict[str, Any], query: LeadDiscoveryQuery) -> bool:
    industry = _norm(str(payload.get("industry") or ""))
    city = _norm(str(payload.get("city") or ""))
    if query.industries and industry not in query.industries:
        return False
    if query.cities and city not in query.cities:
        return False
    emp_raw = payload.get("employees_count")
    emp: int | None
    try:
        emp = int(emp_raw) if emp_raw is not None else None
    except (TypeError, ValueError):
        emp = None
    if query.employees_min is not None or query.employees_max is not None:
        if emp is None:
            return False
        if query.employees_min is not None and emp < query.employees_min:
            return False
        if query.employees_max is not None and emp > query.employees_max:
            return False
    return True


async def search_provider(
    adapter: SourceConnector,
    query: LeadDiscoveryQuery,
    *,
    limit: int,
    credential_ref: str = "vault://fake/lead-discovery",
    model: str = "company",
) -> list[DiscoveredLead]:
    """Pull external leads via Integration Hub SourceConnector (provider fallback)."""
    if limit < 1:
        return []
    if not isinstance(query, LeadDiscoveryQuery):
        raise LeadDiscoveryError("query required")
    key = str(getattr(adapter, "connector_key", "unknown") or "unknown")
    result = await adapter.pull_incremental(
        credential_ref=credential_ref,
        config={
            "industries": list(query.industries),
            "cities": list(query.cities),
        },
        model=model,
        cursor=None,
        limit=max(limit * 3, limit),
    )
    hits: list[DiscoveredLead] = []
    for rec in result.records:
        payload = dict(rec.payload or {})
        if not _payload_matches(payload, query):
            continue
        name = str(payload.get("name") or payload.get("company_name") or rec.external_id)
        emp_raw = payload.get("employees_count")
        try:
            emp = int(emp_raw) if emp_raw is not None else None
        except (TypeError, ValueError):
            emp = None
        hits.append(
            DiscoveredLead(
                id=f"prov:{key}:{rec.external_id}",
                company_name=name.strip() or rec.external_id,
                industry=_norm(str(payload.get("industry") or "")),
                city=_norm(str(payload.get("city") or "")),
                employees_count=emp,
                source=provider_source_label(key),
                external_id=str(rec.external_id),
            )
        )
        if len(hits) >= limit:
            break
    return hits


def _dedupe_key(lead: DiscoveredLead) -> str:
    return _norm(lead.company_name) or _norm(lead.external_id) or lead.id


async def discover_leads(
    *,
    query: LeadDiscoveryQuery,
    universe: MemCompanyUniverse,
    provider: SourceConnector | None = None,
    tenant_id: str | None = None,
    credential_ref: str = "vault://fake/lead-discovery",
) -> tuple[list[DiscoveredLead], int, int, str]:
    """Gov-first discovery; provider fills remaining slots. Returns leads + counts + key."""
    gov = search_government(universe, query, tenant_id=tenant_id)
    seen = {_dedupe_key(lead) for lead in gov}
    provider_hits: list[DiscoveredLead] = []
    provider_key = ""
    remaining = max(0, query.limit - len(gov))
    if remaining > 0 and provider is not None:
        provider_key = str(getattr(provider, "connector_key", "") or "")
        raw = await search_provider(
            provider,
            query,
            limit=remaining,
            credential_ref=credential_ref,
        )
        for lead in raw:
            key = _dedupe_key(lead)
            if key in seen:
                continue
            seen.add(key)
            provider_hits.append(lead)
            if len(provider_hits) >= remaining:
                break
    merged = list(gov) + list(provider_hits)
    return merged, len(gov), len(provider_hits), provider_key
