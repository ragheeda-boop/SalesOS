"""STORY-10-03 — No-code Workflow Builder canvas document (CAP-083).

Canvas is a Studio authoring document. Execution always goes through the
existing ``domains.workflow.WorkflowEngine`` (no second interpreter).
Linear + branching (if_else). Loops/for_each deferred. Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

CanvasNodeKind = Literal["action", "branch"]


@dataclass
class CanvasNode:
    """One node on the no-code canvas.

    ``action`` → maps 1:1 to a ``WorkflowStep``.
    ``branch`` → compiles to ``if_else`` with nested then/else action defs.
    """

    id: str
    kind: CanvasNodeKind
    step_type: str = ""  # action: VALID_STEP_TYPES; branch: always if_else
    config: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None  # action gate OR branch condition
    then_nodes: list[CanvasNode] = field(default_factory=list)
    else_nodes: list[CanvasNode] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "step_type": self.step_type,
            "config": dict(self.config),
            "condition": self.condition,
            "then_nodes": [n.as_dict() for n in self.then_nodes],
            "else_nodes": [n.as_dict() for n in self.else_nodes],
        }

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> CanvasNode:
        return CanvasNode(
            id=str(raw.get("id") or ""),
            kind=str(raw.get("kind") or "action"),  # type: ignore[arg-type]
            step_type=str(raw.get("step_type") or ""),
            config=dict(raw.get("config") or {}),
            condition=raw.get("condition"),
            then_nodes=[CanvasNode.from_dict(n) for n in (raw.get("then_nodes") or [])],
            else_nodes=[CanvasNode.from_dict(n) for n in (raw.get("else_nodes") or [])],
        )


@dataclass
class WorkflowCanvas:
    """Tenant-scoped canvas draft for CAP-083 Studio."""

    id: str
    tenant_id: str
    name: str
    description: str = ""
    trigger_type: str = "manual"
    nodes: list[CanvasNode] = field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "nodes": [n.as_dict() for n in self.nodes],
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> WorkflowCanvas:
        now = datetime.now(UTC).isoformat()
        return WorkflowCanvas(
            id=str(raw.get("id") or ""),
            tenant_id=str(raw.get("tenant_id") or ""),
            name=str(raw.get("name") or ""),
            description=str(raw.get("description") or ""),
            trigger_type=str(raw.get("trigger_type") or "manual"),
            nodes=[CanvasNode.from_dict(n) for n in (raw.get("nodes") or [])],
            schema_version=int(raw.get("schema_version") or 1),
            created_at=str(raw.get("created_at") or now),
            updated_at=str(raw.get("updated_at") or now),
        )
