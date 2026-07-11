import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.middleware import RequestIDMiddleware, RequestLoggingMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.common.metrics import metrics
from app.routers.metrics import MetricsMiddleware
from app.config import settings
from app.database import get_db
from sdk.events.base import DomainEvent
from sdk.telemetry import StructuredLogger, setup_telemetry
from sdk.vector import OpenAIEmbeddingService
from runtime import (
    ContextBuilder,
    DataFabricPipeline,
    DecisionEngine,
    DecisionFeedbackLoop,
    EventRuntime,
    FeatureStore,
    KnowledgeGraphEngine,
    PolicyEngine,
    RecommendationEngine,
    SearchRuntime,
    TimelineRuntime,
)
from runtime.activity_runtime import ActivityRuntime
from runtime.feature_store.features import (
    IcpComputer,
    FundingScoreComputer,
    HiringScoreComputer,
    GrowthScoreComputer,
    IntentScoreComputer,
    ExpansionScoreComputer,
    RevenueScoreComputer,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import async_session, close_db, init_db
    from modules.registry import register_modules

    if os.environ.get("SALESOS_TESTING"):
        yield
    else:
        # Configure JSON logging before anything else
        from app.common.logging_config import configure_logging
        configure_logging(settings.log_level)

        await init_db()
        register_modules()
        setup_telemetry("salesos")

        if settings.sentry_dsn:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.env,
                traces_sample_rate=settings.sentry_traces_sample_rate,
            )
            if app.state.logger:
                app.state.logger.info("Sentry initialized: dsn=%s env=%s", settings.sentry_dsn[:20] + "...", settings.env)

        app.state.logger = StructuredLogger("salesos.api")

        # ── Event Runtime ──
        if settings.event_bus_type == "kafka":
            from sdk.events.kafka_bus import KafkaEventBus
            event_runtime = KafkaEventBus(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_group_id,
                auto_offset_reset=settings.kafka_auto_offset_reset,
            )
        else:
            event_runtime = EventRuntime(
                session_factory=async_session,
                logger=app.state.logger,
            )
        app.state.event_runtime = event_runtime
        # Backward compat: services expect app.state.event_bus
        app.state.event_bus = event_runtime

        # ── Activity Runtime (unified activity spine) ──
        activity_runtime = ActivityRuntime(
            session_factory=async_session,
            logger=app.state.logger,
        )
        app.state.activity_runtime = activity_runtime

        # ── Work Intelligence Engine ──
        from app.modules.work_intelligence.service import WorkIntelligenceEngine
        work_intelligence_engine = WorkIntelligenceEngine(
            activity_runtime=activity_runtime,
            logger=app.state.logger,
        )
        app.state.work_intelligence_engine = work_intelligence_engine

        # ── Timeline Recorder (PostgreSQL-backed) ──
        from domains.timeline.engine.recorder import TimelineRecorder
        from domains.timeline.engine.postgres_repo import PostgresTimelineRepository
        timeline_repo = PostgresTimelineRepository(async_session())
        timeline_recorder = TimelineRecorder(timeline_repo)
        app.state.timeline_repo = timeline_repo
        app.state.timeline_recorder = timeline_recorder

        # ── Opportunity Service (PostgreSQL-backed, used by opportunities router) ──
        from domains.commercial.opportunity.engine.service import OpportunityService
        from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository
        opp_session = async_session()
        opp_repo = PostgresOpportunityRepository(opp_session)
        app.state.opportunity_service = OpportunityService(
            repository=opp_repo,
            event_bus=event_runtime,
        )

        # ── PgVectorStore (production vector search) ──
        from domains.search.engine.vector_store import PgVectorStore
        vector_store = PgVectorStore(session_factory=async_session, collection="vectors")
        app.state.vector_store = vector_store

        # ── Feature Store ──
        feature_store = FeatureStore(
            session_factory=async_session,
            event_runtime=event_runtime,
            computers=[
                IcpComputer(),
                FundingScoreComputer(),
                HiringScoreComputer(),
                GrowthScoreComputer(),
                IntentScoreComputer(),
                ExpansionScoreComputer(),
                RevenueScoreComputer(),
            ],
            logger=app.state.logger,
        )
        app.state.feature_store = feature_store

        # ── Knowledge Graph Runtime ──
        try:
            kg_engine = KnowledgeGraphEngine(
                session_factory=async_session,
                neo4j_uri=settings.neo4j_uri,
                neo4j_user=settings.neo4j_user,
                neo4j_password=settings.neo4j_password,
                logger=app.state.logger,
            )
            app.state.kg_engine = kg_engine
        except Exception:
            app.state.logger.warning("Neo4j unavailable — KG engine disabled")
            kg_engine = None
            app.state.kg_engine = None

        # ── Data Fabric Runtime ──
        data_fabric = DataFabricPipeline(
            session_factory=async_session,
            event_runtime=event_runtime,
            feature_store=feature_store,
            vector_store=vector_store,
            embedding_service=OpenAIEmbeddingService(),
            kg_engine=kg_engine,
            logger=app.state.logger,
        )
        app.state.data_fabric = data_fabric

        # ── Decision Intelligence Engine (DIE) ──
        context_builder = ContextBuilder(
            session_factory=async_session,
            feature_store=feature_store,
            logger=app.state.logger,
        )
        policy_engine = PolicyEngine(
            session_factory=async_session,
            logger=app.state.logger,
        )
        recommendation_engine = RecommendationEngine(
            logger=app.state.logger,
        )
        decision_engine = DecisionEngine(
            session_factory=async_session,
            context_builder=context_builder,
            policy_engine=policy_engine,
            recommendation_engine=recommendation_engine,
            event_runtime=event_runtime,
            feature_store=feature_store,
            logger=app.state.logger,
        )
        app.state.context_builder = context_builder
        app.state.policy_engine = policy_engine
        app.state.recommendation_engine = recommendation_engine
        app.state.decision_engine = decision_engine

        # Decision Feedback Loop
        feedback_loop = DecisionFeedbackLoop(
            session_factory=async_session,
            logger=app.state.logger,
        )
        app.state.feedback_loop = feedback_loop

        # ── Decision Platform Engine (module-level) ──
        from app.modules.decision.engine import DecisionEngine as DecisionPlatformEngine
        app.state.decision_platform_engine = DecisionPlatformEngine()

        # ── Universal Timeline Runtime ──
        timeline_runtime = TimelineRuntime(
            session_factory=async_session,
            logger=app.state.logger,
        )
        app.state.timeline_runtime = timeline_runtime
        # Subscribe Activity Runtime + Universal Timeline + legacy recorder to ALL domain events
        async def _on_timeline_event(event: DomainEvent) -> None:
            await activity_runtime.on_domain_event(event.to_dict_legacy())
            await timeline_runtime.on_domain_event(event.to_dict_legacy())
            await timeline_recorder.on_domain_event(event.to_dict_legacy())

        event_runtime.subscribe("*", _on_timeline_event)

        # ── Search Runtime ──
        search_runtime = SearchRuntime(
            session_factory=async_session,
            embedding_service=OpenAIEmbeddingService(),
            kg_engine=kg_engine,
            logger=app.state.logger,
        )
        app.state.search_runtime = search_runtime

        # ── Widget Engine ──
        from runtime.widget_engine import WidgetRegistry, register_builtin_widgets
        register_builtin_widgets()
        WidgetRegistry.generate_from_capabilities()
        app.state.widget_registry = WidgetRegistry

        # ── UX Runtime (Experience Layer) ──
        from runtime.ux_runtime import UXRuntime
        from runtime.ux_runtime.router import set_ux_runtime
        ux_runtime = UXRuntime()
        app.state.ux_runtime = ux_runtime
        set_ux_runtime(ux_runtime)
        app.state.object_viewer = None  # lazy init via UniversalObjectViewer

        # ── Platform SDK ──
        from sdk.backend_sdk import BackendClient
        backend_sdk = BackendClient(app.state._state)
        app.state.backend_sdk = backend_sdk

        # ── UI Schema Engine ──
        from runtime.ui_schema_engine import UISchemaEngine
        schema_engine = UISchemaEngine()
        app.state.schema_engine = schema_engine

        # ── Form Engine ──
        from runtime.form_engine import FormEngine
        form_engine = FormEngine()
        app.state.form_engine = form_engine

        # ── Action Engine ──
        from runtime.action_engine import ActionRegistry
        action_registry = ActionRegistry()
        app.state.action_registry = action_registry

        # ── Extension API ──
        from runtime.extension_api import init_hooks
        init_hooks()

        # ── Plugin Sandbox ──
        from runtime.plugin_sandbox import PluginSandbox, register_hook_points
        plugin_sandbox = PluginSandbox()
        register_hook_points()
        app.state.plugin_sandbox = plugin_sandbox

        yield
        kg = getattr(app.state, "kg_engine", None)
        if kg is not None:
            await kg.close()
        await close_db()


