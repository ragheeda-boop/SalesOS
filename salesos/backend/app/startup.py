import asyncio
import os
from typing import Any

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import CacheService
from app.common.logging_config import configure_logging
from app.config import settings
from app.database import async_session, close_db, init_db
from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository
from domains.feature_store import FeatureStoreService as FeatureStoreDomainService
from domains.feature_store.postgres_repo import PostgresFeatureStoreRepository
from domains.search.engine.postgres_repo import PostgresSearchRepository
from domains.search.engine.vector_store import PgVectorStore
from domains.timeline.engine.postgres_repo import PostgresTimelineRepository
from domains.timeline.engine.recorder import TimelineRecorder
from modules.registry import register_modules
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
from runtime.data_fabric_runtime.scrapers.scraper_config import validate_scraper_keys_startup
from runtime.feature_store.features import (
    ExpansionScoreComputer,
    FundingScoreComputer,
    GrowthScoreComputer,
    HiringScoreComputer,
    IcpComputer,
    IntentScoreComputer,
    RevenueScoreComputer,
)
from sdk.backend_sdk import BackendClient
from sdk.events.base import DomainEvent
from sdk.events.kafka_bus import KafkaEventBus
from sdk.telemetry import StructuredLogger, setup_telemetry
from sdk.vector import OpenAIEmbeddingService
from runtime.decision_runtime.registry import DecisionWidgetRegistry, register_default_widgets
from runtime.widget_engine import WidgetRegistry, register_builtin_widgets
from runtime.ux_runtime import UXRuntime
from runtime.ux_runtime.router import set_ux_runtime
from runtime.ui_schema_engine import UISchemaEngine
from runtime.form_engine import FormEngine
from runtime.action_engine import ActionRegistry
from runtime.extension_api import init_hooks
from runtime.plugin_sandbox import PluginSandbox, register_hook_points


async def init_startup_services(app: FastAPI) -> list[asyncio.Task]:
    _testing = os.environ.get("SALESOS_TESTING", "").strip().lower()
    if _testing in ("1", "true", "yes", "on"):
        return []

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
            app.state.logger.info(f"Sentry initialized: env={settings.env}")

    app.state.logger = StructuredLogger("salesos.api")

    cache_service = CacheService(
        redis_url=settings.redis_url,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        socket_timeout=settings.redis_socket_timeout,
    )
    cache_ok = await cache_service.health()
    app.state.cache = cache_service
    if app.state.logger:
        app.state.logger.info(f"Cache service {'connected' if cache_ok else 'unavailable'}")

    validate_scraper_keys_startup()

    if settings.event_bus_type == "kafka":
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
    app.state.event_bus = event_runtime

    activity_runtime = ActivityRuntime(
        session_factory=async_session,
        logger=app.state.logger,
    )
    app.state.activity_runtime = activity_runtime

    from app.modules.work_intelligence.service import WorkIntelligenceEngine
    work_intelligence_engine = WorkIntelligenceEngine(
        activity_runtime=activity_runtime,
        logger=app.state.logger,
    )
    app.state.work_intelligence_engine = work_intelligence_engine

    timeline_repo = PostgresTimelineRepository(async_session())
    timeline_recorder = TimelineRecorder(timeline_repo)
    app.state.timeline_repo = timeline_repo
    app.state.timeline_recorder = timeline_recorder

    from domains.commercial.opportunity.engine.service import OpportunityService
    opp_session = async_session()
    opp_repo = PostgresOpportunityRepository(opp_session)
    app.state.opportunity_service = OpportunityService(
        repository=opp_repo,
        event_bus=event_runtime,
    )

    vector_store = PgVectorStore(session_factory=async_session, collection="vectors")
    app.state.vector_store = vector_store

    from app.common.redis_client import AsyncRedisClient
    from sdk.cache import CacheService as SdkCacheService
    _redis_client = AsyncRedisClient()
    _cache_service: Any = None
    if await _redis_client.health():
        _cache_service = SdkCacheService(_redis_client._redis)

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
        cache_service=_cache_service,
        cache_ttl=settings.feature_cache_ttl,
    )
    app.state.feature_store = feature_store

    fs_repo = PostgresFeatureStoreRepository(async_session)
    fs_domain_service = FeatureStoreDomainService(repository=fs_repo)
    app.state.feature_store_domain_service = fs_domain_service

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

    DecisionWidgetRegistry.reset()
    register_default_widgets()

    feedback_loop = DecisionFeedbackLoop(
        session_factory=async_session,
        logger=app.state.logger,
    )
    app.state.feedback_loop = feedback_loop

    from app.modules.decision.engine import DecisionEngine as DecisionPlatformEngine
    app.state.decision_platform_engine = DecisionPlatformEngine()

    from domains.decision_center.postgres_repo import PostgresDecisionCenterRepository
    from domains.decision_center.service import DecisionCenterService
    dc_repo = PostgresDecisionCenterRepository(async_session())
    dc_service = DecisionCenterService(repository=dc_repo)
    app.state.decision_center_service = dc_service

    timeline_runtime = TimelineRuntime(
        session_factory=async_session,
        logger=app.state.logger,
    )
    app.state.timeline_runtime = timeline_runtime

    async def _on_timeline_event(event: DomainEvent) -> None:
        await activity_runtime.on_domain_event(event.to_dict_legacy())
        await timeline_runtime.on_domain_event(event.to_dict_legacy())
        await timeline_recorder.on_domain_event(event.to_dict_legacy())

    event_runtime.subscribe("*", _on_timeline_event)

    search_repo = PostgresSearchRepository(session_factory=async_session)
    search_runtime = SearchRuntime(
        session_factory=async_session,
        embedding_service=OpenAIEmbeddingService(),
        kg_engine=kg_engine,
        logger=app.state.logger,
        search_repo=search_repo,
    )
    app.state.search_runtime = search_runtime

    register_builtin_widgets()
    WidgetRegistry.generate_from_capabilities()
    app.state.widget_registry = WidgetRegistry

    ux_runtime = UXRuntime()
    app.state.ux_runtime = ux_runtime
    set_ux_runtime(ux_runtime)
    app.state.object_viewer = None

    backend_sdk = BackendClient(app.state._state)
    app.state.backend_sdk = backend_sdk

    schema_engine = UISchemaEngine()
    app.state.schema_engine = schema_engine

    form_engine = FormEngine()
    app.state.form_engine = form_engine

    action_registry = ActionRegistry()
    app.state.action_registry = action_registry

    init_hooks()

    plugin_sandbox = PluginSandbox()
    register_hook_points()
    app.state.plugin_sandbox = plugin_sandbox

    from app.routers.notifications import _ws_manager
    heartbeat_task = asyncio.create_task(_ws_manager.heartbeat_loop(interval=30.0))
    cleanup_task = asyncio.create_task(_ws_manager.cleanup_task(interval=30.0))

    return [heartbeat_task, cleanup_task]


async def shutdown_services(app: FastAPI) -> None:
    kg = getattr(app.state, "kg_engine", None)
    if kg is not None:
        await kg.close()
    cache = getattr(app.state, "cache", None)
    if cache is not None:
        await cache.close()
    await close_db()
