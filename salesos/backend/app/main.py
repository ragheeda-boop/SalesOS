import os
import time
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import QueuePool

from app.boot.exceptions import register_exception_handlers
from app.boot.middleware import setup_middleware
from app.boot.routers import register_routers
from app.boot.startup import init_startup_services, shutdown_services
from app.common.schemas import (
    HealthLiveResponse,
    HealthReadyResponse,
    HealthResponse,
    PingResponse,
    VersionResponse,
)
from app.config import settings
from app.database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = await init_startup_services(app)
    yield
    for t in tasks:
        t.cancel()
    await shutdown_services(app)


_start_time = time.time()


def _check_kafka_status(app_state) -> str:
    """Single source of truth for Kafka status reporting across health endpoints."""
    from sdk.events.kafka_bus import KafkaEventBus

    event_runtime = getattr(app_state, "event_runtime", None)
    if isinstance(event_runtime, KafkaEventBus):
        kafka_ok = event_runtime.is_kafka_available
        if kafka_ok is True:
            return "connected"
        elif kafka_ok is False:
            return "fallback_in_memory"
        else:
            return "not_attempted"
    return "in_memory" if event_runtime else "not_configured"


app = FastAPI(
    title="SalesOS API",
    description="Enterprise Company Intelligence Platform",
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

setup_middleware(app)
register_exception_handlers(app)


@app.get("/ping", response_model=PingResponse)
async def ping():
    return PingResponse(ping="pong")


@app.get("/health/live", response_model=HealthLiveResponse)
async def health_live():
    return HealthLiveResponse(status="alive", uptime_seconds=time.time() - _start_time)


@app.get("/health/detailed")
async def health_detailed(request: Request):
    from sqlalchemy import text

    from app.database import async_session, engine
    from app.metrics.collector import collector as app_collector
    from app.metrics.sla_monitor import sla_monitor

    checks: dict[str, Any] = {}
    overall = "healthy"

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        pool = cast(QueuePool, engine.pool)
        pool_info = {
            "status": "connected",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_open": pool.checkedout() + pool.checkedin(),
        }
        checks["database"] = pool_info
        app_collector.track_db_pool(
            pool.checkedout(),
            pool.checkedin(),
            pool.overflow(),
            pool.checkedout() + pool.checkedin(),
        )
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "message": str(e) if settings.env != "production" else "unavailable",
        }
        overall = "degraded"

    cache = getattr(request.app.state, "cache", None)
    if cache is not None:
        cache_ok = await cache.health()
        checks["cache"] = {"status": "connected" if cache_ok else "unavailable"}
        if not cache_ok:
            overall = "degraded"
    else:
        checks["cache"] = {"status": "not_configured"}

    kg = getattr(request.app.state, "kg_engine", None)
    if kg is None:
        checks["graph"] = {"status": "not_configured"}
    else:
        try:
            graph_ok = await kg.health_check()
            checks["graph"] = {"status": "connected" if graph_ok else "unavailable"}
        except Exception:
            checks["graph"] = {"status": "unavailable"}

    kafka_status = _check_kafka_status(request.app.state)
    if kafka_status.startswith("connected") or kafka_status == "in_memory":
        checks["kafka"] = {"status": kafka_status}
    elif kafka_status == "fallback_in_memory":
        checks["kafka"] = {"status": "fallback_in_memory"}
    else:
        checks["kafka"] = {"status": kafka_status}

    try:
        from app.routers.notifications import _ws_manager

        ws_metrics = await _ws_manager.get_metrics()
        checks["websocket"] = ws_metrics
    except Exception:
        checks["websocket"] = {"status": "unknown"}

    try:
        sla_report = sla_monitor.get_report()
        checks["sla"] = sla_report
    except Exception:
        checks["sla"] = {"status": "unknown"}

    checks["uptime_seconds"] = round(time.time() - _start_time, 1)
    checks["version"] = settings.service_version

    return {"status": overall, "checks": checks}


