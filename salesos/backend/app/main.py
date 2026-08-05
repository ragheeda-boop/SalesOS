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

    from sdk.events.kafka_bus import KafkaEventBus

    event_runtime = getattr(request.app.state, "event_runtime", None)
    if isinstance(event_runtime, KafkaEventBus):
        kafka_ok = event_runtime.is_kafka_available
        checks["kafka"] = {"status": "connected" if kafka_ok else "fallback_in_memory"}
    elif event_runtime is not None:
        # Default EVENT_BUS_TYPE=in_memory — Kafka not required for GA (documented degraded).
        checks["kafka"] = {"status": "in_memory"}
    else:
        checks["kafka"] = {"status": "not_configured"}

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

    from sdk.events.kafka_bus import KafkaEventBus

    event_runtime = getattr(request.app.state, "event_runtime", None)
    try:
        if isinstance(event_runtime, KafkaEventBus):
            kafka_ok = event_runtime.is_kafka_available
            deps["kafka"] = {
                "status": "connected" if kafka_ok else "fallback_in_memory",
                "type": "message_queue",
                "critical": False,
            }
        else:
            deps["kafka"] = {
                "status": "in_memory" if event_runtime else "not_configured",
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

    from sdk.events.kafka_bus import KafkaEventBus

    event_runtime = getattr(request.app.state, "event_runtime", None)
    if isinstance(event_runtime, KafkaEventBus):
        kafka_ok = event_runtime.is_kafka_available
        if kafka_ok is True:
            checks["kafka"] = "connected"
        elif kafka_ok is False:
            checks["kafka"] = "fallback_in_memory"
        else:
            checks["kafka"] = "not_attempted"
    else:
        checks["kafka"] = "in_memory" if event_runtime else "not_configured"

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

    from sdk.events.kafka_bus import KafkaEventBus

    kafka_bus = getattr(request.app.state, "event_runtime", None)
    if isinstance(kafka_bus, KafkaEventBus):
        kafka_ok = kafka_bus.is_kafka_available
        if kafka_ok is True:
            checks["kafka"] = "connected"
        elif kafka_ok is False:
            checks["kafka"] = "fallback_in_memory"
        else:
            checks["kafka"] = "not_attempted"
    else:
        checks["kafka"] = "in_memory" if kafka_bus else "not_configured"

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


@app.get("/")
async def root():
    return {
        "name": "SalesOS API",
        "version": settings.service_version,
        "docs": "/docs",
        "health": "/health",
    }


register_routers(app)
