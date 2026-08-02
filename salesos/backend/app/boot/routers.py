from fastapi import Depends, FastAPI

from app.dependencies import verify_token


def register_routers(app: FastAPI) -> None:
    _auth = [Depends(verify_token)]

    from app.routers.metrics import router as metrics_router

    app.include_router(metrics_router, tags=["Metrics"])

    # GA-P2-05: Two distinct admin routers serve different concerns.
    # runtime.admin_router = Operational admin (metrics, health/full, DLQ management)
    # app.modules.admin.router = Platform admin (tenants, users, plans, billing, feature flags, roles, audit log, etc.)  # noqa: E501
    from runtime.admin_router import router as runtime_admin_router

    app.include_router(runtime_admin_router, tags=["Admin"])

    from app.application.dashboard.router import router as dashboard_router
    from app.modules.admin.router import router as admin_router
    from app.modules.api_keys.router import router as api_keys_router
    from app.modules.audit.router import router as audit_router
    from app.modules.cache.router import router as cache_router
    from app.modules.communication_hub.router import router as communication_hub_router
    from app.modules.company.router import router as company_router
    from app.modules.contact.router import router as contact_router
    from app.modules.decision.router import router as decision_platform_router
    from app.modules.employee_360.router import router as employee_360_router
    from app.modules.entity_resolution.router import router as entity_resolution_router
    from app.modules.excel_import.router import router as excel_import_router
    from app.modules.executive.router import router as executive_router
    from app.modules.identity.router import router as identity_router
    from app.modules.integration_hub.router import router as integration_hub_router
    from app.modules.monitoring.router import router as monitoring_router
    from app.modules.notion_sync.router import router as notion_sync_router
    from app.modules.revenue_execution.router import router as revenue_execution_router
    from app.modules.signal_marketplace.router import router as signal_marketplace_router
    from app.modules.sso.router import router as sso_router
    from app.modules.work_intelligence.router import router as work_intelligence_router
    from app.routers.admin_demo import router as admin_demo_router
    from app.routers.commercial import router as commercial_router
    from app.routers.copilot import router as copilot_router
    from app.routers.demo import router as demo_router
    from domains.employee.router import router as employee_domain_router
    from domains.feature_store.router import router as feature_store_domain_router
    from runtime.activity_runtime.router import router as activity_router
    from runtime.capability_framework.router import router as capability_router
    from runtime.data_fabric_runtime.router import router as data_fabric_router
    from runtime.decision_runtime.router import router as decision_router
    from runtime.event_runtime.router import router as event_runtime_router
    from runtime.feature_store.router import router as feature_store_router
    from runtime.knowledge_graph_runtime.router import router as graph_router
    from runtime.search_runtime.router import router as search_router
    from runtime.timeline_runtime.router import router as timeline_router
    from runtime.ux_runtime.router import router as ux_router

    app.include_router(identity_router, prefix="/api/v1/identity", tags=["Identity"])
    app.include_router(
        notion_sync_router, prefix="/api/v1", tags=["Notion Sync"], dependencies=_auth
    )
    app.include_router(
        excel_import_router, prefix="/api/v1", tags=["Excel Import"], dependencies=_auth
    )
    app.include_router(
        employee_360_router, prefix="/api/v1", tags=["Employee 360"], dependencies=_auth
    )
    app.include_router(
        employee_domain_router, prefix="/api/v1", tags=["Employee Domain"], dependencies=_auth
    )

    from domains.employee.intelligence_router import router as employee_intelligence_router

    app.include_router(
        employee_intelligence_router,
        prefix="/api/v1",
        tags=["Employee Intelligence"],
        dependencies=_auth,
    )
    # Same router remounted without schema for infra health probes (not a second module).
    app.include_router(
        employee_intelligence_router, prefix="", tags=["Employee Health"], include_in_schema=False
    )

    from domains.employee.webhook_handler import router as employee_webhook_router

    app.include_router(employee_webhook_router, prefix="/api/v1", tags=["Employee Webhooks"])

    # STORY-05-02 — public Stripe webhook (signature-verified; no JWT/CSRF cookie).
    from app.modules.billing.stripe_router import webhook_router as stripe_webhook_router

    app.include_router(stripe_webhook_router, prefix="/api/v1", tags=["Billing - Stripe Webhooks"])

    app.include_router(executive_router, prefix="/api/v1", tags=["Executive"], dependencies=_auth)
    app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"], dependencies=_auth)
    app.include_router(
        work_intelligence_router, prefix="/api/v1", tags=["Work Intelligence"], dependencies=_auth
    )
    app.include_router(
        decision_platform_router, prefix="", tags=["Decision Platform"], dependencies=_auth
    )
    app.include_router(
        revenue_execution_router, prefix="", tags=["Revenue Execution"], dependencies=_auth
    )

    from domains.decision_center.router import router as decision_center_router

    app.include_router(
        decision_center_router, prefix="/api/v1", tags=["Decision Center"], dependencies=_auth
    )
    app.include_router(
        company_router, prefix="/api/v1/companies", tags=["Companies"], dependencies=_auth
    )
    app.include_router(
        contact_router, prefix="/api/v1/contacts", tags=["Contacts"], dependencies=_auth
    )
    app.include_router(activity_router, prefix="/api/v1", tags=["Activity"], dependencies=_auth)

    from intelligence.activity_intelligence.api.router import router as activity_intelligence_router

    app.include_router(
        activity_intelligence_router, tags=["Activity Intelligence"], dependencies=_auth
    )
    app.include_router(
        entity_resolution_router,
        prefix="/api/v1/entity-resolution",
        tags=["Entity Resolution"],
        dependencies=_auth,
    )
    app.include_router(signal_marketplace_router, tags=["Signal Marketplace"], dependencies=_auth)
    app.include_router(
        event_runtime_router, prefix="/api/v1", tags=["Event Runtime"], dependencies=_auth
    )
    app.include_router(
        data_fabric_router, prefix="/api/v1", tags=["Data Fabric"], dependencies=_auth
    )
    app.include_router(
        feature_store_router, prefix="/api/v1", tags=["Feature Store"], dependencies=_auth
    )
    app.include_router(
        feature_store_domain_router,
        prefix="/api/v1",
        tags=["Feature Store Domain"],
        dependencies=_auth,
    )
    app.include_router(
        decision_router, prefix="/api/v1", tags=["Decision Engine"], dependencies=_auth
    )
    app.include_router(graph_router, prefix="/api/v1", tags=["Knowledge Graph"], dependencies=_auth)
    app.include_router(timeline_router, prefix="/api/v1", tags=["Timeline"], dependencies=_auth)
    app.include_router(search_router, prefix="/api/v1", tags=["Search"], dependencies=_auth)
    from app.routers.search import router as search_api_router

    app.include_router(search_api_router, prefix="/api/v1", tags=["Search"], dependencies=_auth)
    app.include_router(capability_router, dependencies=_auth)
    app.include_router(ux_router, dependencies=_auth)

    from runtime.action_engine.router import router as action_router
    from runtime.extension_api.router import router as extension_router
    from runtime.form_engine.router import router as form_router
    from runtime.plugin_sandbox.router import router as plugin_router
    from runtime.ui_schema_engine.router import router as schema_router

    app.include_router(schema_router, dependencies=_auth)
    app.include_router(form_router, dependencies=_auth)
    app.include_router(action_router, dependencies=_auth)
    app.include_router(extension_router, dependencies=_auth)
    app.include_router(plugin_router, dependencies=_auth)

    from domains.marketplace.router import router as marketplace_router

    app.include_router(marketplace_router)

    app.include_router(sso_router, prefix="/api/v1", tags=["SSO"])
    # Mount without router-level auth so Google OAuth /callback can complete
    # without a Bearer header. Protected routes declare Depends(verify_token).
    app.include_router(communication_hub_router, prefix="/api/v1", tags=["Communication Hub"])
    # DOM-021 Integration Hub (STORY-08-06) — Studio FE STORY-08-07 surfaces.
    app.include_router(
        integration_hub_router,
        prefix="/api/v1",
        tags=["Integration Hub"],
        dependencies=_auth,
    )
    # DOM-022 Tenant Studio — STORY-10-01 CAP-082 custom field definitions.
    from app.modules.tenant_studio.router import router as tenant_studio_router
    from app.modules.tenant_studio.scoring_rules_router import (
        router as scoring_rules_router,
    )
    from app.modules.tenant_studio.workflow_builder_router import (
        router as workflow_builder_router,
    )

    app.include_router(
        tenant_studio_router,
        prefix="/api/v1",
        tags=["Tenant Studio"],
        dependencies=_auth,
    )
    # DOM-022 / CAP-083 — STORY-10-03 Workflow Builder canvas → Workflow Engine.
    app.include_router(
        workflow_builder_router,
        prefix="/api/v1",
        tags=["Tenant Studio"],
        dependencies=_auth,
    )
    # DOM-022 / CAP-085 — STORY-10-04 Scoring Rules Studio (fail-safe evaluate).
    app.include_router(
        scoring_rules_router,
        prefix="/api/v1",
        tags=["Tenant Studio"],
        dependencies=_auth,
    )
    # DOM-022 / CAP-003 — STORY-10-06 Permissions Studio (entitlement ceiling).
    from app.modules.tenant_studio.permissions_router import (
        router as permissions_studio_router,
    )

    app.include_router(
        permissions_studio_router,
        prefix="/api/v1",
        tags=["Tenant Studio"],
        dependencies=_auth,
    )
    # DOM-022 / CAP-093 — STORY-10-08 Notification Rules Studio.
    from app.modules.tenant_studio.notification_rules_router import (
        router as notification_rules_router,
    )

    app.include_router(
        notification_rules_router,
        prefix="/api/v1",
        tags=["Tenant Studio"],
        dependencies=_auth,
    )
    app.include_router(audit_router, prefix="/api/v1", tags=["Audit"], dependencies=_auth)
    app.include_router(api_keys_router, prefix="/api/v1", tags=["API Keys"], dependencies=_auth)
    app.include_router(admin_router)
    app.include_router(monitoring_router, tags=["Monitoring"])
    app.include_router(cache_router, tags=["Cache"], dependencies=_auth)
    app.include_router(copilot_router, prefix="/api/v1", tags=["Copilot"], dependencies=_auth)
    app.include_router(commercial_router, prefix="/api/v1", tags=["Commercial"], dependencies=_auth)

    app.include_router(demo_router, tags=["Demo"])
    app.include_router(admin_demo_router, tags=["Admin"], dependencies=_auth)

    from app.routers.workflows import router as workflow_router

    app.include_router(
        workflow_router, prefix="/api/v1", tags=["Workflow Engine"], dependencies=_auth
    )

    from app.modules.rules_engine.router import router as rules_engine_router

    app.include_router(rules_engine_router, tags=["Rules Engine"], dependencies=_auth)

    from app.routers.meetings import router as meetings_router
    from app.routers.opportunities import router as opportunities_router
    from app.routers.revenue import router as revenue_router
    from runtime.nba_engine.api.router import router as nba_router
    from runtime.pipeline_analytics.router import router as pipeline_analytics_router

    app.include_router(
        opportunities_router, prefix="/api/v1", tags=["Opportunities"], dependencies=_auth
    )
    app.include_router(
        meetings_router, prefix="/api/v1", tags=["Meeting Intelligence"], dependencies=_auth
    )
    app.include_router(revenue_router, prefix="/api/v1", tags=["Revenue"], dependencies=_auth)
    app.include_router(nba_router, prefix="/api/v1", tags=["NBA Engine"], dependencies=_auth)
    app.include_router(
        pipeline_analytics_router, prefix="/api/v1", tags=["Pipeline Analytics"], dependencies=_auth
    )

    from app.routers.rag import router as rag_router

    app.include_router(rag_router, prefix="/api/v1", tags=["RAG"], dependencies=_auth)

    from app.routers.analytics import router as analytics_router

    app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"], dependencies=_auth)

    from app.routers.ai import router as ai_router

    app.include_router(ai_router, prefix="/api/v1", tags=["AI"], dependencies=_auth)

    from app.modules.telemetry.router import router as telemetry_router

    app.include_router(telemetry_router, tags=["Telemetry"], dependencies=_auth)

    from app.routers.notifications import router as notifications_router

    app.include_router(
        notifications_router, prefix="/api/v1", tags=["Notifications"], dependencies=_auth
    )

    from app.modules.webhooks.router import router as webhooks_router

    app.include_router(webhooks_router)

    from app.routers.enrichment import router as enrichment_router

    app.include_router(enrichment_router, prefix="/api/v1", tags=["Enrichment"], dependencies=_auth)

    from app.routers.mcp import router as mcp_router

    app.include_router(mcp_router, dependencies=_auth)

    from app.routers.source_of_truth import router as source_of_truth_router

    app.include_router(source_of_truth_router)

    from app.graphql.schema import graphql_router

    app.include_router(graphql_router, prefix="/graphql", dependencies=_auth)
