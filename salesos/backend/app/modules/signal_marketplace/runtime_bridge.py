"""Runtime bridge: domain events → subscribed signal detections (Phase 4E).

Closes the loop the Data Readiness Gate flagged: a catalog existed but no
tenant ever saw a `signal_events` row because nothing connected the event
bus to detection. Semantics:

- Matching reuses SignalDetectionEngine.match_signals (single source).
- Gating: an event becomes a signal_event ONLY for companies with an ACTIVE
  subscription to that signal (marketplace contract: subscribe → receive).
- Sessions are per-call from the canonical app pool; writes flow through
  Postgres repos behind canonical RLS.
"""

import logging
import uuid

from app.database import async_session
from app.modules.signal_marketplace.engine import SignalDetectionEngine
from app.modules.signal_marketplace.models import SignalEvent
from app.modules.signal_marketplace.postgres_repo import (
    PostgresSignalEventRepository,
    PostgresSignalRepository,
    PostgresSignalSubscriptionRepository,
)

logger = logging.getLogger("salesos.signals.bridge")


class SignalDetectionBridge:
    """Stateless-per-call detector with a lazily hydrated catalog map."""

    def __init__(self) -> None:
        self._catalog_map: dict[str, object] | None = None

    async def _ensure_catalog(self) -> dict:
        if self._catalog_map is None:
            async with async_session() as db:
                signals = await PostgresSignalRepository(db).get_all()
            self._catalog_map = {s.id: s for s in signals}
            logger.info(
                "signal bridge hydrated catalog: %d signals", len(self._catalog_map)
            )
        return self._catalog_map

    def refresh(self) -> None:
        """Drop the cached catalog map (e.g., after admin catalog changes)."""
        self._catalog_map = None

    async def on_domain_event(self, event: dict) -> int:
        """Accepts a legacy-format domain event dict; returns events created."""
        event_type = str(event.get("event_type") or "")
        aggregate_id = str(event.get("aggregate_id") or "")
        tenant_id = str(event.get("tenant_id") or "")
        data = event.get("data")
        if not event_type or not aggregate_id or not tenant_id:
            return 0

        engine = SignalDetectionEngine(service=None)  # type: ignore[arg-type]
        engine._signal_map = await self._ensure_catalog()  # noqa: SLF001
        matched = engine.match_signals(event_type)
        if not matched:
            return 0

        created = 0
        async with async_session() as db:
            # DEC-085: pin the tenant GUC or canonical RLS hides/mutes rows
            from sqlalchemy import text as _text

            await db.execute(
                _text("SELECT set_config('app.tenant_id', :t, true)"),
                {"t": tenant_id},
            )
            sub_repo = PostgresSignalSubscriptionRepository(db)
            event_repo = PostgresSignalEventRepository(db)
            for signal_id in matched:
                subs = await sub_repo.list_by_signal_and_company(
                    signal_id, aggregate_id, tenant_id
                )
                if not any(s.active for s in subs):
                    continue  # marketplace contract: only subscribers receive
                await event_repo.create(
                    SignalEvent(
                        id=str(uuid.uuid4()),
                        signal_id=signal_id,
                        company_id=aggregate_id,
                        tenant_id=tenant_id,
                        data=data if isinstance(data, dict) else {},
                    )
                )
                catalog = self._catalog_map or {}
                sig_def = catalog.get(signal_id)
                if sig_def is not None:
                    from app.modules.company.signal_persistence import upsert_signals

                    await upsert_signals(
                        db,
                        tenant_id=tenant_id,
                        company_id=aggregate_id,
                        signals=[
                            {
                                "type": signal_id,
                                "severity": getattr(sig_def, "severity", "info"),
                                "title": getattr(sig_def, "name", signal_id),
                                "description": getattr(sig_def, "description", ""),
                                "source": "signal_marketplace",
                                "confidence_score": getattr(sig_def, "weight", None),
                            }
                        ],
                    )
                created += 1
            await db.commit()
        if created:
            logger.info(
                "signal bridge: %d event(s) for company=%s on %s",
                created,
                aggregate_id,
                event_type,
            )
        return created


def get_signal_detection_bridge() -> SignalDetectionBridge:
    """Process-wide singleton (boot registers this on the event runtime)."""
    global _bridge
    try:
        return _bridge  # type: ignore[name-defined]
    except NameError:
        _bridge = SignalDetectionBridge()
        return _bridge
