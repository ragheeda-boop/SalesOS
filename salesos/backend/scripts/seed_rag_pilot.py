#!/usr/bin/env python3
"""Pilot RAG corpus for pif tenant (Phase 4F — 5 small tenant-scoped docs).

Usage (Docker):
  docker compose exec backend python scripts/seed_rag_pilot.py
  docker compose exec backend python scripts/seed_rag_pilot.py --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import async_session

T_PIF = "a0000000-0000-4000-a000-000000000001"
NS = uuid.uuid5(uuid.NAMESPACE_URL, "phase4f-rag-pilot-seed")
DOC_IDS = [str(uuid.uuid5(NS, f"doc-{i}")) for i in range(1, 6)]

PILOT_DOCS = [
    ("PIF Investment Overview", "PIF manages diversified investments across giga-projects and strategic sectors."),
    ("Construction Sector Policy", "Regulatory updates for construction licensing and contract awards in KSA."),
    ("Healthcare Expansion", "MOH facility licensing signals and hospital market entry criteria."),
    ("Financial Services SAMA", "SAMA licensing requirements for new financial institution market entry."),
    ("Digital Transformation", "Enterprise B2B digital transformation procurement patterns in Riyadh."),
]


async def _pin(db, tenant: str) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": tenant})


async def seed() -> None:
    async with async_session() as db:
        await _pin(db, T_PIF)
        for doc_id, (title, content) in zip(DOC_IDS, PILOT_DOCS, strict=True):
            await db.execute(
                text(
                    "INSERT INTO rag_documents (id, tenant_id, source_type, source_id, "
                    "title, content) VALUES (CAST(:i AS uuid), CAST(:t AS uuid), "
                    "'pilot', :sid, :title, :content) ON CONFLICT (id) DO NOTHING"
                ),
                {"i": doc_id, "t": T_PIF, "sid": doc_id, "title": title, "content": content},
            )
        await db.commit()
    print(f"Seeded {len(PILOT_DOCS)} pilot RAG documents for tenant {T_PIF}")


async def cleanup() -> None:
    async with async_session() as db:
        await _pin(db, T_PIF)
        for doc_id in DOC_IDS:
            await db.execute(
                text("DELETE FROM rag_document_chunks WHERE document_id=CAST(:d AS uuid)"),
                {"d": doc_id},
            )
            await db.execute(
                text("DELETE FROM rag_documents WHERE id=CAST(:i AS uuid)"),
                {"i": doc_id},
            )
        await db.commit()
    print(f"Cleaned pilot RAG documents for tenant {T_PIF}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    asyncio.run(cleanup() if args.cleanup else seed())


if __name__ == "__main__":
    main()
