"""SalesOS startup orchestrator — dependency-aware parallel initialization.

Layered architecture:
  Phase 0  Bootstrap           sequential  log + DB + telemetry
  Phase 1  Independent         parallel    20+ services with only DB dependency
  Phase 2  Feature + Opps      parallel    need event_runtime / cache from Phase 1
  Phase 3  Decision pipeline   parallel    need feature_store from Phase 2
  Phase 4  Data fabric + etc   parallel    need multiple Phase 2/3 results
  Phase 5  Background tasks    sequential  WebSocket heartbeats

Each phase uses asyncio.gather(return_exceptions=True) for fault isolation
so one slow/failing service never blocks others in the same phase.
"""

import asyncio
import contextlib
import os
import time
from typing import Any

from fastapi import FastAPI

from app.cache import CacheService
from app.common.logging_config import configure_logging
from app.config import settings
from app.database import async_session, close_db, init_db
from sdk.telemetry import StructuredLogger, setup_telemetry


# ── Phase 0: Bootstrap ──────────────────────────────────────────────────────

async def _phase0_bootstrap(app: FastAPI, logger: StructuredLogger, t_start: float) -> None:
    """Initialize logging, database, module registry, telemetry, Sentry."""

    configure_logging(settings.log_level)
    logger.info("Phase 0 bootstrap started")

    await init_db()
    logger.info(f"  init_db complete (+{time.monotonic() - t_start:.1f}s)")

    from modules.registry import register_modules
    register_modules()
    setup_telemetry("salesos")
    logger.info(f"  modules + telemetry ready (+{time.monotonic() - t_start:.1f}s)")

    if settings.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.env,
                traces_sample_rate=settings.sentry_traces_sample_rate,
            )
            logger.info("  Sentry initialized")
        except Exception:
            logger.exception("  Sentry init failed — continuing")


# ── Phase 1: Independent services (all parallel) ─────────────────────────────

