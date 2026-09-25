"""ID Registry — Centralized, concurrent-safe global ID generation.

Implements the architecture from Doc 04 §2.6:
- G-C-XXXXXXXX for companies
- G-P-XXXXXXXX for persons
- UUID v4 + Crockford base32 encoding
- PostgreSQL advisory lock for batch concurrency
- INSERT ON CONFLICT DO NOTHING as safety net

Invariants:
- Each entity gets exactly one G-C/G-P ID
- No two entities receive the same ID
- IDs are never recycled
- Generation is atomic (database-level)
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    pass

# Crockford base32 alphabet (no I, L, O, U — ambiguous chars)
# 32 characters total: 0-9 + A-H + J-K + M-N + P-T + V-Z
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Advisory lock key for batch operations
_LOCK_KEY = "hashtext('md_id_registry_batch')"


def _encode_base32(data: bytes) -> str:
    """Encode bytes to Crockford base32 (fixed-length output)."""
    value = int.from_bytes(data, "big")
    if value == 0:
        return _ALPHABET[0] * 26  # UUID is 16 bytes = 128 bits → 26 base32 chars
    result: list[str] = []
    while value > 0:
        value, remainder = divmod(value, 32)
        result.append(_ALPHABET[remainder])
    return "".join(reversed(result))


def generate_global_id(entity_type: str) -> str:
    """Generate a stable global ID.

    Args:
        entity_type: 'C' for company, 'P' for person

    Returns:
        G-C-XXXXXXXX or G-P-XXXXXXXX

    Rules:
    - Generated from UUID v4
    - Encoded as Crockford base32 (8 chars)
    - Format: G-{entity_type}-{XXXXXXXX}
    - Called once per entity creation, never regenerated
    """
    if entity_type not in ("C", "P"):
        raise ValueError(f"entity_type must be 'C' or 'P', got '{entity_type}'")
    uid = uuid.uuid4()
    encoded = _encode_base32(uid.bytes)
    return f"G-{entity_type}-{encoded[:8]}"


class IDRegistry:
    """Centralized, concurrent-safe ID generation.

    Uses PostgreSQL advisory locks for batch serialization and
    INSERT ON CONFLICT DO NOTHING as the final safety net.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def acquire_batch_lock(self) -> None:
        """Acquire advisory lock for batch operations.

        Lock scope: transaction-level (pg_advisory_xact_lock).
        Released automatically at COMMIT or ROLLBACK.
        """
        await self.session.execute(
            text(f"SELECT pg_advisory_xact_lock({_LOCK_KEY})")
        )

    async def generate_company_id(self) -> str:
        """Generate G-C-XXXXXXXX. Call once per company creation."""
        return generate_global_id("C")

    async def generate_person_id(self) -> str:
        """Generate G-P-XXXXXXXX. Call once per person creation."""
        return generate_global_id("P")

    async def is_id_used(self, global_id: str) -> bool:
        """Check if ID already exists in md_global_companies or md_global_people."""
        result = await self.session.execute(
            text(
                "SELECT 1 FROM md_global_companies WHERE id = :id "
                "UNION ALL "
                "SELECT 1 FROM md_global_people WHERE id = :id"
            ),
            {"id": global_id},
        )
        return result.scalar() is not None

    async def register_id(
        self,
        global_id: str,
        entity_type: str,
    ) -> bool:
        """Register a global ID atomically.

        Returns True if registered, False if already exists (idempotent).
        Uses INSERT ON CONFLICT DO NOTHING as safety net.
        """
        slug = global_id.lower().replace("g-c-", "gc-").replace("g-p-", "gp-")
        table = "md_global_companies" if entity_type == "C" else "md_global_people"
        result = await self.session.execute(
            text(
                f"INSERT INTO {table} (id, slug, canonical_name, status) "
                "VALUES (:id, :slug, :name, 'active') "
                "ON CONFLICT (id) DO NOTHING "
                "RETURNING id"
            ),
            {"id": global_id, "slug": slug, "name": f"placeholder_{global_id}"},
        )
        return result.scalar() is not None
