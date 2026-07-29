"""Upsert CRM contacts from synced email/calendar addresses (company-linked only).

Contacts are created only when company_linker resolves a tenant company for the
address domain — never invents companies or orphan contacts.
"""

from __future__ import annotations

import logging
import re
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication_hub.company_linker import (
    _FREE_EMAIL_DOMAINS,
    resolve_company_ids_for_addresses,
)

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_ADDRESSES = 50


def _normalize_email(raw: str) -> str | None:
    if not raw:
        return None
    # Strip display-name wrappers: "Alice <alice@acme.com>"
    if "<" in raw and ">" in raw:
        raw = raw[raw.rfind("<") + 1 : raw.rfind(">")].strip()
    email = raw.strip().lower()
    if not _EMAIL_RE.match(email):
        return None
    domain = email.rsplit("@", 1)[-1]
    if domain in _FREE_EMAIL_DOMAINS:
        return None
    return email


def _display_name_from_email(email: str) -> str:
    local = email.split("@", 1)[0]
    cleaned = re.sub(r"[._+\-]+", " ", local).strip()
    return cleaned.title() if cleaned else email


async def upsert_contacts_from_addresses(
    db: AsyncSession,
    tenant_id: UUID,
    addresses: list[str],
    *,
    source: str = "google_sync",
) -> dict:
    """Link external addresses to CRM contacts under matched companies.

    Dedupes on (tenant_id, lower(email)). Skips free-mail and unmatched domains.
    """
    normalized: list[str] = []
    seen: set[str] = set()
    for addr in addresses:
        email = _normalize_email(addr)
        if not email or email in seen:
            continue
        seen.add(email)
        normalized.append(email)
        if len(normalized) >= _MAX_ADDRESSES:
            break

    if not normalized:
        return {"created": 0, "updated": 0, "skipped": 0}

    created = 0
    updated = 0
    skipped = 0

    for email in normalized:
        company_ids = await resolve_company_ids_for_addresses(db, tenant_id, [email])
        if not company_ids:
            skipped += 1
            continue
        company_id = company_ids[0]
        name = _display_name_from_email(email)

        existing = await db.execute(
            sa_text(
                """
                SELECT id::text AS id FROM contacts
                WHERE tenant_id = :tid AND lower(coalesce(email, '')) = :email
                LIMIT 1
                """
            ),
            {"tid": str(tenant_id), "email": email},
        )
        row = existing.mappings().first()
        if row:
            await db.execute(
                sa_text(
                    """
                    UPDATE contacts
                    SET company_id = COALESCE(company_id, CAST(:cid AS uuid)),
                        source = COALESCE(source, :source),
                        updated_at = NOW()
                    WHERE id = CAST(:id AS uuid) AND tenant_id = :tid
                    """
                ),
                {
                    "cid": company_id,
                    "source": source,
                    "id": row["id"],
                    "tid": str(tenant_id),
                },
            )
            updated += 1
        else:
            await db.execute(
                sa_text(
                    """
                    INSERT INTO contacts (
                        id, tenant_id, company_id, name, email, source,
                        is_primary, confidence_score, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), :tid, CAST(:cid AS uuid), :name, :email, :source,
                        false, 0.5, NOW(), NOW()
                    )
                    """
                ),
                {
                    "tid": str(tenant_id),
                    "cid": company_id,
                    "name": name,
                    "email": email,
                    "source": source,
                },
            )
            created += 1

    logger.info(
        "contact_sync.upsert",
        extra={
            "tenant_id": str(tenant_id),
            "created": created,
            "updated": updated,
            "skipped": skipped,
        },
    )
    return {"created": created, "updated": updated, "skipped": skipped}