async def _init_cache(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        cache_service = CacheService(
            redis_url=settings.redis_url,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            socket_timeout=settings.redis_socket_timeout,
        )
        cache_ok = await cache_service.health()
        app.state.cache = cache_service
        logger.info(f"  cache: {'connected' if cache_ok else 'unavailable'}")
    except Exception:
        logger.exception("  cache init failed")
        app.state.cache = None


async def _init_event_runtime(app: FastAPI, logger: StructuredLogger) -> None:
    from sdk.events.kafka_bus import KafkaEventBus
    from runtime.event_runtime import EventRuntime

    try:
        if settings.event_bus_type == "kafka":
            event_runtime = KafkaEventBus(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.kafka_group_id,
                auto_offset_reset=settings.kafka_auto_offset_reset,
            )
        else:
            event_runtime = EventRuntime(
                session_factory=async_session,
                logger=logger,
            )
        app.state.event_runtime = event_runtime
        app.state.event_bus = event_runtime
        logger.info(f"  event bus: {settings.event_bus_type}")
    except Exception:
        logger.exception("  event bus init failed — using in-memory fallback")
        event_runtime = EventRuntime(session_factory=async_session, logger=logger)
        app.state.event_runtime = event_runtime
        app.state.event_bus = event_runtime


async def _init_activity(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.activity_runtime import ActivityRuntime

    try:
        ar = ActivityRuntime(session_factory=async_session, logger=logger)
        app.state.activity_runtime = ar

        from app.modules.work_intelligence.service import WorkIntelligenceEngine
        wi = WorkIntelligenceEngine(activity_runtime=ar, logger=logger)
        app.state.work_intelligence_engine = wi
        logger.info("  activity + work_intelligence: ok")
    except Exception:
        logger.exception("  activity runtime init failed")


async def _init_timeline_recorder(app: FastAPI, logger: StructuredLogger) -> None:
    from domains.timeline.engine.postgres_repo import PostgresTimelineRepository
    from domains.timeline.engine.recorder import TimelineRecorder

    try:
        sess = async_session()
        app.state._timeline_session = sess
        repo = PostgresTimelineRepository(sess)
        app.state.timeline_recorder = TimelineRecorder(repo)
        logger.info("  timeline recorder: ok")
    except Exception:
        logger.exception("  timeline recorder init failed")


async def _init_vector_store(app: FastAPI, logger: StructuredLogger) -> None:
    from domains.search.engine.vector_store import PgVectorStore

    try:
        vs = PgVectorStore(session_factory=async_session, collection="vectors")
        app.state.vector_store = vs
        logger.info("  vector store: ok")
    except Exception:
        logger.exception("  vector store init failed")
        app.state.vector_store = None


async def _init_sdk_cache(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from app.common.redis_client import AsyncRedisClient
        from sdk.cache import CacheService as SdkCacheService

        rc = AsyncRedisClient()
        app.state._sdk_redis_client = rc
        healthy = await rc.health() if hasattr(rc, "health") else False
        if healthy:
            app.state._sdk_cache_service = SdkCacheService(rc._redis)
            logger.info("  sdk cache: connected")
        else:
            app.state._sdk_cache_service = None
            logger.info("  sdk cache: unavailable")
    except Exception:
        logger.exception("  sdk cache init failed")
        app.state._sdk_cache_service = None


async def _init_feature_store_domain(app: FastAPI, logger: StructuredLogger) -> None:
    from domains.feature_store import FeatureStoreService as FSDomainService
    from domains.feature_store.postgres_repo import PostgresFeatureStoreRepository

    try:
        sess = async_session()
        app.state._fs_repo_session = sess
        repo = PostgresFeatureStoreRepository(sess)
        app.state.feature_store_domain_service = FSDomainService(repository=repo)
        logger.info("  feature store domain: ok")
    except Exception:
        logger.exception("  feature store domain init failed")


async def _init_knowledge_graph(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.knowledge_graph_runtime import KnowledgeGraphEngine

    try:
        kg = KnowledgeGraphEngine(
            session_factory=async_session,
            neo4j_uri=settings.neo4j_uri,
            neo4j_user=settings.neo4j_user,
            neo4j_password=settings.neo4j_password,
            logger=logger,
        )
        app.state.kg_engine = kg
        logger.info("  knowledge graph: ok")
    except Exception:
        logger.exception("  knowledge graph init failed")
        app.state.kg_engine = None


async def _init_decision_center(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from domains.decision_center.postgres_repo import PostgresDecisionCenterRepository
        from domains.decision_center.service import DecisionCenterService
        sess = async_session()
        app.state._dc_session = sess
        repo = PostgresDecisionCenterRepository(sess)
        app.state.decision_center_service = DecisionCenterService(repository=repo)
        logger.info("  decision center: ok")
    except Exception:
        logger.exception("  decision center init failed")


async def _init_decision_platform(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from app.modules.decision.engine import DecisionEngine as DecisionPlatformEngine
        app.state.decision_platform_engine = DecisionPlatformEngine()
        logger.info("  decision platform: ok")
    except Exception:
        logger.exception("  decision platform init failed")


async def _init_widgets_ux(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from runtime.widget_engine import WidgetRegistry, register_builtin_widgets
        register_builtin_widgets()
        WidgetRegistry.generate_from_capabilities()
        app.state.widget_registry = WidgetRegistry
        logger.info("  widget registry: ok")
    except Exception:
        logger.exception("  widget registry init failed")

    try:
        from runtime.ux_runtime import UXRuntime
        from runtime.ux_runtime.router import set_ux_runtime
        ux = UXRuntime()
        app.state.ux_runtime = ux
        set_ux_runtime(ux)
        logger.info("  ux runtime: ok")
    except Exception:
        logger.exception("  ux runtime init failed")


async def _init_ui_engines(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from runtime.ui_schema_engine import UISchemaEngine
        from runtime.form_engine import FormEngine
        from runtime.action_engine import ActionRegistry
        app.state.schema_engine = UISchemaEngine()
        app.state.form_engine = FormEngine()
        app.state.action_registry = ActionRegistry()
        logger.info("  ui engines (schema/form/action): ok")
    except Exception:
        logger.exception("  ui engines init failed")


async def _init_plugin_sandbox(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from runtime.extension_api import init_hooks
        from runtime.plugin_sandbox import PluginSandbox, register_hook_points
        init_hooks()
        ps = PluginSandbox()
        register_hook_points()
        app.state.plugin_sandbox = ps
        logger.info("  plugin sandbox: ok")
    except Exception:
        logger.exception("  plugin sandbox init failed")


async def _init_scraper(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from runtime.data_fabric_runtime.scrapers.scraper_config import validate_scraper_keys_startup
        validate_scraper_keys_startup()
        logger.info("  scraper keys: ok")
    except Exception:
        logger.exception("  scraper key validation failed")


# ── Phase 2: Feature store + opportunity ─────────────────────────────────────

async def _init_opportunity(app: FastAPI, logger: StructuredLogger) -> None:
    from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository

    try:
        event_runtime = getattr(app.state, "event_runtime", None)
        from domains.commercial.opportunity.engine.service import OpportunityService
        sess = async_session()
        app.state._opportunity_session = sess
        repo = PostgresOpportunityRepository(sess)
        app.state.opportunity_service = OpportunityService(
            repository=repo,
            event_bus=event_runtime,
        )
        logger.info("  opportunity service: ok")
    except Exception:
        logger.exception("  opportunity service init failed")


async def _init_feature_store(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.feature_store import FeatureStore
    from runtime.feature_store.features import (
        ExpansionScoreComputer,
        FundingScoreComputer,
        GrowthScoreComputer,
        HiringScoreComputer,
        IcpComputer,
        IntentScoreComputer,
        RevenueScoreComputer,
    )

    try:
        event_runtime = getattr(app.state, "event_runtime", None)
        cache_svc = getattr(app.state, "_sdk_cache_service", None)
        fs = FeatureStore(
            session_factory=async_session,
            event_runtime=event_runtime,
            computers=[
                IcpComputer(), FundingScoreComputer(), HiringScoreComputer(),
                GrowthScoreComputer(), IntentScoreComputer(),
                ExpansionScoreComputer(), RevenueScoreComputer(),
            ],
            logger=logger,
            cache_service=cache_svc,
            cache_ttl=settings.feature_cache_ttl,
        )
        app.state.feature_store = fs
        logger.info("  feature store: ok")
    except Exception:
        logger.exception("  feature store init failed")
        app.state.feature_store = None


# ── Phase 3: Decision pipeline ───────────────────────────────────────────────

async def _init_policy_engine(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.policy_runtime import PolicyEngine

    try:
        pe = PolicyEngine(session_factory=async_session, logger=logger)
        app.state.policy_engine = pe
        logger.info("  policy engine: ok")
    except Exception:
        logger.exception("  policy engine init failed")


async def _init_recommendation_engine(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.recommendation_runtime import RecommendationEngine

    try:
        re = RecommendationEngine(logger=logger)
        app.state.recommendation_engine = re
        logger.info("  recommendation engine: ok")
    except Exception:
        logger.exception("  recommendation engine init failed")


async def _init_context_builder(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.context_runtime import ContextBuilder

    try:
        fs = getattr(app.state, "feature_store", None)
        cb = ContextBuilder(
            session_factory=async_session,
            feature_store=fs,
            logger=logger,
        )
        app.state.context_builder = cb
        logger.info("  context builder: ok")
    except Exception:
        logger.exception("  context builder init failed")


async def _init_decision_engine(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.decision_runtime import DecisionEngine

    try:
        cb = getattr(app.state, "context_builder", None)
        pe = getattr(app.state, "policy_engine", None)
        re = getattr(app.state, "recommendation_engine", None)
        er = getattr(app.state, "event_runtime", None)
        fs = getattr(app.state, "feature_store", None)
        de = DecisionEngine(
            session_factory=async_session,
            context_builder=cb,
            policy_engine=pe,
            recommendation_engine=re,
            event_runtime=er,
            feature_store=fs,
            logger=logger,
        )
        app.state.decision_engine = de
        logger.info("  decision engine: ok")
    except Exception:
        logger.exception("  decision engine init failed")


async def _init_decision_feedback(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.decision_runtime.feedback_loop import DecisionFeedbackLoop
    from runtime.decision_runtime.registry import DecisionWidgetRegistry, register_default_widgets

    try:
        DecisionWidgetRegistry.reset()
        register_default_widgets()
        fl = DecisionFeedbackLoop(session_factory=async_session, logger=logger)
        app.state.feedback_loop = fl
        logger.info("  decision widgets + feedback: ok")
    except Exception:
        logger.exception("  decision feedback init failed")


async def _init_backend_sdk(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from sdk.backend_sdk import BackendClient
        app.state.backend_sdk = BackendClient(app.state._state)
        logger.info("  backend sdk: ok")
    except Exception:
        logger.exception("  backend sdk init failed")


# ── Phase 4: Data fabric, search, timeline ───────────────────────────────────

async def _init_embedding_service(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from sdk.vector import OpenAIEmbeddingService
        es = OpenAIEmbeddingService()
        app.state._embedding_service = es
        logger.info("  embedding service: ok")
    except Exception:
        logger.exception("  embedding service init failed")
        app.state._embedding_service = None


async def _init_data_fabric(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.data_fabric_runtime import DataFabricPipeline

    try:
        er = getattr(app.state, "event_runtime", None)
        fs = getattr(app.state, "feature_store", None)
        vs = getattr(app.state, "vector_store", None)
        es = getattr(app.state, "_embedding_service", None)
        kg = getattr(app.state, "kg_engine", None)
        df = DataFabricPipeline(
            session_factory=async_session,
            event_runtime=er,
            feature_store=fs,
            vector_store=vs,
            embedding_service=es,
            kg_engine=kg,
            logger=logger,
        )
        app.state.data_fabric = df
        logger.info("  data fabric: ok")
    except Exception:
        logger.exception("  data fabric init failed")
        app.state.data_fabric = None


async def _init_search_runtime(app: FastAPI, logger: StructuredLogger) -> None:
    from domains.search.engine.postgres_repo import PostgresSearchRepository
    from runtime.search_runtime import SearchRuntime

    try:
        es = getattr(app.state, "_embedding_service", None)
        kg = getattr(app.state, "kg_engine", None)
        if es is None:
            from sdk.vector import OpenAIEmbeddingService
            es = OpenAIEmbeddingService()
        sr = SearchRuntime(
            session_factory=async_session,
            embedding_service=es,
            kg_engine=kg,
            logger=logger,
            search_repo=PostgresSearchRepository(session_factory=async_session),
        )
        app.state.search_runtime = sr
        logger.info("  search runtime: ok")
    except Exception:
        logger.exception("  search runtime init failed")


async def _init_timeline_runtime(app: FastAPI, logger: StructuredLogger) -> None:
    from runtime.timeline_runtime import TimelineRuntime

    try:
        tr = TimelineRuntime(session_factory=async_session, logger=logger)
        app.state.timeline_runtime = tr
        logger.info("  timeline runtime: ok")
    except Exception:
        logger.exception("  timeline runtime init failed")


async def _init_workflow_subscriber(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from domains.workflow.postgres_repo import PostgresWorkflowRepository
        from domains.workflow.service import WorkflowService
        from domains.workflow.engine import WorkflowEngine
        from domains.workflow.event_subscriber import WorkflowEventSubscriber

        event_runtime = getattr(app.state, "event_runtime", None)
        if event_runtime is None:
            logger.warning("  workflow subscriber: skipped (no event_runtime)")
            return

        sess = async_session()
        app.state._workflow_session = sess
        repo = PostgresWorkflowRepository(session=sess)
        engine = WorkflowEngine(repository=repo)
        service = WorkflowService(repository=repo, engine=engine)

        subscriber = WorkflowEventSubscriber(
            workflow_service=service,
            event_bus=event_runtime,
            engine=engine,
        )
        await subscriber.start()
        app.state.workflow_subscriber = subscriber
        logger.info("  workflow subscriber: ok")
    except Exception:
        logger.exception("  workflow subscriber init failed")


async def _init_timeline_subscriber(app: FastAPI, logger: StructuredLogger) -> None:
    try:
        from sdk.events.base import DomainEvent
        event_runtime = getattr(app.state, "event_runtime", None)
        if event_runtime is None:
            return

        async def _on_timeline_event(event: DomainEvent) -> None:
            try:
                ar = getattr(app.state, "activity_runtime", None)
                tr = getattr(app.state, "timeline_runtime", None)
                rec = getattr(app.state, "timeline_recorder", None)
                d = event.to_dict_legacy() if hasattr(event, "to_dict_legacy") else event
                if ar:
                    await ar.on_domain_event(d)
                if tr:
                    await tr.on_domain_event(d)
                if rec:
                    await rec.on_domain_event(d)
            except Exception:
                pass

        event_runtime.subscribe("*", _on_timeline_event)
        logger.info("  timeline subscriber: ok")
    except Exception:
        logger.exception("  timeline subscriber init failed")


# ── Phase 5: Background tasks ────────────────────────────────────────────────

async def _phase5_background(app: FastAPI, logger: StructuredLogger) -> list[asyncio.Task]:
    tasks: list[asyncio.Task] = []
    try:
        from app.routers.notifications import _ws_manager
        tasks.append(asyncio.create_task(_ws_manager.heartbeat_loop(interval=30.0)))
        tasks.append(asyncio.create_task(_ws_manager.cleanup_task(interval=30.0)))
        logger.info("  websocket background tasks started")
    except Exception:
        logger.exception("  websocket background tasks init failed")
    return tasks


# ── Orchestrator ─────────────────────────────────────────────────────────────

async def init_startup_services(app: FastAPI) -> list[asyncio.Task]:
    """Orchestrate layered parallel startup of all SalesOS services."""

    # Only skip boot when explicitly testing ("1"/"true"). Compose sets
    # SALESOS_TESTING=0 which must NOT skip init (Python truthy string trap).
    _testing = os.environ.get("SALESOS_TESTING", "").strip().lower()
    if _testing in ("1", "true", "yes", "on"):
        return []

    t_start = time.monotonic()
    logger = StructuredLogger("salesos.boot")
    app.state.logger = logger
    logger.info("SalesOS startup sequence initiated")

    # ── Phase 0: Bootstrap (sequential) ──────────────────────────────────
    try:
        await _phase0_bootstrap(app, logger, t_start)
    except Exception:
        logger.exception("Phase 0 bootstrap failed — continuing with degraded mode")
        # Do NOT re-raise: app must still serve /health and basic endpoints

    # ── Phase 1: Independent services (parallel) ─────────────────────────
    logger.info("Phase 1: parallel independent services")
    p1_start = time.monotonic()

    phase1_tasks = [
        _init_cache(app, logger),
        _init_event_runtime(app, logger),
        _init_activity(app, logger),
        _init_timeline_recorder(app, logger),
        _init_vector_store(app, logger),
        _init_sdk_cache(app, logger),
        _init_feature_store_domain(app, logger),
        _init_knowledge_graph(app, logger),
        _init_decision_center(app, logger),
        _init_decision_platform(app, logger),
        _init_widgets_ux(app, logger),
        _init_ui_engines(app, logger),
        _init_plugin_sandbox(app, logger),
        _init_scraper(app, logger),
    ]
    await asyncio.gather(*phase1_tasks, return_exceptions=True)
    logger.info(f"Phase 1 complete (+{time.monotonic() - p1_start:.1f}s)")

    # ── Phase 2: Feature store + opportunity (parallel) ──────────────────
    logger.info("Phase 2: feature store + opportunity service")
    p2_start = time.monotonic()

    await asyncio.gather(
        _init_opportunity(app, logger),
        _init_feature_store(app, logger),
        return_exceptions=True,
    )
    logger.info(f"Phase 2 complete (+{time.monotonic() - p2_start:.1f}s)")

    # ── Phase 3: Decision pipeline (parallel) ────────────────────────────
    logger.info("Phase 3: decision pipeline")
    p3_start = time.monotonic()

    await asyncio.gather(
        _init_policy_engine(app, logger),
        _init_recommendation_engine(app, logger),
        _init_context_builder(app, logger),
        _init_backend_sdk(app, logger),
        return_exceptions=True,
    )
    await asyncio.gather(
        _init_decision_engine(app, logger),
        _init_decision_feedback(app, logger),
        return_exceptions=True,
    )
    logger.info(f"Phase 3 complete (+{time.monotonic() - p3_start:.1f}s)")

    # ── Phase 4: Data fabric + search + timeline (parallel) ──────────────
    logger.info("Phase 4: data fabric + search + timeline")
    p4_start = time.monotonic()

    await _init_embedding_service(app, logger)
    await asyncio.gather(
        _init_data_fabric(app, logger),
        _init_search_runtime(app, logger),
        _init_timeline_runtime(app, logger),
        return_exceptions=True,
    )
    await _init_timeline_subscriber(app, logger)
    await _init_workflow_subscriber(app, logger)
    logger.info(f"Phase 4 complete (+{time.monotonic() - p4_start:.1f}s)")

    # ── Phase 5: Background tasks ────────────────────────────────────────
    tasks = await _phase5_background(app, logger)

    elapsed = time.monotonic() - t_start
    logger.info(f"SalesOS startup complete in {elapsed:.1f}s")
    return tasks


# ── Shutdown ─────────────────────────────────────────────────────────────────

async def shutdown_services(app: FastAPI) -> None:
    logger = getattr(app.state, "logger", None)

    async def _safe_close(name: str, close_fn):
        try:
            await close_fn
            if logger:
                logger.info(f"Shutdown: {name} closed")
        except Exception:
            if logger:
                logger.exception(f"Shutdown: {name} close failed")

    closeables: list[tuple[str, Any]] = [
        ("kg_engine", getattr(app.state, "kg_engine", None)),
        ("cache_service", getattr(app.state, "cache", None)),
        ("event_runtime", getattr(app.state, "event_runtime", None)),
        ("search_runtime", getattr(app.state, "search_runtime", None)),
        ("feature_store", getattr(app.state, "feature_store", None)),
        ("data_fabric", getattr(app.state, "data_fabric", None)),
        ("timeline_runtime", getattr(app.state, "timeline_runtime", None)),
        ("activity_runtime", getattr(app.state, "activity_runtime", None)),
        ("decision_engine", getattr(app.state, "decision_engine", None)),
        ("context_builder", getattr(app.state, "context_builder", None)),
        ("policy_engine", getattr(app.state, "policy_engine", None)),
        ("feedback_loop", getattr(app.state, "feedback_loop", None)),
        ("ux_runtime", getattr(app.state, "ux_runtime", None)),
        ("sdk_redis_client", getattr(app.state, "_sdk_redis_client", None)),
    ]

    for name, svc in closeables:
        if svc is not None and hasattr(svc, "close"):
            await _safe_close(name, svc.close())

    for sess_attr in ("_timeline_session", "_opportunity_session", "_fs_repo_session", "_dc_session", "_workflow_session"):
        sess = getattr(app.state, sess_attr, None)
        if sess:
            with contextlib.suppress(Exception):
                await sess.close()

    await _safe_close("database", close_db())
    if logger:
        logger.info("SalesOS shutdown complete")
