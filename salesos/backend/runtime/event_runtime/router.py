"""Event Runtime REST endpoints for monitoring and management."""

from fastapi import APIRouter, Depends, Request

from runtime.event_runtime import EventRuntime

router = APIRouter()


@router.get("/event-runtime/stats")
async def event_runtime_stats(request: Request):
    runtime: EventRuntime | None = getattr(request.app.state, "event_runtime", None)
    if not runtime:
        return {"status": "not_initialized"}
    metrics = runtime.metrics.snapshot()
    dlq_count = runtime.dead_letter_queue.count()
    return {
        "status": "running",
        "metrics": metrics,
        "dead_letter_count": dlq_count,
    }


@router.get("/event-runtime/dead-letters")
async def list_dead_letters(request: Request):
    runtime: EventRuntime | None = getattr(request.app.state, "event_runtime", None)
    if not runtime:
        return {"items": [], "total": 0}
    entries = runtime.dead_letter_queue.get_all()
    return {
        "items": [e.to_dict() for e in entries],
        "total": len(entries),
    }


@router.post("/event-runtime/dead-letters/{entry_id}/replay")
async def replay_dead_letter(entry_id: str, request: Request):
    runtime: EventRuntime | None = getattr(request.app.state, "event_runtime", None)
    if not runtime:
        return {"message": "Runtime not initialized"}
    success = await runtime.replay_dead_letter(entry_id)
    return {"message": f"Replayed {entry_id}", "success": success}


@router.post("/event-runtime/dead-letters/replay-all")
async def replay_all_dead_letters(request: Request):
    runtime: EventRuntime | None = getattr(request.app.state, "event_runtime", None)
    if not runtime:
        return {"message": "Runtime not initialized"}
    count = await runtime.replay_all_dead_letters()
    return {"message": f"Replayed {count} events", "count": count}


@router.get("/event-runtime/metrics")
async def event_runtime_metrics(request: Request):
    runtime: EventRuntime | None = getattr(request.app.state, "event_runtime", None)
    if not runtime:
        return {}
    return runtime.metrics.snapshot()
