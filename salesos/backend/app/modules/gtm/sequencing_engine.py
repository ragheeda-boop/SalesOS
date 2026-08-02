"""STORY-11-09 / 11-09b — Sequencing state machine (email + LinkedIn + WhatsApp).

Advances enrollments via compliant partner channel senders; binds Task + Activity.
Honesty: no live SMTP / LinkedIn / WhatsApp network claimed.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

import uuid

from app.modules.gtm.sequence_channels import (
    CompliantChannelSender,
    build_default_channel_senders,
)
from app.modules.gtm.sequencing import (
    BoundActivityRef,
    BoundTaskRef,
    EnrollmentStepState,
    SequenceDefinition,
    SequenceEnrollment,
    SequencingError,
)


def build_enrollment(
    definition: SequenceDefinition,
    *,
    tenant_id: str,
    contact_email: str,
    enrollment_id: str | None = None,
    created_at: str,
    contact_handles: dict[str, str] | None = None,
) -> SequenceEnrollment:
    email = (contact_email or "").strip().lower()
    if not email or "@" not in email:
        raise SequencingError("contact_email must be a valid email")
    if definition.tenant_id != tenant_id:
        raise SequencingError("sequence/tenant mismatch")
    if not definition.steps:
        raise SequencingError("sequence has no steps")

    handles = {
        str(k).strip().lower(): str(v).strip()
        for k, v in (contact_handles or {}).items()
        if str(k).strip() and str(v).strip()
    }
    states = [
        EnrollmentStepState(step_id=s.id, status="pending", day_offset=s.day_offset)
        for s in definition.steps
    ]
    states[0].status = "due"
    rid = (enrollment_id or "").strip() or uuid.uuid4().hex[:12]
    return SequenceEnrollment(
        id=rid,
        tenant_id=tenant_id,
        sequence_id=definition.id,
        contact_email=email,
        contact_handles=handles,
        status="active",
        current_step_index=0,
        step_states=states,
        created_at=created_at,
        updated_at=created_at,
    )


async def advance_enrollment(
    enrollment: SequenceEnrollment,
    definition: SequenceDefinition,
    *,
    now_iso: str,
    senders: dict[str, CompliantChannelSender] | None = None,
    send_mode: str = "partner_api",
) -> SequenceEnrollment:
    """Send current due step via channel sender, bind Task+Activity, advance."""
    if enrollment.status != "active":
        raise SequencingError(f"cannot advance enrollment in status {enrollment.status}")
    if definition.id != enrollment.sequence_id:
        raise SequencingError("definition/enrollment sequence_id mismatch")

    idx = enrollment.current_step_index
    if idx < 0 or idx >= len(definition.steps):
        raise SequencingError("current_step_index out of range")

    step = definition.steps[idx]
    state = enrollment.step_states[idx]
    if state.status not in ("due", "pending"):
        raise SequencingError(f"step {step.id} not actionable (status={state.status})")

    channel_map = senders or build_default_channel_senders()
    sender = channel_map.get(step.channel)
    if sender is None:
        raise SequencingError(f"no sender configured for channel {step.channel!r}")

    mode = "email_recorded" if step.channel == "email" else send_mode
    result = await sender.send(
        step=step,
        contact_email=enrollment.contact_email,
        contact_handles=dict(enrollment.contact_handles),
        mode=mode,
    )
    if not result.ok:
        state.status = "failed"
        enrollment.last_send = result.as_dict()
        enrollment.updated_at = now_iso
        enrollment.schema_version += 1
        raise SequencingError(f"channel send failed: {result.message}")

    task_id = f"task-{enrollment.id}-{step.id}"
    activity_id = f"act-{enrollment.id}-{step.id}"
    title = f"[Sequence:{step.channel}] {step.subject}"
    enrollment.task_bindings.append(
        BoundTaskRef(
            task_id=task_id,
            title=title,
            source="sequence",
            completed=True,
            step_id=step.id,
        )
    )
    enrollment.activity_bindings.append(
        BoundActivityRef(
            activity_id=activity_id,
            kind=f"{step.channel}_sequence_step",
            summary=(
                f"{step.channel} to {enrollment.contact_email}: {step.subject} "
                f"via {result.provider_key}"
            ),
            step_id=step.id,
        )
    )
    enrollment.last_send = result.as_dict()
    state.status = "sent"
    enrollment.updated_at = now_iso
    enrollment.schema_version += 1

    next_idx = idx + 1
    if next_idx >= len(definition.steps):
        enrollment.status = "completed"
        enrollment.current_step_index = idx
    else:
        enrollment.current_step_index = next_idx
        enrollment.step_states[next_idx].status = "due"

    return enrollment


def pause_enrollment(enrollment: SequenceEnrollment, *, now_iso: str) -> SequenceEnrollment:
    if enrollment.status != "active":
        raise SequencingError("only active enrollments can be paused")
    enrollment.status = "paused"
    enrollment.updated_at = now_iso
    enrollment.schema_version += 1
    return enrollment


def resume_enrollment(enrollment: SequenceEnrollment, *, now_iso: str) -> SequenceEnrollment:
    if enrollment.status != "paused":
        raise SequencingError("only paused enrollments can be resumed")
    enrollment.status = "active"
    enrollment.updated_at = now_iso
    enrollment.schema_version += 1
    return enrollment


def cancel_enrollment(enrollment: SequenceEnrollment, *, now_iso: str) -> SequenceEnrollment:
    if enrollment.status in ("completed", "cancelled"):
        raise SequencingError(f"cannot cancel enrollment in status {enrollment.status}")
    enrollment.status = "cancelled"
    enrollment.updated_at = now_iso
    enrollment.schema_version += 1
    for state in enrollment.step_states:
        if state.status in ("pending", "due"):
            state.status = "skipped"
    return enrollment
