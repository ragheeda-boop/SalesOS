"""Prometheus metrics endpoint and HTTP metrics middleware for SalesOS."""

import time

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.metrics import metrics

router = APIRouter()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track HTTP request count and duration for every request."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        path = request.url.path
        method = request.method
        metrics.track_http_request(method, path, response.status_code, duration)
        return response


@router.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus-formatted metrics for scraping."""
    return PlainTextResponse(metrics.generate())
