"""Resolve CRM company IDs from email addresses / domains (tenant-scoped)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

_FREE_EMAIL_DOMAINS = frozenset(
    {
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
    }
)

# Cap domains to bound query size / param count.
_MAX_DOMAINS = 20


def extract_domains(addresses: list[str]) -> set[str]:
    domains: set[str] = set()
    for addr in addresses:
        if not addr or "@" not in addr:
            continue
        domain = addr.rsplit("@", 1)[-1].strip().lower()
        # Reject values that are not plausible hostnames (defense-in-depth).
        if not domain or not all(c.isalnum() or c in ".-" for c in domain):
            continue
        if domain.startswith(".") or domain.endswith(".") or ".." in domain:
            continue
        if domain and domain not in _FREE_EMAIL_DOMAINS:
            domains.add(domain)
    return domains


async def resolve_company_ids_for_addresses(
    db: AsyncSession,
    tenant_id: UUID,
    addresses: list[str],
) -> list[str]:
    """Match company website/email fields containing external domains.

    Domain values are bound as parameters — never interpolated into SQL text.
    """
    domains = sorted(extract_domains(addresses))[:_MAX_DOMAINS]
    if not domains:
        return []

    # Bound OR clauses with named parameters (d0, d1, ...) — keys are integers only.
    clauses: list[str] = []
    params: dict = {"tid": str(tenant_id)}
    for i, domain in enumerate(domains):
        key = f"d{i}"
        params[key] = f"%{domain}%"
        clauses.append(
            f"(lower(coalesce(website, '')) LIKE :{key} "
            f"OR lower(coalesce(email, '')) LIKE :{key})"
        )

    # Clause keys are generated from enumerate indices only (not user input).
    sql = sa_text(
        "SELECT id::text AS id FROM companies "
        "WHERE tenant_id = :tid AND (" + " OR ".join(clauses) + ") "
        "LIMIT 20"
    )
    result = await db.execute(sql, params)
    return [row["id"] for row in result.mappings().all()]
