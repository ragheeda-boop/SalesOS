"""Prometheus metrics endpoint and HTTP metrics middleware for SalesOS.

Endpoints:
  GET /metrics         — full Prometheus scrape target (common.metrics + new collector)
  GET /metrics/pool    — database connection pool stats
  GET /metrics/app     — application-level metrics (WS, cache, NBA, DB pool)
  GET /api/v1/admin/sla-report — SLA compliance report per category
"""

import time

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.common.metrics import metrics
from app.dependencies import require_role_dep, verify_token
from app.metrics.collector import collector
from app.metrics.sla_monitor import sla_monitor
from intelligence.providers.observability import ai_observability

# Scrape path /metrics has no user-JWT dependency (PROD-W5-004).
# Protect via network policy / internal scrape; admin/app metrics stay auth'd.
router = APIRouter()
_auth_deps = [Depends(verify_token)]


class MetricsMiddleware:
    """Track HTTP request count and duration for every request.

    Uses ASGI __call__ pattern (not BaseHTTPMiddleware) to avoid
    body streaming deadlocks with nested middleware + exception handlers.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start = time.time()
        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start
            path = scope.get("path", "")
            method = scope.get("method", "GET")
            metrics.track_http_request(method, path, status_code, duration)
            collector.track_http_request(method, path, status_code, duration)
            category = _categorize_path(path)
            if category:
                sla_monitor.record_request(category, duration * 1000, status_code)


def _categorize_path(path: str) -> str | None:
    """Map a URL path to an SLA category name."""
    if path.startswith("/health") or path == "/ping" or path.startswith("/metrics"):
        return "health"
    if path.startswith("/api/v1/identity") or path.startswith("/api/v1/sso"):
        return "auth"
    if (
        path.startswith("/api/v1/enrich")
        or path.startswith("/api/v1/ai")
        or path.startswith("/api/v1/data-fabric")
    ):
        return "enrichment"
    if path.startswith("/api/v1/search"):
        return "critical_path"
    if "decision-runtime" in path or path.startswith("/api/v1/decision"):
        return "standard"
    if path.startswith("/api/v1/companies"):
        if path.endswith("/search"):
            return "critical_path"
        return "standard"
    if "/dashboard" in path:
        return "critical_path"
    if any(seg in path for seg in ["/contacts", "/opportunities", "/meetings", "/revenue"]):
        return "standard"
    return None


@router.get("/metrics")
async def prometheus_metrics():
    """Expose combined Prometheus-formatted metrics for scraping.

    No user JWT — scrape via internal network / Prometheus service mesh.
    """
    common = metrics.generate()
    app = collector.generate()
    ai = ai_observability.generate()
    return PlainTextResponse(common + "\n" + app + "\n" + ai)


@router.get("/metrics/pool", dependencies=_auth_deps)
async def db_pool_metrics():
    """Expose database connection pool metrics."""
    from app.database import get_pool_metrics

    pool = get_pool_metrics()
    collector.track_db_pool(
        pool.get("checked_out", 0),
        pool.get("checked_in", 0),
        pool.get("overflow", 0),
        pool.get("total_open", 0),
    )
    return pool


@router.get("/metrics/app", dependencies=_auth_deps)
async def app_metrics():
    """Application-level metrics: WS connections, cache stats, NBA timing."""
    from app.routers.notifications import _ws_manager

    ws_metrics = await _ws_manager.get_metrics()
    return {
        "websocket": ws_metrics,
        "cache": {
            "hits": collector._cache_hits,
            "misses": collector._cache_misses,
            "hit_ratio": collector._cache_hits
            / max(1, collector._cache_hits + collector._cache_misses),
        },
        "errors": {
            "http_5xx": collector._error_count.get("http_5xx", 0),
            "http_4xx": collector._error_count.get("http_4xx", 0),
        },
    }


@router.get("/api/v1/admin/sla-report")
async def sla_report(
    _=Depends(require_role_dep("admin")),
):
    """SLA compliance report per endpoint category (24h window)."""
    return sla_monitor.get_report()
