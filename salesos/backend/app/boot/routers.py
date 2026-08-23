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
    from app.routers.approval import router as approval_router
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
    # EAB-001-P0-DUP-01 / Decision API SoT:
    # Canonical governed decisions = Decision Center (`/api/v1/decisions*`).
    # Decision Platform keeps `/api/v1/decision/*` (alternate capability).
    # Decision Runtime remounted under `/api/v1/decision-runtime` (below) — do not
    # remount Runtime at `/api/v1` (collided with Platform evaluate + Center decisions).
    # See docs/audit/ga-engineering-audit/enterprise-audit-board/history/
    # EAB-2026-08-06-001/DECISION-API-SOT.md
    app.include_router(
        decision_platform_router,
        prefix="",
        tags=["Decision Platform (alternate)"],
        dependencies=_auth,
    )
    # A.1: revenue_execution opportunity CRUD remounted to
    # `/api/v1/revenue-execution/opportunities*` (see that router). Canonical
    # `/api/v1/opportunities` = commercial.py (FE query-param + GET-by-id).
    # opportunities.py keeps JSON PUT / PATCH stage / close-won|lost only.
    app.include_router(
        revenue_execution_router, prefix="", tags=["Revenue Execution"], dependencies=_auth
    )

    from domains.decision_center.router import router as decision_center_router

    app.include_router(
        decision_center_router,
        prefix="/api/v1",
        tags=["Decision Center (SoT)"],
        dependencies=_auth,
    )
    app.include_router(
        company_router, prefix="/api/v1/companies", tags=["Companies"], dependencies=_auth
    )
    app.include_router(
        contact_router, prefix="/api/v1/contacts", tags=["Contacts"], dependencies=_auth
    )
    from app.routers.opportunity_contacts import router as opportunity_contacts_router
    app.include_router(
        opportunity_contacts_router, prefix="/api/v1", tags=["Opportunity Contacts"], dependencies=_auth
    )
    from app.routers.attribution import router as attribution_router
    app.include_router(
        attribution_router, prefix="/api/v1", tags=["Attribution (Shadow)"], dependencies=_auth
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
    # Deprecated HTTP prefix: was `/api/v1` (collided with Center + Platform).
    # New SoT prefix: `/api/v1/decision-runtime` (engine code retained; not deleted).
    app.include_router(
        decision_router,
        prefix="/api/v1/decision-runtime",
        tags=["Decision Runtime (remounted; deprecated /api/v1 aliases)"],
        dependencies=_auth,
    )
    app.include_router(graph_router, prefix="/api/v1", tags=["Knowledge Graph"], dependencies=_auth)
    app.include_router(timeline_router, prefix="/api/v1", tags=["Timeline"], dependencies=_auth)
    # EAB-001-P1-DUP-02: runtime search is primary; app.routers.search is experimental.
    app.include_router(search_router, prefix="/api/v1", tags=["Search"], dependencies=_auth)
    from app.routers.search import router as search_api_router

    app.include_router(
        search_api_router,
        prefix="/api/v1",
        tags=["Search (experimental)"],
        dependencies=_auth,
    )
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

    # DOM-024 / CAP-071/072 — STORY-13-01 MarketplaceListing (OBJ-325).
    from app.modules.marketplace_listings.router import (
        router as marketplace_listings_router,
    )
    from domains.marketplace.router import router as marketplace_router

    app.include_router(
        marketplace_listings_router,
        prefix="/api/v1",
        tags=["Marketplace Listings"],
        dependencies=_auth,
    )
    app.include_router(marketplace_router)

    # EPIC-14 / STORY-14-01 — Load/SLO harness companion (50-tenant pooled tier).
    from app.modules.load_slo.router import router as load_slo_router

    app.include_router(
        load_slo_router,
        prefix="/api/v1",
        tags=["Load SLO"],
        dependencies=_auth,
    )

    # EPIC-14 / STORY-14-02 — Chaos resilience fault-injection harness (CI).
    from app.modules.chaos_resilience.router import router as chaos_resilience_router

    app.include_router(
        chaos_resilience_router,
        prefix="/api/v1",
        tags=["Chaos Resilience"],
        dependencies=_auth,
    )
    # EPIC-14 / STORY-14-06 — AI provider failover harness (non-prod; builds on 14-02).
    from app.modules.chaos_resilience.ai_failover_router import (
        router as ai_failover_router,
    )

    app.include_router(
        ai_failover_router,
        prefix="/api/v1",
        tags=["Chaos Resilience"],
        dependencies=_auth,
    )
    # EPIC-14 / STORY-14-07 — LLM regression suite (non-prod golden fixtures).
    from app.modules.chaos_resilience.llm_regression_router import (
        router as llm_regression_router,
    )

    app.include_router(
        llm_regression_router,
        prefix="/api/v1",
        tags=["Chaos Resilience"],
        dependencies=_auth,
    )

    # EPIC-14 / STORY-14-03 — DR drill harness (backup/restore, RTO/RPO).
    from app.modules.dr_drill.router import router as dr_drill_router

    app.include_router(
        dr_drill_router,
        prefix="/api/v1",
        tags=["DR Drill"],
        dependencies=_auth,
    )

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
    # DOM-022 / CAP-087 — STORY-10-05 Territory Rules Studio (geography/industry/size).
    from app.modules.tenant_studio.territories_router import (
        router as territories_studio_router,
    )

    app.include_router(
        territories_studio_router,
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
    # DOM-022 / CAP-092 — STORY-10-07 Branding & Languages Studio.
    from app.modules.tenant_studio.branding_router import (
        router as branding_studio_router,
    )

    app.include_router(
        branding_studio_router,
        prefix="/api/v1",
        tags=["Tenant Studio"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-095 — STORY-11-01 ICP Engine (versioned ICPProfile).
    from app.modules.gtm.icp_router import (
        router as icp_router,
    )

    app.include_router(
        icp_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-096 — STORY-11-02 TAM/SAM/SOM Market Sizing.
    from app.modules.gtm.market_sizing_router import (
        router as market_sizing_router,
    )

    app.include_router(
        market_sizing_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-097 — STORY-11-03 Lead Discovery (gov-first + Hub fallback).
    from app.modules.gtm.lead_discovery_router import (
        router as lead_discovery_router,
    )

    app.include_router(
        lead_discovery_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-099 — STORY-11-05 Enrichment Waterfall (≥2 providers).
    from app.modules.gtm.enrichment_router import (
        router as enrichment_router,
    )

    app.include_router(
        enrichment_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-100 — STORY-11-06 Contact Verification (swap-in connector).
    from app.modules.gtm.verification_router import (
        router as gtm_verification_router,
    )

    app.include_router(
        gtm_verification_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-098 — STORY-11-04 Lookalike Accounts.
    from app.modules.gtm.lookalike_router import (
        router as lookalike_router,
    )

    app.include_router(
        lookalike_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-101 — STORY-11-07 Website Intelligence (fixture + prompt registry).
    from app.modules.gtm.website_intelligence_router import (
        router as website_intelligence_router,
    )

    app.include_router(
        website_intelligence_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-103 — STORY-11-08 AI Outreach (Prompt Registry path; draft_only).
    from app.modules.gtm.outreach_router import (
        router as outreach_router,
    )

    app.include_router(
        outreach_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # DOM-023 / CAP-104 — STORY-11-09 Sequencing Engine (email channel).
    from app.modules.gtm.sequencing_router import (
        router as sequencing_router,
    )

    app.include_router(
        sequencing_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    # Phase 4C — ICP profile admin CRUD (Postgres persistence, canonical RLS).
    from app.modules.gtm.icp_admin_router import (
        router as icp_admin_router,
    )

    app.include_router(
        icp_admin_router,
        prefix="/api/v1",
        tags=["GTM Intelligence"],
        dependencies=_auth,
    )
    app.include_router(audit_router, prefix="/api/v1", tags=["Audit"], dependencies=_auth)
    app.include_router(api_keys_router, prefix="/api/v1", tags=["API Keys"], dependencies=_auth)
    app.include_router(admin_router)
    app.include_router(monitoring_router, tags=["Monitoring"])
    app.include_router(cache_router, tags=["Cache"], dependencies=_auth)
    app.include_router(copilot_router, prefix="/api/v1", tags=["Copilot"], dependencies=_auth)
    app.include_router(approval_router, prefix="/api/v1", tags=["Approval"], dependencies=_auth)
    # STORY-12-04 — Per-plan AI model tier (Plan.entitlements; copilot flag unchanged).
    from app.modules.admin.ai_model_tiers_router import (
        router as ai_model_tiers_router,
    )

    app.include_router(
        ai_model_tiers_router,
        prefix="/api/v1",
        tags=["AI Model Tiers"],
        dependencies=_auth,
    )
    # DOM-022 / CAP-089 — STORY-12-01 Prompt Library (extends CAP-023; no live LLM).
    from app.modules.tenant_studio.prompt_library_router import (
        router as prompt_library_router,
    )

    app.include_router(
        prompt_library_router,
        prefix="/api/v1",
        tags=["AI Studio"],
        dependencies=_auth,
    )
    # DOM-022 / CAP-091 — STORY-12-02 AI Policies (reuses AI-GR-*; no live LLM).
    from app.modules.tenant_studio.ai_policies_router import (
        router as ai_policies_router,
    )

    app.include_router(
        ai_policies_router,
        prefix="/api/v1",
        tags=["AI Studio"],
        dependencies=_auth,
    )
    # DOM-012 / CAP-063 — STORY-12-03 AI Memory MVP (conversation-level; opt-in).
    from app.modules.tenant_studio.ai_memory_router import (
        router as ai_memory_router,
    )

    app.include_router(
        ai_memory_router,
        prefix="/api/v1",
        tags=["AI Studio"],
        dependencies=_auth,
    )
    app.include_router(commercial_router, prefix="/api/v1", tags=["Commercial"], dependencies=_auth)

    app.include_router(demo_router, tags=["Demo"])
    app.include_router(admin_demo_router, tags=["Admin"], dependencies=_auth)

    from app.routers.workflows import router as workflow_router

    # EAB-001-P1-DUP-02: workflow webhook CRUD lives at `/api/v1/workflow/webhooks*`
    # (not `/api/v1/webhooks*`) so Integration Hub owns `/api/v1/webhooks/*`.
    app.include_router(
        workflow_router, prefix="/api/v1", tags=["Workflow Engine"], dependencies=_auth
    )

    from app.modules.rules_engine.router import router as rules_engine_router

    app.include_router(rules_engine_router, tags=["Rules Engine"], dependencies=_auth)

    from app.routers.meetings import router as meetings_router
    from app.routers.revenue import router as revenue_router
    from runtime.nba_engine.api.router import router as nba_router
    from runtime.pipeline_analytics.router import router as pipeline_analytics_router

    # B.1: commercial.py owns all `/api/v1/opportunities*` (list/create/get/mutate).
    app.include_router(
        meetings_router, prefix="/api/v1", tags=["Meeting Intelligence"], dependencies=_auth
    )
    app.include_router(revenue_router, prefix="/api/v1", tags=["Revenue"], dependencies=_auth)
    app.include_router(nba_router, prefix="/api/v1", tags=["NBA Engine"], dependencies=_auth)
    app.include_router(
        pipeline_analytics_router, prefix="/api/v1", tags=["Pipeline Analytics"], dependencies=_auth
    )

    # P1-6: Mount revenue planning router (forecast/quota/territory) — was dead code
    from domains.revenue.router import router as revenue_planning_router

    app.include_router(
        revenue_planning_router,
        prefix="/api/v1/revenue-planning",
        tags=["Revenue Planning"],
        dependencies=_auth,
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

    # Integration Hub subscriptions SoT: `/api/v1/webhooks/subscriptions*` (not workflow).
    app.include_router(webhooks_router)

    from app.routers.enrichment import router as enrichment_router

    app.include_router(enrichment_router, prefix="/api/v1", tags=["Enrichment"], dependencies=_auth)

    from app.routers.mcp import router as mcp_router

    app.include_router(mcp_router, dependencies=_auth)

    from app.routers.source_of_truth import router as source_of_truth_router

    app.include_router(source_of_truth_router)

    from app.graphql.schema import graphql_router

    app.include_router(graphql_router, prefix="/graphql", dependencies=_auth)
