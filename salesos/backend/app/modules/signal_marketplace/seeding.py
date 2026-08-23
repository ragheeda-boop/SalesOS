"""Signal catalog seeding from platform Knowledge Packs (Phase 4D).

The Data Readiness Gate (2026-08-23) found `signal_catalog` empty although
shipped packs carry real signal definitions and `load_all_packs()` was never
invoked anywhere (dead path). This module makes seeding an explicit, idempotent
startup step. The catalog is GLOBAL_PLATFORM content (ADR: no tenant_id) —
seeding it is deployment setup, not tenant data population.
"""

import logging

from app.database import async_session
from app.modules.signal_marketplace.engine import SignalDetectionEngine
from app.modules.signal_marketplace.postgres_repo import PostgresSignalRepository
from app.modules.signal_marketplace.service import SignalMarketplaceService

logger = logging.getLogger("salesos.signals.seeding")


async def seed_signal_catalog_from_packs() -> dict:
    """Load every shipped pack's signal definitions into signal_catalog.

    Idempotent by construction: register_signal upserts only when the id is
    absent, so repeated boots never duplicate rows. Never raises into boot —
    a broken pack degrades to a warning; the marketplace simply stays empty.
    """
    try:
        async with async_session() as db:
            service = SignalMarketplaceService(
                signal_repo=PostgresSignalRepository(db),
            )
            engine = SignalDetectionEngine(service)
            signals = await engine.load_all_packs()
            await db.commit()
    except Exception as exc:  # noqa: BLE001 — boot must not die on pack content
        logger.warning("signal catalog seeding failed (non-fatal): %s", exc)
        return {"seeded": 0, "ok": False, "error": str(exc)}
    logger.info("signal catalog seeded: %d signals from knowledge packs", len(signals))
    return {"seeded": len(signals), "ok": True}
