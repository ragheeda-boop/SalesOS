"""Agent SDK — build AI agents that understand the platform.

An agent gets:
  - Context: current object, user, tenant, permissions
  - Timeline: recent events for the object
  - Knowledge Graph: relationships, competitors, decision makers
  - Features: ICP, Funding, Hiring, Growth, Intent, Expansion, Revenue scores
  - Decisions: past decisions and their outcomes
  - Actions: available actions the agent can execute
  - Search: query any entity

No agent needs to access runtimes directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentContext:
    """Everything an agent knows about the current situation."""
    user_id: str
    tenant_id: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_data: Optional[dict] = None
    timeline: list[dict] = field(default_factory=list)
    features: dict = field(default_factory=dict)
    decisions: list[dict] = field(default_factory=list)
    graph: Optional[dict] = None
    permissions: list[str] = field(default_factory=list)
    active_widgets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_data": self.entity_data,
            "timeline_count": len(self.timeline),
            "features": self.features,
            "decisions_count": len(self.decisions),
            "graph": self.graph,
            "permissions": self.permissions,
            "active_widgets": self.active_widgets,
        }


@dataclass
class AgentAction:
    """An action an agent can propose or execute."""
    id: str
    label: str
    description: Optional[str] = None
    handler: Optional[str] = None
    parameters: dict = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "handler": self.handler,
            "parameters": self.parameters,
            "permissions": self.permissions,
            "requires_confirmation": self.requires_confirmation,
        }


class AgentContextCollector:
    """Collects context from all runtimes for the AI agent."""

    def __init__(self, runtime_registry: dict[str, Any]):
        self._runtimes = runtime_registry

    def collect(self, user_id: str, tenant_id: str,
                entity_type: Optional[str] = None,
                entity_id: Optional[str] = None) -> AgentContext:
        ctx = AgentContext(user_id=user_id, tenant_id=tenant_id,
                           entity_type=entity_type, entity_id=entity_id)

        # Entity data
        if entity_type and entity_id:
            # Try to get entity data from DB via session
            ctx.entity_data = {"type": entity_type, "id": entity_id}

        # Timeline
        timeline_rt = self._runtimes.get("timeline_runtime")
        if timeline_rt and entity_type and entity_id:
            try:
                import asyncio
                events = asyncio.run(timeline_rt.query(
                    entity_type=entity_type, entity_id=entity_id, limit=20
                ))
                ctx.timeline = events if isinstance(events, list) else []
            except Exception:
                pass

        # Features
        feature_store = self._runtimes.get("feature_store")
        if feature_store and entity_id:
            try:
                import asyncio
                scores = asyncio.run(feature_store.get_scores(entity_id))
                ctx.features = scores if isinstance(scores, dict) else {}
            except Exception:
                pass

        # Graph
        kg = self._runtimes.get("kg_engine")
        if kg and entity_id:
            try:
                import asyncio
                network = asyncio.run(kg.get_ego_network(entity_id, depth=1))
                ctx.graph = network if isinstance(network, dict) else None
            except Exception:
                pass

        return ctx


def create_agent_context(runtime_registry: dict[str, Any]) -> AgentContextCollector:
    return AgentContextCollector(runtime_registry)
