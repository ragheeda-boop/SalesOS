"""STORY-11-09 / 11-09b — In-memory sequences + multi-channel enrollments."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.sequence_channels import (
    CompliantChannelSender,
    build_default_channel_senders,
)
from app.modules.gtm.sequencing import (
    SequenceDefinition,
    SequenceEnrollment,
    SequencingError,
    normalize_steps,
)
from app.modules.gtm.sequencing_engine import (
    advance_enrollment,
    build_enrollment,
    cancel_enrollment,
    pause_enrollment,
    resume_enrollment,
)


@dataclass
class MemSequencingStore:
    """Tenant-scoped SequenceDefinition + SequenceEnrollment for CAP-104."""

    _definitions: dict[str, SequenceDefinition] = field(default_factory=dict)
    _enrollments: dict[str, SequenceEnrollment] = field(default_factory=dict)
    _senders: dict[str, CompliantChannelSender] = field(
        default_factory=build_default_channel_senders
    )

    def bind_senders(self, senders: dict[str, CompliantChannelSender]) -> None:
        self._senders = dict(senders)

    def create_definition(
        self,
        *,
        tenant_id: str,
        name: str,
        steps: list[dict] | None,
        definition_id: str | None = None,
    ) -> SequenceDefinition:
        tid = (tenant_id or "").strip()
        if not tid:
            raise SequencingError("tenant_id required")
        nm = (name or "").strip()
        if not nm:
            raise SequencingError("name required")
        parsed = normalize_steps(steps)
        channels = {s.channel for s in parsed}
        channel_label = next(iter(channels)) if len(channels) == 1 else "multi"
        rid = (definition_id or "").strip() or uuid.uuid4().hex[:12]
        if rid in self._definitions:
            raise SequencingError("sequence id already exists; use a new id")
        now = datetime.now(UTC).isoformat()
        row = SequenceDefinition(
            id=rid,
            tenant_id=tid,
            name=nm,
            steps=parsed,
            channel=channel_label,
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
        self._definitions[row.id] = row
        return row

    def get_definition(self, definition_id: str, *, tenant_id: str) -> SequenceDefinition | None:
        row = self._definitions.get(str(definition_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_definitions(self, *, tenant_id: str) -> list[SequenceDefinition]:
        tid = str(tenant_id)
        return sorted(
            [d for d in self._definitions.values() if d.tenant_id == tid],
            key=lambda d: d.updated_at or "",
            reverse=True,
        )

    def enroll(
        self,
        *,
        tenant_id: str,
        sequence_id: str,
        contact_email: str,
        enrollment_id: str | None = None,
        contact_handles: dict[str, str] | None = None,
    ) -> SequenceEnrollment:
        definition = self.get_definition(sequence_id, tenant_id=tenant_id)
        if definition is None:
            raise KeyError("sequence definition not found")
        now = datetime.now(UTC).isoformat()
        row = build_enrollment(
            definition,
            tenant_id=str(tenant_id),
            contact_email=contact_email,
            enrollment_id=enrollment_id,
            created_at=now,
            contact_handles=contact_handles,
        )
        existing = self._enrollments.get(row.id)
        if existing and existing.tenant_id != str(tenant_id):
            raise PermissionError("cross-tenant enrollment write blocked")
        self._enrollments[row.id] = row
        return row

    async def advance(self, enrollment_id: str, *, tenant_id: str) -> SequenceEnrollment:
        enrollment = self.get_enrollment(enrollment_id, tenant_id=tenant_id)
        if enrollment is None:
            raise KeyError("enrollment not found")
        definition = self.get_definition(enrollment.sequence_id, tenant_id=tenant_id)
        if definition is None:
            raise KeyError("sequence definition not found")
        now = datetime.now(UTC).isoformat()
        updated = await advance_enrollment(
            enrollment,
            definition,
            now_iso=now,
            senders=self._senders,
        )
        self._enrollments[updated.id] = updated
        return updated

    def pause(self, enrollment_id: str, *, tenant_id: str) -> SequenceEnrollment:
        enrollment = self.get_enrollment(enrollment_id, tenant_id=tenant_id)
        if enrollment is None:
            raise KeyError("enrollment not found")
        updated = pause_enrollment(enrollment, now_iso=datetime.now(UTC).isoformat())
        self._enrollments[updated.id] = updated
        return updated

    def resume(self, enrollment_id: str, *, tenant_id: str) -> SequenceEnrollment:
        enrollment = self.get_enrollment(enrollment_id, tenant_id=tenant_id)
        if enrollment is None:
            raise KeyError("enrollment not found")
        updated = resume_enrollment(enrollment, now_iso=datetime.now(UTC).isoformat())
        self._enrollments[updated.id] = updated
        return updated

    def cancel(self, enrollment_id: str, *, tenant_id: str) -> SequenceEnrollment:
        enrollment = self.get_enrollment(enrollment_id, tenant_id=tenant_id)
        if enrollment is None:
            raise KeyError("enrollment not found")
        updated = cancel_enrollment(enrollment, now_iso=datetime.now(UTC).isoformat())
        self._enrollments[updated.id] = updated
        return updated

    def get_enrollment(self, enrollment_id: str, *, tenant_id: str) -> SequenceEnrollment | None:
        row = self._enrollments.get(str(enrollment_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_enrollments(self, *, tenant_id: str) -> list[SequenceEnrollment]:
        tid = str(tenant_id)
        return sorted(
            [e for e in self._enrollments.values() if e.tenant_id == tid],
            key=lambda e: e.updated_at or "",
            reverse=True,
        )


DEFAULT_SEQUENCING_STORE = MemSequencingStore()