_start_time = time.time()

app = FastAPI(
    title="SalesOS API",
    description="Enterprise Company Intelligence Platform",
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_hosts.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=[m.strip() for m in settings.cors_allow_methods.split(",") if m.strip()],
    allow_headers=[h.strip() for h in settings.cors_allow_headers.split(",") if h.strip()],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)

# Redis-backed rate limiter (falls back to in-memory if Redis unavailable)
_redis = None
try:
    import redis.asyncio as aioredis
    _redis = aioredis.Redis.from_url(settings.redis_url)
except Exception:
    pass
app.add_middleware(RateLimitMiddleware, rate=settings.rate_limit_default, window=settings.rate_limit_window, redis_client=_redis)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger = getattr(request.app.state, "logger", None)
    if logger:
        logger.exception("Unhandled exception: %s %s", request.method, request.url.path)
    else:
        traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.get("/health/live")
async def health_live():
    """Kubernetes liveness probe — simple process health."""
    return {"status": "alive", "uptime_seconds": time.time() - _start_time}

@app.get("/health/ready")
async def health_ready(request: Request):
    """Kubernetes readiness probe — checks critical dependencies."""
    from sqlalchemy import text
    from app.database import async_session
    from app.config import settings

    checks = {}

    # Database
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis / Cache
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.redis_url, socket_connect_timeout=settings.redis_health_socket_connect_timeout, socket_timeout=settings.redis_health_socket_timeout)
        await r.ping()
        await r.aclose()
        checks["cache"] = "connected"
    except Exception:
        checks["cache"] = "unavailable"

    # Kafka
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
        checks["kafka"] = "active" if event_runtime else "not_configured"

    # Neo4j / KG
    kg = getattr(request.app.state, "kg_engine", None)
    checks["graph"] = "connected" if kg is not None and kg.metrics.neo4j_available else "not_configured"

    # Rate limiter
    rate_limiter = any(
        "RateLimitMiddleware" in str(m.cls)
        for m in request.app.user_middleware
        if m.cls is not None
    )
    checks["rate_limiter"] = "active" if rate_limiter else "not_configured"

    all_ready = checks.get("database") == "connected" and checks.get("cache") != "unavailable"
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
    }

