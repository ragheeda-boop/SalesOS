"""Feature module and capability registrations.

Called on application startup to register every module's features,
capabilities, permissions, and metadata in the global registries.
"""

from sdk.capability_registry import (
    AIDeclaration,
    Capability,
    CapabilityRegistry,
    CapabilityType,
    EventDeclaration,
    ExecutorDeclaration,
    ExecutionStrategy,
    MetricDeclaration,
)
from sdk.feature_registry import FeatureModule, FeatureRegistry, ModuleStatus
from sdk.permissions import PermissionAction, PermissionRegistry


def register_modules() -> None:
    _register_identity()
    _register_company()
    _register_entity_resolution()
    _register_timeline()
    _register_opportunity()
    _register_search()
    _register_permissions()
    _register_platform_capabilities()


# ─────────────────────────────────────────────
# Feature Modules (existing — platform metadata)
# ─────────────────────────────────────────────


def _register_identity() -> None:
    FeatureRegistry.register(FeatureModule(
        name="identity",
        label="Identity & Access",
        label_ar="الهوية والوصول",
        description="Tenant management, user authentication, role-based access control",
        description_ar="إدارة المستأجرين، المصادقة، التحكم في الوصول",
        version="1.0.0",
        status=ModuleStatus.IN_PROGRESS,
        entities=["Tenant", "User", "Role"],
        permissions=["tenant.*", "user.*"],
        events=["tenant.created", "user.registered", "user.logged_in", "user.role_changed"],
        api_prefix="/api/v1",
        sprint=1,
        owner="platform",
        tags=["identity", "auth", "rbac"],
    ))


def _register_company() -> None:
    FeatureRegistry.register(FeatureModule(
        name="company",
        label="Company Intelligence",
        label_ar="ذكاء الشركات",
        description="Company profiles, branches, licenses, contacts, entity resolution",
        description_ar="ملفات الشركات، الفروع، التراخيص، جهات الاتصال",
        version="1.0.0",
        status=ModuleStatus.IN_PROGRESS,
        entities=["Company", "Branch", "License", "Contact", "GoldenRecord"],
        permissions=["company.*", "branch.*", "license.*", "contact.*"],
        events=["company.created", "company.merged", "company.enriched",
                "entity_resolution.match_found", "golden_record.created"],
        api_prefix="/api/v1",
        sprint=1,
        owner="platform",
        tags=["company", "crm", "data"],
    ))


def _register_timeline() -> None:
    FeatureRegistry.register(FeatureModule(
        name="timeline",
        label="Timeline & Activity",
        label_ar="الجدول الزمني والنشاط",
        description="Activity logging, timeline aggregation, event history",
        description_ar="تسجيل النشاطات، تجميع الجدول الزمني",
        version="1.0.0",
        status=ModuleStatus.PLANNED,
        entities=["Activity", "Timeline"],
        permissions=["activity.*", "timeline.*"],
        events=["activity.logged", "timeline.updated"],
        api_prefix="/api/v1",
        sprint=4,
        owner="platform",
        tags=["activity", "timeline"],
    ))


def _register_opportunity() -> None:
    FeatureRegistry.register(FeatureModule(
        name="opportunity",
        label="Pipeline & Opportunities",
        label_ar="خطة المبيعات والفرص",
        description="Sales pipeline management, opportunity tracking, stage automation",
        description_ar="إدارة خط المبيعات، تتبع الفرص",
        version="1.0.0",
        status=ModuleStatus.PLANNED,
        entities=["Opportunity", "Pipeline", "Stage"],
        permissions=["opportunity.*", "pipeline.*"],
        events=["opportunity.created", "opportunity.stage_changed",
                "opportunity.won", "opportunity.lost"],
        api_prefix="/api/v1",
        sprint=5,
        owner="crm",
        tags=["crm", "pipeline", "sales"],
    ))


def _register_search() -> None:
    FeatureRegistry.register(FeatureModule(
        name="search",
        label="Search & Discovery",
        label_ar="البحث والاكتشاف",
        description="Full-text search, vector search, advanced filtering, saved searches",
        description_ar="البحث النصي، البحث المتجه، التصفية المتقدمة",
        version="1.0.0",
        status=ModuleStatus.COMPLETED,
        entities=["SearchIndex", "SavedSearch", "SearchHistory"],
        permissions=["search.*"],
        events=[],
        api_prefix="/api/v1",
        sprint=3,
        owner="platform",
        tags=["search", "discovery"],
    ))


def _register_entity_resolution() -> None:
    FeatureRegistry.register(FeatureModule(
        name="entity_resolution",
        label="Entity Resolution",
        label_ar="حل الكيانات",
        description="Golden record management, identity matching, field-level conflict resolution",
        description_ar="إدارة السجلات الذهبية، مطابقة الكيانات، حل تعارضات الحقول",
        version="1.0.0",
        status=ModuleStatus.IN_PROGRESS,
        entities=["GoldenRecord", "EntityResolutionConflict", "EntityResolutionLog"],
        permissions=["golden_record.*", "entity_resolution.*"],
        events=["golden_record.created", "golden_record.updated",
                "entity_resolution.match_found", "entity_resolution.completed"],
        api_prefix="/api/v1/entity-resolution",
        sprint=2,
        owner="platform",
        tags=["entity-resolution", "data-fabric", "golden-record"],
    ))


