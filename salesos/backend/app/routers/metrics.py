"""Prometheus metrics endpoint and HTTP metrics middleware for SalesOS.

Endpoints:
  GET /metrics         — full Prometheus scrape target (common.metrics + new collector)
  GET /metrics/pool    — database connection pool stats
  GET /metrics/app     — application-level metrics (WS, cache, NBA, DB pool)
  GET /api/v1/admin/sla-report — SLA compliance report per category
"""

import time
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.metrics import metrics
from app.metrics.collector import collector
from app.metrics.sla_monitor import sla_monitor

router = APIRouter()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track HTTP request count and duration for every request."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        path = request.url.path
        method = request.method
        status = response.status_code
        metrics.track_http_request(method, path, status, duration)
        collector.track_http_request(method, path, status, duration)

        # Feed SLA monitor — categorise by path prefix
        category = _categorize_path(path)
        if category:
            sla_monitor.record_request(category, duration * 1000, status)

        return response


def _categorize_path(path: str) -> str | None:
    """Map a URL path to an SLA category name."""
    if path.startswith("/health") or path == "/ping" or path.startswith("/metrics"):
        return "health"
    if path.startswith("/api/v1/identity") or path.startswith("/api/v1/sso"):
        return "auth"
    if path.startswith("/api/v1/enrich") or path.startswith("/api/v1/ai") or path.startswith("/api/v1/data-fabric"):
        return "enrichment"
    if path.startswith("/api/v1/search"):
        return "critical_path"
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
    """Expose combined Prometheus-formatted metrics for scraping."""
    common = metrics.generate()
    app = collector.generate()
    return PlainTextResponse(common + "\n" + app)


@router.get("/metrics/pool")
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


@router.get("/metrics/app")
async def app_metrics():
    """Application-level metrics: WS connections, cache stats, NBA timing."""
    from app.routers.notifications import _ws_manager
    ws_metrics = await _ws_manager.get_metrics()
    return {
        "websocket": ws_metrics,
        "cache": {
            "hits": collector._cache_hits,
            "misses": collector._cache_misses,
            "hit_ratio": collector._cache_hits / max(1, collector._cache_hits + collector._cache_misses),
        },
        "errors": {
            "http_5xx": collector._error_count.get("http_5xx", 0),
            "http_4xx": collector._error_count.get("http_4xx", 0),
        },
    }


@router.get("/api/v1/admin/sla-report")
async def sla_report():
    """SLA compliance report per endpoint category (24h window)."""
    return sla_monitor.get_report()
