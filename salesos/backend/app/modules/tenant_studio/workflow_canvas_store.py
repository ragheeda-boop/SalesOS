"""STORY-10-03 — In-memory Workflow Canvas store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.tenant_studio.workflow_canvas import WorkflowCanvas
from app.modules.tenant_studio.workflow_compiler import (
    WorkflowCanvasCompileError,
    compile_canvas,
    workflow_to_public_dict,
)
from domains.workflow.models import Workflow


@dataclass
class MemWorkflowCanvasStore:
    """Tenant-scoped canvas drafts for CAP-083 Studio."""

    _by_id: dict[str, WorkflowCanvas] = field(default_factory=dict)

    def save(self, canvas: WorkflowCanvas) -> WorkflowCanvas:
        tid = (canvas.tenant_id or "").strip()
        if not tid:
            raise WorkflowCanvasCompileError("tenant_id required")
        if not (canvas.name or "").strip():
            raise WorkflowCanvasCompileError("name required")
        now = datetime.now(UTC).isoformat()
        if not canvas.id:
            canvas.id = uuid.uuid4().hex[:12]
        existing = self._by_id.get(canvas.id)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant canvas write blocked")
        canvas.created_at = existing.created_at if existing else now
        canvas.updated_at = now
        if existing:
            canvas.schema_version = max(existing.schema_version + 1, 1)
        self._by_id[canvas.id] = canvas
        return canvas

    def get(self, canvas_id: str, *, tenant_id: str) -> WorkflowCanvas | None:
        row = self._by_id.get(str(canvas_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[WorkflowCanvas]:
        tid = str(tenant_id)
        return [c for c in self._by_id.values() if c.tenant_id == tid]

    def compile(
        self, canvas_id: str, *, tenant_id: str, status: str = "draft"
    ) -> tuple[WorkflowCanvas, Workflow, dict]:
        canvas = self.get(canvas_id, tenant_id=tenant_id)
        if canvas is None:
            raise KeyError("canvas not found")
        workflow = compile_canvas(canvas, workflow_id=canvas.id, status=status)
        return canvas, workflow, workflow_to_public_dict(workflow)


DEFAULT_CANVAS_STORE = MemWorkflowCanvasStore()