@app.get("/health/dependencies")
async def health_dependencies(request: Request):
    from sqlalchemy import text

    from app.database import async_session

    deps: dict[str, dict] = {}
    overall = "healthy"

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        deps["postgresql"] = {"status": "connected", "type": "database", "critical": True}
    except Exception as e:
        deps["postgresql"] = {
            "status": "error",
            "type": "database",
            "critical": True,
            "message": str(e) if settings.env != "production" else "unavailable",
        }
        overall = "degraded"

    cache = getattr(request.app.state, "cache", None)
    try:
        if cache is not None:
            cache_ok = await cache.health()
        else:
            cache_ok = False
        deps["redis"] = {
            "status": "connected" if cache_ok else "unavailable",
            "type": "cache",
            "critical": False,
        }
    except Exception as e:
        deps["redis"] = {
            "status": "error",
            "type": "cache",
            "critical": False,
            "message": str(e) if settings.env != "production" else "unavailable",
        }

    kafka_status = _check_kafka_status(request.app.state)
    try:
        deps["kafka"] = {
            "status": kafka_status,
            "type": "message_queue",
            "critical": False,
        }
    except Exception as e:
        deps["kafka"] = {
            "status": "error",
            "type": "message_queue",
            "critical": False,
            "message": str(e) if settings.env != "production" else "unavailable",
        }

    try:
        kg = getattr(request.app.state, "kg_engine", None)
        if kg is None:
            deps["neo4j"] = {
                "status": "not_configured",
                "type": "graph_database",
                "critical": False,
            }
        else:
            is_healthy = await kg.health_check()
            deps["neo4j"] = {
                "status": "connected" if is_healthy else "unavailable",
                "type": "graph_database",
                "critical": False,
            }
    except Exception as e:
        deps["neo4j"] = {
            "status": "error",
            "type": "graph_database",
            "critical": False,
            "message": str(e) if settings.env != "production" else "unavailable",
        }

    try:
        fs = getattr(request.app.state, "feature_store", None)
        deps["feature_store"] = {
            "status": "initialized" if fs else "not_initialized",
            "type": "feature_store",
            "critical": False,
        }
    except Exception:
        deps["feature_store"] = {"status": "unknown", "type": "feature_store", "critical": False}

    return {
        "status": overall,
        "dependencies": deps,
        "summary": {
            "total": len(deps),
            "healthy": sum(
                1
                for d in deps.values()
                if d["status"]
                in (
                    "connected",
                    "active",
                    "initialized",
                    "fallback_in_memory",
                    "not_configured",
                    "in_memory",
                )
            ),
            "degraded": sum(
                1 for d in deps.values() if d["status"] in ("error", "unavailable", "unhealthy")
            ),
        },
    }


@app.get("/health/ready", response_model=HealthReadyResponse)
async def health_ready(request: Request):
    from sqlalchemy import text

    from app.database import async_session

    checks: dict[str, Any] = {}

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception:
        checks["database"] = "unavailable"

    cache = getattr(request.app.state, "cache", None)
    if cache is not None:
        checks["cache"] = "connected" if await cache.health() else "unavailable"
    else:
        checks["cache"] = "unavailable"

    checks["kafka"] = _check_kafka_status(request.app.state)

    kg = getattr(request.app.state, "kg_engine", None)
    if kg is None:
        checks["graph"] = "not_configured"
    else:
        try:
            checks["graph"] = "connected" if await kg.health_check() else "unavailable"
        except Exception:
            checks["graph"] = "unavailable"

    rate_limiter = any(
        "RateLimitMiddleware" in str(m.cls)
        for m in request.app.user_middleware
        if m.cls is not None
    )
    checks["rate_limiter"] = "active" if rate_limiter else "not_configured"

    try:
        from runtime.data_fabric_runtime.scrapers.scraper_config import get_scraper_health

        scraper_health = get_scraper_health()
        checks["scrapers"] = scraper_health
    except Exception:
        checks["scrapers"] = "unavailable"

    all_ready = checks.get("database") == "connected" and checks.get("cache") != "unavailable"
    return HealthReadyResponse(
        status="ready" if all_ready else "not_ready",
        checks=checks,
    )


