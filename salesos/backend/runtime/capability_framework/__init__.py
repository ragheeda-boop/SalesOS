"""Capability Framework — every feature is a self-contained, self-registering capability.

Each capability declares:
  - Manifest (id, name, version, dependencies, events, APIs, entities, permissions, UI)
  - Lifecycle (draft → experimental → beta → stable → deprecated → removed)
  - Health (coverage, latency, errors, AI cost, usage)
  - Contracts (consumes, produces, events, APIs, permissions)

The Capability Registry is the single source of truth for what the platform can do.
Company360, Dynamic Navigation, Dynamic Search, Dynamic Permissions, AI — all read from here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class CapabilityStatus(str, Enum):
    DRAFT = "draft"
    EXPERIMENTAL = "experimental"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


@dataclass
class CapabilityContract:
    consumes: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    apis: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "consumes": self.consumes,
            "produces": self.produces,
            "events": self.events,
            "apis": self.apis,
            "permissions": self.permissions,
            "entities": self.entities,
        }


@dataclass
class CapabilityUIDefinition:
    tabs: list[str] = field(default_factory=list)
    sidebar: Optional[str] = None
    icon: Optional[str] = None
    routes: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tabs": self.tabs,
            "sidebar": self.sidebar,
            "icon": self.icon,
            "routes": self.routes,
            "components": self.components,
        }


@dataclass
class CapabilityHealth:
    coverage: float = 0.0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    ai_cost_per_call: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "coverage": self.coverage,
            "avg_latency_ms": self.avg_latency_ms,
            "error_rate": self.error_rate,
            "ai_cost_per_call": self.ai_cost_per_call,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


@dataclass
class CapabilityManifest:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    owner: str = "platform"
    status: CapabilityStatus = CapabilityStatus.DRAFT
    dependencies: list[str] = field(default_factory=list)
    contract: CapabilityContract = field(default_factory=CapabilityContract)
    ui: CapabilityUIDefinition = field(default_factory=CapabilityUIDefinition)
    health: CapabilityHealth = field(default_factory=CapabilityHealth)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "owner": self.owner,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "contract": self.contract.to_dict(),
            "ui": self.ui.to_dict(),
            "health": self.health.to_dict(),
            "tags": self.tags,
        }


# ── Capability class (decorator-based registration) ───────────

class Capability:
    """Decorator to register a Python class as a platform capability.

    Usage:
        @Capability(id="company", name="Company Intelligence", version="1.0.0")
        class CompanyCapability:
            ...

    Or instantiate directly:
        cap = Capability(id="search", name="Universal Search")
        CapabilityRegistry.register(cap)
    """

    _registry: dict[str, "Capability"] = {}

    def __init__(
        self,
        id: str,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        owner: str = "platform",
        status: CapabilityStatus = CapabilityStatus.DRAFT,
        dependencies: Optional[list[str]] = None,
        contract: Optional[CapabilityContract] = None,
        ui: Optional[CapabilityUIDefinition] = None,
        tags: Optional[list[str]] = None,
    ):
        self.manifest = CapabilityManifest(
            id=id, name=name, version=version, description=description,
            owner=owner, status=status, dependencies=dependencies or [],
            contract=contract or CapabilityContract(),
            ui=ui or CapabilityUIDefinition(),
            tags=tags or [id],
        )
        self._impl: Optional[type] = None

    def __call__(self, cls):
        """Use as decorator — captures the class as implementation."""
        self._impl = cls
        Capability._registry[self.manifest.id] = self
        return cls

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def impl(self) -> Optional[type]:
        return self._impl

    @classmethod
    def get(cls, capability_id: str) -> Optional["Capability"]:
        return cls._registry.get(capability_id)

    @classmethod
    def all(cls) -> list["Capability"]:
        return list(cls._registry.values())

    @classmethod
    def by_status(cls, status: CapabilityStatus) -> list["Capability"]:
        return [c for c in cls.all() if c.manifest.status == status]

    @classmethod
    def by_tag(cls, tag: str) -> list["Capability"]:
        return [c for c in cls.all() if tag in c.manifest.tags]

    @classmethod
    def sidebar_items(cls) -> list[dict]:
        return [
            {"id": c.id, "name": c.manifest.name, "icon": c.manifest.ui.icon,
             "routes": c.manifest.ui.routes, "tabs": c.manifest.ui.tabs}
            for c in cls.all() if c.manifest.ui.sidebar or c.manifest.ui.routes
        ]

    @classmethod
    def tab_items(cls, parent_id: str) -> list[dict]:
        cap = cls.get(parent_id)
        if not cap:
            return []
        return [{"id": tab, "name": tab.replace("_", " ").title()} for tab in cap.manifest.ui.tabs]

    @classmethod
    def searchable_entities(cls) -> list[dict]:
        return [
            {"capability": c.id, "entities": c.manifest.contract.entities}
            for c in cls.all() if c.manifest.contract.entities
        ]

    @classmethod
    def registered_apis(cls) -> list[dict]:
        return [
            {"capability": c.id, "apis": c.manifest.contract.apis}
            for c in cls.all() if c.manifest.contract.apis
        ]

    @classmethod
    def registered_events(cls) -> list[dict]:
        return [
            {"capability": c.id, "events": c.manifest.contract.events}
            for c in cls.all() if c.manifest.contract.events
        ]

    @classmethod
    def registered_permissions(cls) -> list[str]:
        perms: list[str] = []
        for c in cls.all():
            perms.extend(c.manifest.contract.permissions)
        return list(set(perms))


# ── Built-in Capabilities ─────────────────────────────────────

@Capability(
    id="identity",
    name="Identity & Access Management",
    version="1.0.0",
    description="Tenant management, user auth, roles, permissions",
    owner="platform",
    status=CapabilityStatus.STABLE,
    contract=CapabilityContract(
        entities=["tenant", "user"],
        apis=["/api/v1/identity/*"],
        events=["tenant.created", "user.registered", "user.logged_in", "user.role_changed"],
        permissions=["tenant.read", "tenant.write", "user.read", "user.write", "user.admin"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Settings", "Users", "Roles", "Audit"],
        icon="shield",
        routes=["/settings", "/settings/users"],
    ),
    tags=["core", "identity", "security"],
)
class IdentityCapability:
    pass


@Capability(
    id="company",
    name="Company Intelligence",
    version="1.0.0",
    description="Company profiles, CR data, enrichment, golden records",
    owner="platform",
    status=CapabilityStatus.STABLE,
    dependencies=["identity", "data-fabric"],
    contract=CapabilityContract(
        entities=["company", "contact", "license", "branch"],
        apis=["/api/v1/companies/*", "/api/v1/entity-resolution/*"],
        events=["company.created", "company.updated", "company.enriched", "company.merged",
                "contact.created", "license.created", "golden_record.created"],
        permissions=["company.read", "company.write", "company.admin",
                     "contact.read", "contact.write", "license.read"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Overview", "Timeline", "Contacts", "Revenue", "Signals",
              "Products", "Documents", "Recommendations", "Graph", "Audit"],
        icon="building",
        sidebar="main",
        routes=["/companies", "/companies/{id}"],
    ),
    tags=["core", "company", "intelligence"],
)
class CompanyCapability:
    pass


@Capability(
    id="data-fabric",
    name="Data Fabric",
    version="1.0.0",
    description="Data ingestion, normalization, validation, entity resolution",
    owner="platform",
    status=CapabilityStatus.STABLE,
    dependencies=["identity"],
    contract=CapabilityContract(
        entities=["ingestion_batch", "source"],
        apis=["/api/v1/data-fabric/*"],
        events=["data.ingested", "data.normalized", "data.validated", "entity.resolved"],
        permissions=["data-fabric.read", "data-fabric.write", "data-fabric.admin"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Sources", "Pipeline", "Schedule", "Logs"],
        icon="database",
        routes=["/data-fabric"],
    ),
    tags=["core", "data", "pipeline"],
)
class DataFabricCapability:
    pass


@Capability(
    id="search",
    name="Universal Search",
    version="1.0.0",
    description="Full-text, semantic, graph, and hybrid search across all entities",
    owner="platform",
    status=CapabilityStatus.STABLE,
    dependencies=["company", "identity"],
    contract=CapabilityContract(
        entities=["company", "contact"],
        apis=["/api/v1/search", "/api/v1/search/suggest", "/api/v1/search/similar/*"],
        permissions=["search.read"],
    ),
    ui=CapabilityUIDefinition(
        icon="search",
        routes=["/search"],
    ),
    tags=["core", "search"],
)
class SearchCapability:
    pass


@Capability(
    id="timeline",
    name="Universal Timeline",
    version="1.0.0",
    description="Event-sourced timelines for every business object",
    owner="platform",
    status=CapabilityStatus.STABLE,
    dependencies=["event-runtime"],
    contract=CapabilityContract(
        entities=["timeline_entry"],
        apis=["/api/v1/timeline/*"],
        events=["*"],  # subscribes to ALL events
        permissions=["timeline.read"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Activity", "History"],
        icon="clock",
    ),
    tags=["core", "timeline", "events"],
)
class TimelineCapability:
    pass


@Capability(
    id="knowledge-graph",
    name="Knowledge Graph",
    version="1.0.0",
    description="Entity relationship graph with Neo4j and SQL fallback",
    owner="platform",
    status=CapabilityStatus.BETA,
    dependencies=["company"],
    contract=CapabilityContract(
        entities=["graph_node", "graph_edge"],
        apis=["/api/v1/graph/*"],
        events=["graph.populated", "graph.edge.created"],
        permissions=["graph.read", "graph.write"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Graph View", "Relationships", "Path Finder"],
        icon="share2",
    ),
    tags=["core", "graph", "neo4j"],
)
class KnowledgeGraphCapability:
    pass


@Capability(
    id="feature-store",
    name="Feature Store",
    version="1.0.0",
    description="Precomputed business features: ICP, Funding, Hiring, Growth, Intent, Expansion, Revenue",
    owner="platform",
    status=CapabilityStatus.STABLE,
    dependencies=["company"],
    contract=CapabilityContract(
        entities=["company_feature"],
        apis=["/api/v1/features/*"],
        events=["feature.computed", "feature.refreshed"],
        permissions=["feature-store.read"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Features", "Scores", "History"],
        icon="bar-chart",
    ),
    tags=["core", "features", "ml"],
)
class FeatureStoreCapability:
    pass


@Capability(
    id="decision-engine",
    name="Decision Intelligence Engine",
    version="1.0.0",
    description="Context-aware decision engine with NBA, policies, feedback loop",
    owner="platform",
    status=CapabilityStatus.BETA,
    dependencies=["feature-store", "context-runtime", "policy-runtime"],
    contract=CapabilityContract(
        entities=["decision", "recommendation", "feedback"],
        apis=["/api/v1/decision/*", "/api/v1/decisions/*"],
        events=["decision.created", "decision.accepted", "decision.executed",
                "decision.feedback_received"],
        permissions=["decision.read", "decision.write", "decision.admin"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Next Best Action", "Decisions", "History", "Metrics"],
        icon="zap",
        sidebar="main",
        routes=["/decisions"],
    ),
    tags=["core", "ai", "decision"],
)
class DecisionEngineCapability:
    pass


@Capability(
    id="event-runtime",
    name="Event Runtime",
    version="1.0.0",
    description="Event lifecycle orchestrator: store, subscribers, retry, DLQ, metrics",
    owner="platform",
    status=CapabilityStatus.STABLE,
    contract=CapabilityContract(
        entities=["domain_event"],
        apis=["/api/v1/event-runtime/*"],
        events=["*"],
        permissions=["event-runtime.read", "event-runtime.admin"],
    ),
    tags=["core", "events", "infrastructure"],
)
class EventRuntimeCapability:
    pass


@Capability(
    id="marketplace",
    name="Marketplace",
    version="0.1.0",
    description="Capability marketplace — install new capabilities dynamically",
    owner="platform",
    status=CapabilityStatus.DRAFT,
    dependencies=["capability-framework"],
    contract=CapabilityContract(
        entities=["marketplace_item", "capability_install"],
        permissions=["marketplace.read", "marketplace.install", "marketplace.admin"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["Browse", "Installed", "Updates"],
        icon="shopping-cart",
        routes=["/marketplace"],
    ),
    tags=["marketplace", "ecosystem"],
)
class MarketplaceCapability:
    pass


@Capability(
    id="capability-framework",
    name="Capability Framework",
    version="1.0.0",
    description="Self-describing platform capabilities: manifest, registry, lifecycle, health",
    owner="platform",
    status=CapabilityStatus.STABLE,
    contract=CapabilityContract(
        entities=["capability"],
        apis=["/api/v1/capabilities/*"],
        permissions=["capability.read", "capability.admin"],
    ),
    ui=CapabilityUIDefinition(
        tabs=["All Capabilities", "Health", "Registry"],
        icon="grid",
        routes=["/capabilities"],
    ),
    tags=["core", "platform", "architecture"],
)
class CapabilityFrameworkCapability:
    pass
