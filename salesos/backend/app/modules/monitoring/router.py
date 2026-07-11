import time
import statistics
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.dependencies import verify_token

router = APIRouter(dependencies=[Depends(verify_token)])


# ─── Schemas ───────────────────────────────────────────────────


class MonitoringEventSchema(BaseModel):
    type: str
    timestamp: str
    method: str | None = None
    path: str | None = None
    duration_ms: int | None = None
    status: int | None = None
    error_message: str | None = None
    error_stack: str | None = None
    context: str | None = None
    component_name: str | None = None
    name: str | None = None
    value: float | None = None
    tags: dict[str, str] | None = None
    route: str | None = None
    fcp: float | None = None
    lcp: float | None = None
    fid: float | None = None
    cls: float | None = None
    memory_used_mb: float | None = None
    dom_interactive: float | None = None
    dom_complete: float | None = None


class EventBatch(BaseModel):
    events: list[MonitoringEventSchema]


# ─── In-memory store ──────────────────────────────────────────


class _MonitoringStore:
    def __init__(self):
        self.api_calls: list[dict] = []
        self.errors: list[dict] = []
        self.page_loads: list[dict] = []
        self.web_vitals: dict[str, list[float]] = defaultdict(list)
        self.custom_metrics: dict[str, list[float]] = defaultdict(list)
        self.max_samples = 10_000

    def ingest(self, event: MonitoringEventSchema):
        if event.type == "api_call":
            self.api_calls.append({
                "method": event.method,
                "path": event.path,
                "duration_ms": event.duration_ms,
                "status": event.status,
                "timestamp": event.timestamp,
            })
            if len(self.api_calls) > self.max_samples:
                self.api_calls.pop(0)

        elif event.type == "error":
            self.errors.append({
                "message": event.error_message,
                "stack": event.error_stack,
                "context": event.context,
                "time": event.timestamp,
            })
            if len(self.errors) > self.max_samples:
                self.errors.pop(0)

        elif event.type == "page_load":
            self.page_loads.append({
                "route": event.route,
                "duration_ms": event.duration_ms,
                "dom_interactive": event.dom_interactive,
                "dom_complete": event.dom_complete,
                "fcp": event.fcp,
                "memory_used_mb": event.memory_used_mb,
                "timestamp": event.timestamp,
            })
            if len(self.page_loads) > self.max_samples:
                self.page_loads.pop(0)

        elif event.type == "web_vital":
            if event.name:
                self.web_vitals[event.name].append(event.value or 0)
                if len(self.web_vitals[event.name]) > self.max_samples:
                    self.web_vitals[event.name].pop(0)

        elif event.type == "metric":
            if event.name:
                self.custom_metrics[event.name].append(event.value or 0)
                if len(self.custom_metrics[event.name]) > self.max_samples:
                    self.custom_metrics[event.name].pop(0)

    def aggregate(self) -> dict:
        api_durations = sorted(
            (c["duration_ms"] for c in self.api_calls if c.get("duration_ms")),
        )
        page_durations = sorted(
            (p["duration_ms"] for p in self.page_loads if p.get("duration_ms")),
        )
        dom_interactive_times = sorted(
            (p["dom_interactive"] for p in self.page_loads if p.get("dom_interactive")),
        )

        recent_errors = [
            {"message": e["message"] or "", "time": e["time"]}
            for e in self.errors[-20:]
        ][::-1]

        error_by_context: dict[str, int] = defaultdict(int)
        for e in self.errors:
            ctx = e["context"] or "unknown"
            error_by_context[ctx] += 1

        latest_load = self.page_loads[-1] if self.page_loads else None

        return {
            "api_calls": {
                "total": len(self.api_calls),
                "p50_ms": self._percentile(api_durations, 50),
                "p95_ms": self._percentile(api_durations, 95),
                "p99_ms": self._percentile(api_durations, 99),
            },
            "errors": {
                "total": len(self.errors),
                "by_context": dict(error_by_context),
                "recent": recent_errors,
            },
            "page_loads": {
                "total": len(self.page_loads),
                "avg_load_ms": round(statistics.mean(page_durations), 1) if page_durations else 0,
                "avg_dom_interactive_ms": round(statistics.mean(dom_interactive_times), 1) if dom_interactive_times else 0,
            },
            "web_vitals": {
                "lcp": round(statistics.mean(self.web_vitals.get("lcp", [])), 1) if self.web_vitals.get("lcp") else None,
                "fid": round(statistics.mean(self.web_vitals.get("fid", [])), 1) if self.web_vitals.get("fid") else None,
                "cls": round(statistics.mean(self.web_vitals.get("cls", [])), 4) if self.web_vitals.get("cls") else None,
            },
            "memory": {
                "current_mb": latest_load.get("memory_used_mb") if latest_load else None,
            },
            "system_health": {
                "database": "unknown",
                "cache": "unknown",
                "graph": "unknown",
                "kafka": "unknown",
                "uptime_seconds": time.time() - self._start_time,
            },
        }

    def health(self) -> dict:
        return {
            "status": "ok",
            "events_ingested": len(self.api_calls) + len(self.errors) + len(self.page_loads) + sum(len(v) for v in self.web_vitals.values()) + sum(len(v) for v in self.custom_metrics.values()),
            "uptime_seconds": time.time() - self._start_time,
            "api_calls_total": len(self.api_calls),
            "errors_total": len(self.errors),
            "page_loads_total": len(self.page_loads),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _percentile(sorted_data: list[float], p: int) -> int:
        if not sorted_data:
            return 0
        k = (len(sorted_data) - 1) * p / 100
        f = int(k)
        c = f + 1
        if c >= len(sorted_data):
            return round(sorted_data[-1])
        return round(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]))

    _start_time: float = time.time()


store = _MonitoringStore()


# ─── Routes ────────────────────────────────────────────────────


@router.post("/api/v1/monitoring/events")
async def ingest_events(batch: EventBatch):
    for event in batch.events:
        store.ingest(event)
    return {"status": "ok", "ingested": len(batch.events)}


@router.get("/api/v1/monitoring/metrics")
async def get_metrics(request: Request):
    result = store.aggregate()
    result["system_health"] = await _resolve_system_health(request)
    return result


@router.get("/api/v1/monitoring/health")
async def get_health(request: Request):
    health = store.health()
    health["checks"] = await _resolve_system_health(request)
    return health


async def _resolve_system_health(request: Request) -> dict[str, str]:
    checks: dict[str, str] = {}
    app_state = request.app.state

    checks["database"] = "connected" if getattr(app_state, "db_available", True) else "disconnected"
    checks["cache"] = "connected" if hasattr(app_state, "event_runtime") else "unavailable"
    checks["graph"] = "connected" if getattr(app_state, "kg_engine", None) is not None else "not_configured"
    checks["kafka"] = "active" if getattr(app_state, "event_runtime", None) else "not_configured"
    checks["rate_limiter"] = "active"
    checks["uptime_seconds"] = f"{time.time() - getattr(app_state, '_start_time', time.time()):.0f}"

    return checks
