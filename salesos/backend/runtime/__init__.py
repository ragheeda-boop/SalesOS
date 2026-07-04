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
  timeline_runtime/         — Universal Timeline for every object (planned)
  search_runtime/           — Semantic + Hybrid + Ranking search (planned)
  workflow_runtime/         — Workflow execution engine (planned)
  agent_runtime/            — AI agent execution (planned for P1)
  execution_runtime/        — Sync/async execution models (planned)
  memory_runtime/           — Agent memory management (planned)
  simulation_runtime/       — Scenario simulation (planned)
  scheduler_runtime/        — Scheduled/cron task execution (planned)
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
]
