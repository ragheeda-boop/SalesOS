"""STORY-11-09 — CAP-104 Sequencing Engine models (OBJ-356 SequenceDefinition).

Email-channel sequences bound to Activity/Task-shaped refs (no parallel CRM model).
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SequenceStatus = Literal["draft", "active", "paused", "completed", "cancelled"]
StepRuntimeStatus = Literal["pending", "due", "sent", "skipped", "failed"]
SUPPORTED_CHANNELS: tuple[str, ...] = ("email",)


class SequencingError(ValueError):
    """Invalid sequence definition or enrollment input."""


@dataclass
class SequenceStep:
    """One email step in a sequence definition."""

    id: str
    day_offset: int = 0
    channel: str = "email"
    subject: str = ""
    body: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "day_offset": self.day_offset,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
        }


@dataclass
class SequenceDefinition:
    """Versioned sequence template (email-only this sprint)."""

    id: str
    tenant_id: str
    name: str
    steps: list[SequenceStep] = field(default_factory=list)
    channel: str = "email"
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "steps": [s.as_dict() for s in self.steps],
            "channel": self.channel,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "step_count": len(self.steps),
        }


@dataclass(frozen=True)
class BoundTaskRef:
    """Task-shaped binding — not a parallel engagement aggregate."""

    task_id: str
    title: str
    source: str = "sequence"
    completed: bool = False
    step_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "source": self.source,
            "completed": self.completed,
            "step_id": self.step_id,
        }


@dataclass(frozen=True)
class BoundActivityRef:
    """Activity-shaped binding for sequence step execution evidence."""

    activity_id: str
    kind: str = "email_sequence_step"
    summary: str = ""
    step_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "kind": self.kind,
            "summary": self.summary,
            "step_id": self.step_id,
        }


@dataclass
class EnrollmentStepState:
    step_id: str
    status: str = "pending"
    day_offset: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status,
            "day_offset": self.day_offset,
        }


@dataclass
class SequenceEnrollment:
    """Active enrollment of a contact into a sequence definition."""

    id: str
    tenant_id: str
    sequence_id: str
    contact_email: str
    status: str = "active"
    current_step_index: int = 0
    step_states: list[EnrollmentStepState] = field(default_factory=list)
    task_bindings: list[BoundTaskRef] = field(default_factory=list)
    activity_bindings: list[BoundActivityRef] = field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "sequence_id": self.sequence_id,
            "contact_email": self.contact_email,
            "status": self.status,
            "current_step_index": self.current_step_index,
            "step_states": [s.as_dict() for s in self.step_states],
            "task_bindings": [t.as_dict() for t in self.task_bindings],
            "activity_bindings": [a.as_dict() for a in self.activity_bindings],
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "bound_to_task_activity": True,
        }


def normalize_steps(raw_steps: list[dict[str, Any]] | None) -> list[SequenceStep]:
    if not raw_steps:
        raise SequencingError("at least one sequence step required")
    steps: list[SequenceStep] = []
    for i, raw in enumerate(raw_steps):
        channel = str(raw.get("channel") or "email").strip().lower() or "email"
        if channel not in SUPPORTED_CHANNELS:
            raise SequencingError(
                f"unsupported channel {channel!r}; email-only this sprint "
                "(LinkedIn/WhatsApp deferred)"
            )
        day = int(raw.get("day_offset") if raw.get("day_offset") is not None else i)
        if day < 0:
            raise SequencingError("day_offset must be >= 0")
        subject = str(raw.get("subject") or "").strip()
        body = str(raw.get("body") or "").strip()
        if not subject:
            raise SequencingError(f"step {i}: subject required")
        sid = str(raw.get("id") or "").strip() or f"step-{i + 1}"
        steps.append(
            SequenceStep(
                id=sid,
                day_offset=day,
                channel=channel,
                subject=subject,
                body=body,
            )
        )
    return steps
