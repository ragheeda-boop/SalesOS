"""Runtime — core execution infrastructure for SalesOS.

Directory structure:
  event_runtime/            — Event lifecycle orchestrator (Store → Subscribers → Retry → DLQ → Metrics)
  data_fabric_runtime/      — Ingestion pipeline (Collector → Normalizer → Validator → Entity Resolution → Golden Record)
  feature_store/            — Precomputed business features with caching and event refresh
  decision_runtime/         — Decision Intelligence Engine (Context → Policies → Engine → NBA → Feedback)
  context_runtime/          — Multi-dimensional company context builder
  policy_runtime/           — Business policy evaluation (DNC, VIP, Government, etc.)
  recommendation_runtime/   — Recommendation generation from templates
  knowledge_graph_runtime/  — Graph engine (Neo4j + SQL fallback)
  timeline_runtime/         — Universal Timeline for every object
  search_runtime/           — Semantic + Hybrid + Ranking search
  activity_runtime/         — Activity records spine table
  ux_runtime/               — Experience layer (Navigation, Layout, Widget, Theme, Command, Notification)
  widget_engine/            — Widget registry and built-in widgets
  capability_framework/     — Self-describing capabilities
  ui_schema_engine/         — Dynamic UI schema generation
  form_engine/              — Dynamic form generation from JSON Schema
  action_engine/            — Action registry and execution
  extension_api/            — Hook point registry
  plugin_sandbox/           — Isolated plugin execution
  admin_router/             — Admin-only endpoints
  object_viewer/            — Universal object viewer
"""

from runtime.event_runtime import EventRuntime, DeadLetterQueue, RetryPolicy, EventMetrics, SubscriberPriority
from runtime.data_fabric_runtime import DataFabricPipeline
from runtime.feature_store import FeatureStore, FeatureComputer, FeatureResult, FeatureStoreMetrics
from runtime.decision_runtime import DecisionEngine, DecisionObject, DecisionType, DecisionStatus, DecisionFeedback
from runtime.decision_runtime.feedback_loop import DecisionFeedbackLoop
from runtime.context_runtime import ContextBuilder, CompanyContext
from runtime.policy_runtime import PolicyEngine
from runtime.recommendation_runtime import RecommendationEngine, Recommendation
from runtime.knowledge_graph_runtime import KnowledgeGraphEngine, GraphNode, GraphEdge, GraphPath, NodeLabel, EdgeType
from runtime.timeline_runtime import TimelineRuntime, TimelineEntry
from runtime.search_runtime import SearchRuntime, SearchResult, SearchResultItem, SearchStrategy
from runtime.activity_runtime import ActivityRuntime
from runtime.ux_runtime import UXRuntime

__all__ = [
    "EventRuntime",
    "DeadLetterQueue",
    "RetryPolicy",
    "EventMetrics",
    "SubscriberPriority",
    "DataFabricPipeline",
    "FeatureStore",
    "FeatureComputer",
    "FeatureResult",
    "FeatureStoreMetrics",
    "DecisionEngine",
    "DecisionObject",
    "DecisionType",
    "DecisionStatus",
    "DecisionFeedback",
    "DecisionFeedbackLoop",
    "ContextBuilder",
    "CompanyContext",
    "PolicyEngine",
    "RecommendationEngine",
    "Recommendation",
    "KnowledgeGraphEngine",
    "GraphNode",
    "GraphEdge",
    "GraphPath",
    "NodeLabel",
    "EdgeType",
    "TimelineRuntime",
    "TimelineEntry",
    "SearchRuntime",
    "SearchResult",
    "SearchResultItem",
    "SearchStrategy",
    "ActivityRuntime",
    "UXRuntime",
]
