"""STORY-09-05 — project.task pull → Task + optional TaskCaseExtension VO.

Extension is a Value Object on Task (no standalone aggregate id).
No invented secrets. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.modules.integration_hub.anti_corruption import (
    AclValidationError,
    CanonicalRecord,
    OdooTranslator,
)
from app.modules.integration_hub.task_case_extension import (
    TaskCaseExtension,
    TaskCaseExtensionValidationError,
    build_task_case_extension,
)
from app.modules.integration_hub.types import PullRecord

DEFAULT_TASK_MAPPINGS: list[dict[str, Any]] = [
    {"internal": "name", "external": "name", "direction": "pull"},
    {"internal": "stage", "external": "stage_id", "direction": "pull"},
]

# Soft stage map for project.task (not strict — generic work tasks vary).
DEFAULT_TASK_STAGE_MAP: dict[str, str] = {
    "1": "new",
    "2": "in_progress",
    "3": "done",
    "new": "new",
    "in_progress": "in_progress",
    "done": "done",
}


@dataclass
class TaskSyncItem:
    external_id: str
    record: CanonicalRecord
    case_extension: TaskCaseExtension | None = None


@dataclass
class TaskSyncBatchResult:
    synced: list[TaskSyncItem] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records_pulled(self) -> int:
        return len(self.synced) + len(self.failed)


async def sync_project_tasks(
    records: Sequence[PullRecord] | Sequence[Mapping[str, Any]],
    *,
    sync_run_id: str,
    mappings: list[Mapping[str, Any]] | None = None,
    translator: OdooTranslator | None = None,
) -> TaskSyncBatchResult:
    """Translate project.task; attach TaskCaseExtension VO when case fields exist."""
    acl = translator or OdooTranslator(stage_map=DEFAULT_TASK_STAGE_MAP)
    maps = list(mappings or DEFAULT_TASK_MAPPINGS)
    out = TaskSyncBatchResult()

    for raw in records:
        if isinstance(raw, PullRecord):
            external_id = raw.external_id
            payload = raw.payload
            updated_at = raw.updated_at
        else:
            external_id = str(raw.get("id") or raw.get("external_id") or "")
            payload = dict(raw)
            updated_at = None
        try:
            # Stage optional on some Odoo task types.
            active_maps = list(maps)
            if payload.get("stage_id") in (None, False, ""):
                active_maps = [
                    m
                    for m in active_maps
                    if not (isinstance(m, Mapping) and m.get("internal") == "stage")
                ]
            canonical = acl.translate(
                payload,
                mappings=active_maps,
                sync_run_id=sync_run_id,
                source_updated_at=updated_at,
            )
            extension = build_task_case_extension(dict(payload))
            if extension is not None:
                # Nest VO — never mint a separate aggregate id.
                canonical.payload["case_extension"] = extension.to_dict()
                assert "id" not in extension.to_dict()
            out.synced.append(
                TaskSyncItem(
                    external_id=external_id or "unknown",
                    record=canonical,
                    case_extension=extension,
                )
            )
        except (AclValidationError, TaskCaseExtensionValidationError) as exc:
            field = getattr(exc, "field", None) or getattr(exc, "case_type", None)
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "malformed_data",
                    "message": str(exc),
                    "field": field,
                }
            )
        except Exception as exc:
            out.failed.append(
                {
                    "external_id": external_id,
                    "kind": "unknown",
                    "message": str(exc),
                }
            )
    return out
