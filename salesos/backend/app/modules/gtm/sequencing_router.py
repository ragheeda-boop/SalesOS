"""STORY-11-09 — GTM Sequencing Engine HTTP (CAP-104).

Email + LinkedIn/WhatsApp via compliant partner senders; Task/Activity bindings.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.sequencing import SequencingError
from app.modules.gtm.sequencing_store import (
    DEFAULT_SEQUENCING_STORE,
    MemSequencingStore,
)

router = APIRouter(prefix="/gtm/sequences", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_SEQUENCING_STORE


class SequenceStepBody(BaseModel):
    id: str | None = None
    day_offset: int = 0
    channel: str = "email"
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = ""


class SequenceCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    steps: list[SequenceStepBody] = Field(..., min_length=1)
    id: str | None = None


class EnrollBody(BaseModel):
    contact_email: str = Field(..., min_length=3, max_length=320)
    linkedin: str = ""
    whatsapp: str = ""
    id: str | None = None


class SequenceResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    steps: list[dict[str, Any]]
    channel: str = "email"
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""
    step_count: int = 0


class EnrollmentResponse(BaseModel):
    id: str
    tenant_id: str
    sequence_id: str
    contact_email: str
    contact_handles: dict[str, str] = Field(default_factory=dict)
    status: str
    current_step_index: int = 0
    step_states: list[dict[str, Any]]
    task_bindings: list[dict[str, Any]]
    activity_bindings: list[dict[str, Any]]
    last_send: dict[str, Any] = Field(default_factory=dict)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""
    bound_to_task_activity: bool = True


@router.get("/meta", dependencies=_AUTH)
async def sequencing_meta() -> dict[str, Any]:
    return {
        "object": "SequenceDefinition",
        "channels": ["email", "linkedin", "whatsapp"],
        "linkedin_policy": "compliant partner API only — no ToS-risk automation",
        "binding": "Activity/Task-shaped refs (no parallel CRM model)",
        "honesty": (
            "CI uses MemLinkedInPartnerSender / MemWhatsAppPartnerSender / "
            "email recorded sender; live SMTP / LinkedIn / WhatsApp network "
            "not claimed."
        ),
    }


@router.post("", response_model=SequenceResponse, dependencies=_AUTH)
async def create_sequence(
    body: SequenceCreateBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> SequenceResponse:
    try:
        row = _STORE.create_definition(
            tenant_id=str(tenant_id),
            name=body.name,
            steps=[s.model_dump() for s in body.steps],
            definition_id=body.id,
        )
    except SequencingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SequenceResponse.model_validate(row.as_dict())


@router.get("", response_model=list[SequenceResponse], dependencies=_AUTH)
async def list_sequences(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[SequenceResponse]:
    rows = _STORE.list_definitions(tenant_id=str(tenant_id))
    return [SequenceResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/enrollments", response_model=list[EnrollmentResponse], dependencies=_AUTH)
async def list_enrollments(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[EnrollmentResponse]:
    rows = _STORE.list_enrollments(tenant_id=str(tenant_id))
    return [EnrollmentResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{sequence_id}", response_model=SequenceResponse, dependencies=_AUTH)
async def get_sequence(
    sequence_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> SequenceResponse:
    row = _STORE.get_definition(sequence_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="sequence definition not found")
    return SequenceResponse.model_validate(row.as_dict())


@router.post(
    "/{sequence_id}/enrollments",
    response_model=EnrollmentResponse,
    dependencies=_AUTH,
)
async def enroll_contact(
    sequence_id: str,
    body: EnrollBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrollmentResponse:
    try:
        handles = {
            k: v
            for k, v in {"linkedin": body.linkedin, "whatsapp": body.whatsapp}.items()
            if v.strip()
        }
        row = _STORE.enroll(
            tenant_id=str(tenant_id),
            sequence_id=sequence_id,
            contact_email=body.contact_email,
            enrollment_id=body.id,
            contact_handles=handles or None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="sequence definition not found") from exc
    except SequencingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return EnrollmentResponse.model_validate(row.as_dict())


@router.get(
    "/enrollments/{enrollment_id}",
    response_model=EnrollmentResponse,
    dependencies=_AUTH,
)
async def get_enrollment(
    enrollment_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrollmentResponse:
    row = _STORE.get_enrollment(enrollment_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="enrollment not found")
    return EnrollmentResponse.model_validate(row.as_dict())


@router.post(
    "/enrollments/{enrollment_id}/advance",
    response_model=EnrollmentResponse,
    dependencies=_AUTH,
)
async def advance_enrollment_http(
    enrollment_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrollmentResponse:
    try:
        row = await _STORE.advance(enrollment_id, tenant_id=str(tenant_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SequencingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EnrollmentResponse.model_validate(row.as_dict())


@router.post(
    "/enrollments/{enrollment_id}/pause",
    response_model=EnrollmentResponse,
    dependencies=_AUTH,
)
async def pause_enrollment_http(
    enrollment_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrollmentResponse:
    try:
        row = _STORE.pause(enrollment_id, tenant_id=str(tenant_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="enrollment not found") from exc
    except SequencingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EnrollmentResponse.model_validate(row.as_dict())


@router.post(
    "/enrollments/{enrollment_id}/resume",
    response_model=EnrollmentResponse,
    dependencies=_AUTH,
)
async def resume_enrollment_http(
    enrollment_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrollmentResponse:
    try:
        row = _STORE.resume(enrollment_id, tenant_id=str(tenant_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="enrollment not found") from exc
    except SequencingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EnrollmentResponse.model_validate(row.as_dict())


@router.post(
    "/enrollments/{enrollment_id}/cancel",
    response_model=EnrollmentResponse,
    dependencies=_AUTH,
)
async def cancel_enrollment_http(
    enrollment_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EnrollmentResponse:
    try:
        row = _STORE.cancel(enrollment_id, tenant_id=str(tenant_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="enrollment not found") from exc
    except SequencingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EnrollmentResponse.model_validate(row.as_dict())


def bind_store(store: MemSequencingStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
