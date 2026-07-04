import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.middleware import RequestIDMiddleware, TimingMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.config import settings
from sdk.events.base import DomainEvent
from sdk.events.store import PostgresEventStore
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
    from sdk.events.domain_events import (
        BranchCreated, CompanyCreated, CompanyEnriched, CompanyIngested,
        CompanyMerged, CompanyUpdated, ContactCreated, ContactUpdated,
        GoldenRecordCreated, GoldenRecordUpdated,
        EntityResolutionCompleted, EntityResolutionMatchFound,
        LicenseCreated, LicenseUpdated,
        TenantCreated, UserLoggedIn, UserPasswordChanged, UserRegistered, UserRoleChanged,
    )

    if os.environ.get("SALESOS_TESTING"):
        yield
    else:
        await init_db()
        register_modules()
        setup_telemetry("salesos")

        if settings.sentry_dsn:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.env,
                traces_sample_rate=0.1,
            )
            if app.state.logger:
                app.state.logger.info("Sentry initialized: dsn=%s env=%s", settings.sentry_dsn[:20] + "...", settings.env)

        app.state.logger = StructuredLogger("salesos.api")

        # ── Event Runtime (replaces InMemoryEventBus) ──
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

        # ── Data Fabric Runtime ──
        data_fabric = DataFabricPipeline(
            session_factory=async_session,
            event_runtime=event_runtime,
            logger=app.state.logger,
        )
        app.state.data_fabric = data_fabric

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

        # ── Knowledge Graph Runtime ──
        kg_engine = KnowledgeGraphEngine(
            session_factory=async_session,
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", "salesos_secret"),
            logger=app.state.logger,
        )
        app.state.kg_engine = kg_engine

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
        await close_db()


app = FastAPI(
    title="SalesOS API",
    description="Enterprise Company Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, rate=60, window=60)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/health")
async def health():
    from app.common.schemas import HealthResponse

    return HealthResponse(
        status="ok",
        version="0.1.0",
        database="connected",
        cache="connected",
        kafka="not_configured",
    )


@app.get("/")
async def root():
    return {
        "name": "SalesOS API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


def register_routers():
    from app.modules.company.router import router as company_router
    from app.modules.contact.router import router as contact_router
    from app.modules.entity_resolution.router import router as entity_resolution_router
    from app.modules.identity.router import router as identity_router
    from app.modules.notion_sync.router import router as notion_sync_router
    from app.modules.excel_import.router import router as excel_import_router
    from app.modules.employee_360.router import router as employee_360_router
    from app.modules.executive.router import router as executive_router
    from app.modules.work_intelligence.router import router as work_intelligence_router
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

    app.include_router(notion_sync_router, prefix="/api/v1", tags=["Notion Sync"])
    app.include_router(excel_import_router, prefix="/api/v1", tags=["Excel Import"])
    app.include_router(employee_360_router, prefix="/api/v1", tags=["Employee 360"])
    app.include_router(executive_router, prefix="/api/v1", tags=["Executive"])
    app.include_router(work_intelligence_router, prefix="/api/v1", tags=["Work Intelligence"])
    app.include_router(identity_router, prefix="/api/v1/identity", tags=["Identity"])
    app.include_router(company_router, prefix="/api/v1/companies", tags=["Companies"])
    app.include_router(contact_router, prefix="/api/v1/contacts", tags=["Contacts"])
    app.include_router(activity_router, prefix="/api/v1", tags=["Activity"])
    app.include_router(entity_resolution_router, prefix="/api/v1/entity-resolution", tags=["Entity Resolution"])
    app.include_router(event_runtime_router, prefix="/api/v1", tags=["Event Runtime"])
    app.include_router(data_fabric_router, prefix="/api/v1", tags=["Data Fabric"])
    app.include_router(feature_store_router, prefix="/api/v1", tags=["Feature Store"])
    app.include_router(decision_router, prefix="/api/v1", tags=["Decision Engine"])
    app.include_router(graph_router, prefix="/api/v1", tags=["Knowledge Graph"])
    app.include_router(timeline_router, prefix="/api/v1", tags=["Timeline"])
    app.include_router(search_router, prefix="/api/v1", tags=["Search"])
    app.include_router(capability_router, prefix="/api/v1", tags=["Capability Framework"])
    app.include_router(ux_router, prefix="/api/v1", tags=["Experience Layer"])

    # XP1 — Schema-Driven UI
    from runtime.ui_schema_engine.router import router as schema_router
    from runtime.form_engine.router import router as form_router
    from runtime.action_engine.router import router as action_router
    from runtime.extension_api.router import router as extension_router
    from runtime.plugin_sandbox.router import router as plugin_router
    app.include_router(schema_router, prefix="/api/v1", tags=["UI Schema"])
    app.include_router(form_router, prefix="/api/v1", tags=["Form Engine"])
    app.include_router(action_router, prefix="/api/v1", tags=["Action Engine"])
    app.include_router(extension_router, prefix="/api/v1", tags=["Extension API"])
    app.include_router(plugin_router, prefix="/api/v1", tags=["Plugin Sandbox"])

    app.include_router(copilot_router, prefix="/api/v1", tags=["Copilot"])
    app.include_router(commercial_router, prefix="/api/v1", tags=["Commercial"])


register_routers()