@app.get("/health")
async def health(request: Request, db: AsyncSession = Depends(get_db)):
    from app.common.schemas import HealthResponse
    from sqlalchemy import text

    status = "ok"
    checks = {}

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {e}"
        status = "degraded"

    # Redis / Cache
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.redis_url, socket_connect_timeout=settings.redis_health_socket_connect_timeout, socket_timeout=settings.redis_health_socket_timeout)
        await r.ping()
        await r.aclose()
        checks["cache"] = "connected"
    except Exception:
        checks["cache"] = "unavailable"

    # Redis connectivity (reuses same connection)
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(settings.redis_url, socket_connect_timeout=settings.redis_health_socket_connect_timeout, socket_timeout=settings.redis_health_socket_timeout)
        await r.ping()
        await r.aclose()
        checks["redis"] = "connected"
    except Exception:
        checks["redis"] = "unavailable"

    # Rate limiter health
    rate_limiter = None
    for m in request.app.user_middleware:
        if m.cls is not None and "RateLimitMiddleware" in m.cls.__name__:
            rate_limiter = m
            break
    checks["rate_limiter"] = "active" if rate_limiter else "not_configured"

    # Neo4j / Knowledge Graph
    kg = getattr(request.app.state, "kg_engine", None)
    checks["graph"] = "connected" if kg is not None and kg.metrics.neo4j_available else "not_configured"

    # Kafka connectivity check
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
        checks["kafka"] = "active" if kafka_bus else "not_configured"

    # Uptime
    checks["uptime_seconds"] = time.time() - _start_time

    return HealthResponse(
        status=status,
        version=settings.service_version,
        database=checks.get("database", "unknown"),
        cache=checks.get("cache", "unknown"),
        graph=checks.get("graph", "not_configured"),
        kafka=checks.get("kafka", "not_configured"),
        redis=checks.get("redis", "unknown"),
        rate_limiter=checks.get("rate_limiter", "unknown"),
        uptime_seconds=checks["uptime_seconds"],
    )


