"""Resolve CRM company IDs from email addresses / domains (tenant-scoped)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

_FREE_EMAIL_DOMAINS = frozenset({
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "me.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
})


def extract_domains(addresses: list[str]) -> set[str]:
    domains: set[str] = set()
    for addr in addresses:
        if not addr or "@" not in addr:
            continue
        domain = addr.rsplit("@", 1)[-1].strip().lower()
        if domain and domain not in _FREE_EMAIL_DOMAINS:
            domains.add(domain)
    return domains


async def resolve_company_ids_for_addresses(
    db: AsyncSession,
    tenant_id: UUID,
    addresses: list[str],
) -> list[str]:
    """Match company website/email fields containing external domains."""
    domains = extract_domains(addresses)
    if not domains:
        return []

    # Build OR clauses for domain substring match on website + email.
    clauses = []
    params: dict = {"tid": str(tenant_id)}
    for i, domain in enumerate(sorted(domains)):
        key = f"d{i}"
        params[key] = f"%{domain}%"
        clauses.append(
            f"(lower(coalesce(website, '')) LIKE :{key} OR lower(coalesce(email, '')) LIKE :{key})"
        )

    sql = f"""
        SELECT id::text AS id
        FROM companies
        WHERE tenant_id = :tid
          AND ({' OR '.join(clauses)})
        LIMIT 20
    """
    result = await db.execute(sa_text(sql), params)
    return [row["id"] for row in result.mappings().all()]
