"""NBA Engine event subscribers — listen to domain events and trigger recomputation."""
from runtime.nba_engine import NBAEngine


def register_subscribers(event_runtime, session_factory, feature_store=None, logger=None):
    """Register NBA Engine as Event Runtime subscriber."""

    async def on_opportunity_event(event):
        if event.event_type in ("opportunity.created", "opportunity.stage_changed"):
            engine = NBAEngine(
                session_factory=session_factory,
                feature_store=feature_store,
                event_runtime=event_runtime,
                logger=logger,
            )
            await engine.recompute(
                opportunity_id=event.aggregate_id,
                tenant_id=event.tenant_id or "",
            )

    event_runtime.subscribe("opportunity.*", on_opportunity_event, priority="EARLY")