@app.get("/health", response_model=HealthResponse)
async def health(request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text

    status = "ok"
    checks: dict[str, Any] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception:
        checks["database"] = "unavailable"
        status = "degraded"

    cache = getattr(request.app.state, "cache", None)
    if cache is not None:
        checks["cache"] = "connected" if await cache.health() else "unavailable"
    else:
        checks["cache"] = "unavailable"

    cache_redis = getattr(request.app.state, "cache", None)
    if cache_redis is not None:
        checks["redis"] = "connected" if await cache_redis.health() else "unavailable"
    else:
        checks["redis"] = "unavailable"

    rate_limiter = None
    for m in request.app.user_middleware:
        if m.cls is not None and "RateLimitMiddleware" in m.cls.__name__:
            rate_limiter = m
            break
    checks["rate_limiter"] = "active" if rate_limiter else "not_configured"

    checks["kafka"] = _check_kafka_status(request.app.state)

    try:
        from runtime.data_fabric_runtime.scrapers.scraper_config import get_scraper_health

        scraper_health = get_scraper_health()
        checks["scrapers"] = scraper_health
    except Exception as e:
        checks["scrapers"] = f"error: {e}"

    checks["uptime_seconds"] = time.time() - _start_time

    kg = getattr(request.app.state, "kg_engine", None)
    if kg is None:
        graph_status = "not_configured"
    else:
        try:
            graph_status = "connected" if await kg.health_check() else "unavailable"
        except Exception:
            graph_status = "unavailable"

    return HealthResponse(
        status=status,
        version=settings.service_version,
        database=checks.get("database", "unknown"),
        cache=checks.get("cache", "unknown"),
        graph=graph_status,
        kafka=checks.get("kafka", "not_configured"),
        redis=checks.get("redis", "unknown"),
        rate_limiter=checks.get("rate_limiter", "unknown"),
        uptime_seconds=float(checks["uptime_seconds"]),
    )


@app.get("/api/v1/version", response_model=VersionResponse)
@app.get("/version", response_model=VersionResponse)
async def version(request: Request):
    """Build provenance — backend commit / schema version / OpenAPI hash.

    Canonical endpoint: `/api/v1/version` (matches every other /api/v1/* route so
    the Next.js rewrite proxies it without a new exception). `/version` is kept
    as a backward-compatible alias (second decorator — FastAPI `.get()` accepts
    one path per call; dual positional paths raise TypeError at import).

    Intended for the FE `/system` page and the CI parity gate so that a
    frontend can prove it speaks the same API contract as the deployed backend.
    """
    import hashlib
    import json as _json
    from sqlalchemy import text

    from app.database import async_session

    # OpenAPI schema is built lazily and cached by FastAPI; hash it at first call.
    schema = request.app.openapi()
    openapi_hash = hashlib.sha256(
        _json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    schema_version = ""
    try:
        async with async_session() as session:
            result = await session.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            )
            row = result.first()
            schema_version = row[0] if row else ""
    except Exception:
        schema_version = "unavailable"

    backend_commit = settings.build_commit or os.environ.get(
        "SOURCE_COMMIT", os.environ.get("RAILWAY_GIT_COMMIT_SHA", "")
    )

    return VersionResponse(
        service="salesos-backend",
        api_version=settings.service_version,
        backend_commit=backend_commit,
        build_date=settings.build_date,
        build_id=settings.build_id,
        schema_version=schema_version,
        openapi_hash=openapi_hash,
    )


@app.get("/")
async def root():
    return {
        "name": "SalesOS API",
        "version": settings.service_version,
        "docs": "/docs",
        "health": "/health",
    }


register_routers(app)