def _register_permissions() -> None:
    for role_name, perms in PermissionRegistry.default_roles().items():
        from sdk.permissions import Role
        role = Role(name=role_name)
        role.permissions.update(perms)
        PermissionRegistry.register_role(role)


# ─────────────────────────────────────────────
# Capability Registry (runtime — for SearchPlanner, AI Agents, etc.)
# ─────────────────────────────────────────────


def _register_platform_capabilities() -> None:
    # ── Company Domain ──
    CapabilityRegistry.register(Capability(
        name="company",
        label="Company Intelligence",
        label_ar="ذكاء الشركات",
        description="Company profiles and search",
        type=CapabilityType.DOMAIN,
        executors=[
            ExecutorDeclaration(
                name="CompanySearchRepository",
                strategy=ExecutionStrategy.POSTGRES_BTREE,
                supports=["exact", "filters", "sort", "pagination"],
                frozen=True,
                verified_p95="<1ms (100K)",
            ),
            ExecutorDeclaration(
                name="CompanyTrigramRepository",
                strategy=ExecutionStrategy.POSTGRES_TRIGRAM,
                supports=["partial", "fuzzy"],
                frozen=True,
                verified_p95="78ms (100K)",
            ),
        ],
        events=EventDeclaration(
            produces=["company.created", "company.updated", "company.ingested",
                      "branch.created", "license.created", "contact.created"],
        ),
        metrics=MetricDeclaration(
            counters=["company_created_total", "company_search_total", "search_zero_results_total"],
            histograms=["company_search_duration_seconds"],
        ),
        permissions=["company.*", "branch.*", "license.*", "contact.*"],
        frozen_interfaces=["SearchQuery", "SearchResult", "SearchPlanner"],
    ))

    # ── Search Capability ──
    CapabilityRegistry.register(Capability(
        name="search",
        label="Search & Discovery",
        label_ar="البحث والاكتشاف",
        description="Multi-executor search engine with strategy matrix",
        type=CapabilityType.SEARCH,
        executors=[
            ExecutorDeclaration(
                name="SearchPlanner",
                strategy=ExecutionStrategy.HYBRID,
                supports=["exact", "partial", "filter", "sort", "pagination", "semantic"],
                frozen=True,
            ),
        ],
        ai=AIDeclaration(
            semantic_search=True,
            similar_companies=True,
        ),
        frozen_interfaces=["SearchQuery", "SearchResult", "SearchPlanner"],
    ))

    # ── Timeline Capability ──
    CapabilityRegistry.register(Capability(
        name="timeline",
        label="Timeline & Activity",
        label_ar="الجدول الزمني والنشاط",
        description="Immutable activity logging with Actor→Activity→Target→Outcome",
        type=CapabilityType.TIMELINE,
        events=EventDeclaration(
            produces=["activity.logged", "timeline.event_appended"],
        ),
        # Timeline will get its executors when built
        executors=[],
    ))

    # ── Contract Domain ──
    CapabilityRegistry.register(Capability(
        name="contract",
        label="Contract Management",
        label_ar="إدارة العقود",
        description="System of Legal Truth — references Quote, never duplicates pricing",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["contract.created", "contract.signed", "contract.activated",
                      "contract.completed", "contract.terminated", "contract.expired", "contract.renewed"],
        ),
        permissions=["contract.*"],
    ))

    # ── Proposal Domain ──
    CapabilityRegistry.register(Capability(
        name="proposal",
        label="Proposal Management",
        label_ar="إدارة العروض",
        description="Communication layer — references Quote revisions, never duplicates pricing",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["proposal.generated", "proposal.approved", "proposal.delivered",
                      "proposal.viewed", "proposal.accepted", "proposal.rejected", "proposal.expired"],
        ),
        permissions=["proposal.*"],
    ))

    # ── Quote Domain ──
    CapabilityRegistry.register(Capability(
        name="quote",
        label="Quote Management",
        label_ar="إدارة عروض الأسعار",
        description="Commercial agreement drafts with approval, revision control, and revenue KPIs",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["quote.created", "quote.revised", "quote.submitted", "quote.approved",
                      "quote.sent", "quote.accepted", "quote.rejected", "quote.expired"],
        ),
        permissions=["quote.*"],
    ))

    # ── Activity Domain ──
    CapabilityRegistry.register(Capability(
        name="activity",
        label="Activity Management",
        label_ar="إدارة النشاطات",
        description="Activity sessions, outcomes, rule engine for pipeline progression",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["activity.session_created", "activity.completed", "activity.rule_triggered"],
        ),
        permissions=["activity.*"],
    ))

    # ── Pipeline Domain ──
    CapabilityRegistry.register(Capability(
        name="pipeline",
        label="Pipeline Management",
        label_ar="إدارة خط المبيعات",
        description="Pipeline definition, stage progression, SLAs, KPIs",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["pipeline.created", "stage.entered", "stage.exited",
                      "stage.overdue", "pipeline.completed", "pipeline.reopened"],
        ),
        permissions=["pipeline.*"],
    ))

    # ── Opportunity Domain ──
    CapabilityRegistry.register(Capability(
        name="opportunity",
        label="Opportunity Management",
        label_ar="إدارة الفرص",
        description="Sales pipeline, stage progression, won/lost tracking",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["opportunity.created", "opportunity.stage_changed", "opportunity.won", "opportunity.lost"],
        ),
        permissions=["opportunity.*"],
    ))

    # ── Email Domain ──
    CapabilityRegistry.register(Capability(
        name="email",
        label="Email Intelligence",
        label_ar="ذكاء البريد الإلكتروني",
        description="Email communication analysis, tracking, and intelligence",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["email.received", "email.sent", "email.tracked", "email.analyzed"],
        ),
        permissions=["email.*"],
    ))

    # ── Revenue Analytics Domain ──
    CapabilityRegistry.register(Capability(
        name="analytics",
        label="Revenue Analytics",
        label_ar="تحليلات الإيرادات",
        description="Measurement Layer — owns KPIs, never facts or decisions. Snapshot-based, explainable, drill-down to RTI",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(produces=["analytics.snapshot_generated"]),
    ))

    # ── Forecast Domain ──
    CapabilityRegistry.register(Capability(
        name="forecast",
        label="Revenue Forecasting",
        label_ar="التوقعات الإيرادية",
        description="Projection Engine — consumes commercial truths, owns predictions, never creates facts",
        type=CapabilityType.DOMAIN,
        ai=AIDeclaration(semantic_search=False),
        events=EventDeclaration(
            produces=["forecast.created", "forecast.finalized"],
        ),
        frozen_interfaces=[],
    ))

    # ── Decision Context Domain ──
    CapabilityRegistry.register(Capability(
        name="context",
        label="Decision Context",
        label_ar="سياق القرارات",
        description="Aggregates facts, knowledge, measurements, policies into contextual snapshots for recommendations",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(produces=["decision.context_built"]),
    ))
    CapabilityRegistry.register(Capability(
        name="recommendation",
        label="Recommendation Engine",
        label_ar="محرك التوصيات",
        description="Consumes Decision Context, produces explainable, contextual, optional recommendations",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(produces=["recommendation.generated"]),
    ))

    # ── Entity Resolution ──
    CapabilityRegistry.register(Capability(
        name="entity_resolution",
        label="Entity Resolution",
        label_ar="حل الكيانات",
        description="Golden record management with provenance, identity matching by CR number, field-level conflict detection",
        type=CapabilityType.DOMAIN,
        executors=[],
        events=EventDeclaration(
            produces=["golden_record.created", "golden_record.updated",
                      "entity_resolution.match_found", "entity_resolution.completed"],
        ),
        metrics=MetricDeclaration(
            counters=["golden_records_created_total", "entity_resolution_conflicts_total"],
        ),
        permissions=["golden_record.*", "entity_resolution.*"],
    ))

    # ── Infrastructure ──
    CapabilityRegistry.register(Capability(
        name="infrastructure",
        label="Infrastructure",
        label_ar="البنية التحتية",
        description="Company infrastructure data (capital, address, branches, licenses)",
        type=CapabilityType.DOMAIN,
        executors=[],
        events=EventDeclaration(produces=[]),
        metrics=MetricDeclaration(counters=[], histograms=[]),
        permissions=["infrastructure.*"],
    ))

    # ── Meeting Domain ──
    CapabilityRegistry.register(Capability(
        name="meeting",
        label="Meeting Intelligence",
        label_ar="ذكاء الاجتماعات",
        description="Meeting scheduling, notes, action items, and outcome tracking",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["meeting.scheduled", "meeting.completed", "meeting.action_item_created"],
        ),
        permissions=["meeting.*"],
    ))

    # ── Playbook Domain ──
    CapabilityRegistry.register(Capability(
        name="playbook",
        label="Sales Playbook",
        label_ar="دليل المبيعات",
        description="Reusable sales playbooks, best practices, and playbook-driven workflows",
        type=CapabilityType.DOMAIN,
        events=EventDeclaration(
            produces=["playbook.activated", "playbook.completed"],
        ),
        permissions=["playbook.*"],
    ))

    # ── AI Copilot (future) ──
    CapabilityRegistry.register(Capability(
        name="ai_copilot",
        label="AI Copilot",
        label_ar="المساعد الذكي",
        description="AI-powered assistant for natural language queries and analysis",
        type=CapabilityType.AI,
        ai=AIDeclaration(
            semantic_search=True,
            similar_companies=True,
            copilot=True,
            rag=True,
        ),
        executors=[
            ExecutorDeclaration(
                name="PgVectorCompanyRepository",
                strategy=ExecutionStrategy.PGVECTOR_HNSW,
                supports=["semantic", "similarity"],
                verified_p95="TBD",
            ),
        ],
    ))