@app.get("/")
async def root():
    return {
        "name": "SalesOS API",
        "version": settings.service_version,
        "docs": "/docs",
        "health": "/health",
    }


def register_routers():
    from app.dependencies import verify_token
    from fastapi import Depends

    _auth = [Depends(verify_token)]

    from app.routers.metrics import router as metrics_router
    app.include_router(metrics_router, tags=["Metrics"])

    from runtime.admin_router import router as admin_router
    app.include_router(admin_router, tags=["Admin"])

    from app.modules.company.router import router as company_router
    from app.modules.contact.router import router as contact_router
    from app.modules.entity_resolution.router import router as entity_resolution_router
    from app.modules.identity.router import router as identity_router
    from app.modules.notion_sync.router import router as notion_sync_router
    from app.modules.excel_import.router import router as excel_import_router
    from app.modules.employee_360.router import router as employee_360_router
    from app.modules.executive.router import router as executive_router
    from app.application.dashboard.router import router as dashboard_router
    from app.modules.work_intelligence.router import router as work_intelligence_router
    from app.modules.decision.router import router as decision_platform_router
    from app.modules.revenue_execution.router import router as revenue_execution_router
    from app.modules.monitoring.router import router as monitoring_router
    from app.routers.commercial import router as commercial_router
    from app.routers.copilot import router as copilot_router
    from runtime.capability_framework.router import router as capability_router
    from runtime.data_fabric_runtime.router import router as data_fabric_router
    from runtime.decision_runtime.router import router as decision_router
    from runtime.event_runtime.router import router as event_runtime_router
    from runtime.feature_store.router import router as feature_store_router
    from runtime.knowledge_graph_runtime.router import router as graph_router
    from runtime.search_runtime.router import router as search_router
    from runtime.activity_runtime.router import router as activity_router
    from runtime.timeline_runtime.router import router as timeline_router
    from runtime.ux_runtime.router import router as ux_router

    app.include_router(identity_router, prefix="/api/v1/identity", tags=["Identity"])
    app.include_router(notion_sync_router, prefix="/api/v1", tags=["Notion Sync"], dependencies=_auth)
    app.include_router(excel_import_router, prefix="/api/v1", tags=["Excel Import"], dependencies=_auth)
    app.include_router(employee_360_router, prefix="/api/v1", tags=["Employee 360"], dependencies=_auth)
    app.include_router(executive_router, prefix="/api/v1", tags=["Executive"], dependencies=_auth)
    app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"], dependencies=_auth)
    app.include_router(work_intelligence_router, prefix="/api/v1", tags=["Work Intelligence"], dependencies=_auth)
    app.include_router(decision_platform_router, prefix="", tags=["Decision Platform"], dependencies=_auth)
    app.include_router(revenue_execution_router, prefix="", tags=["Revenue Execution"], dependencies=_auth)
    app.include_router(company_router, prefix="/api/v1/companies", tags=["Companies"], dependencies=_auth)
    app.include_router(contact_router, prefix="/api/v1/contacts", tags=["Contacts"], dependencies=_auth)
    app.include_router(activity_router, prefix="/api/v1", tags=["Activity"], dependencies=_auth)
    app.include_router(entity_resolution_router, prefix="/api/v1/entity-resolution", tags=["Entity Resolution"], dependencies=_auth)
    app.include_router(event_runtime_router, prefix="/api/v1", tags=["Event Runtime"], dependencies=_auth)
    app.include_router(data_fabric_router, prefix="/api/v1", tags=["Data Fabric"], dependencies=_auth)
    app.include_router(feature_store_router, prefix="/api/v1", tags=["Feature Store"], dependencies=_auth)
    app.include_router(decision_router, prefix="/api/v1", tags=["Decision Engine"], dependencies=_auth)
    app.include_router(graph_router, prefix="/api/v1", tags=["Knowledge Graph"], dependencies=_auth)
    app.include_router(timeline_router, prefix="/api/v1", tags=["Timeline"], dependencies=_auth)
    app.include_router(search_router, prefix="/api/v1", tags=["Search"], dependencies=_auth)
    from app.routers.search import router as search_api_router
    app.include_router(search_api_router, prefix="/api/v1", tags=["Search"], dependencies=_auth)
    app.include_router(capability_router, dependencies=_auth)
    app.include_router(ux_router, dependencies=_auth)

    # XP1 — Schema-Driven UI
    from runtime.ui_schema_engine.router import router as schema_router
    from runtime.form_engine.router import router as form_router
    from runtime.action_engine.router import router as action_router
    from runtime.extension_api.router import router as extension_router
    from runtime.plugin_sandbox.router import router as plugin_router
    app.include_router(schema_router, dependencies=_auth)
    app.include_router(form_router, dependencies=_auth)
    app.include_router(action_router, dependencies=_auth)
    app.include_router(extension_router, dependencies=_auth)
    app.include_router(plugin_router, dependencies=_auth)

    app.include_router(monitoring_router, tags=["Monitoring"])
    app.include_router(copilot_router, prefix="/api/v1", tags=["Copilot"], dependencies=_auth)
    app.include_router(commercial_router, prefix="/api/v1", tags=["Commercial"], dependencies=_auth)

    # Wave 3 — Workflow Engine
    from app.routers.workflows import router as workflow_router
    app.include_router(workflow_router, prefix="/api/v1", tags=["Workflow Engine"], dependencies=_auth)

    # Wave 2 — Revenue Execution Platform
    from app.routers.opportunities import router as opportunities_router
    from app.routers.meetings import router as meetings_router
    from app.routers.revenue import router as revenue_router
    from runtime.nba_engine.api.router import router as nba_router
    from runtime.pipeline_analytics.router import router as pipeline_analytics_router

    app.include_router(opportunities_router, prefix="/api/v1", tags=["Opportunities"], dependencies=_auth)
    app.include_router(meetings_router, prefix="/api/v1", tags=["Meeting Intelligence"], dependencies=_auth)
    app.include_router(revenue_router, prefix="/api/v1", tags=["Revenue"], dependencies=_auth)
    app.include_router(nba_router, prefix="/api/v1", tags=["NBA Engine"], dependencies=_auth)
    app.include_router(pipeline_analytics_router, prefix="/api/v1", tags=["Pipeline Analytics"], dependencies=_auth)

    # Wave 3 — RAG Pipeline
    from app.routers.rag import router as rag_router
    app.include_router(rag_router, prefix="/api/v1", tags=["RAG"], dependencies=_auth)


register_routers()
