"""STORY-11-06 — GTM Contact Verification HTTP (CAP-100).

Single VerificationConnector interface with commodity swap-in.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.verification import VerificationError
from app.modules.gtm.verification_store import (
    DEFAULT_VERIFICATION_STORE,
    MemVerificationStore,
)

router = APIRouter(prefix="/gtm/verification", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_VERIFICATION_STORE


class VerificationBody(BaseModel):
    email: str = ""
    phone: str = ""
    provider_key: str = ""
    id: str | None = None


class ChannelVerdictResponse(BaseModel):
    channel: str
    value: str
    status: str
    confidence: float = 0.0
    reason: str = ""


class VerificationResponse(BaseModel):
    id: str
    tenant_id: str
    request: dict[str, Any]
    verdicts: list[ChannelVerdictResponse]
    provider_key: str = ""
    overall_status: str = "unknown"
    schema_version: int = 1
    created_at: str = ""


@router.get("/meta", dependencies=_AUTH)
async def verification_meta() -> dict[str, Any]:
    return {
        "channels": ["email", "phone"],
        "statuses": ["valid", "invalid", "unknown", "risky"],
        "connectors_configured": _STORE.connector_keys(),
        "interface": "VerificationConnector (single commodity swap-in)",
        "honesty": (
            "CI uses in-memory MemVerificationConnector (fake_verify); "
            "live NeverBounce/ZeroBounce/Twilio Lookup not claimed."
        ),
    }


@router.post("", response_model=VerificationResponse, dependencies=_AUTH)
async def run_contact_verification(
    body: VerificationBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> VerificationResponse:
    try:
        row = await _STORE.verify(
            tenant_id=str(tenant_id),
            email=body.email,
            phone=body.phone,
            provider_key=body.provider_key or None,
            run_id=body.id,
        )
    except VerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return VerificationResponse.model_validate(row.as_dict())


@router.get("", response_model=list[VerificationResponse], dependencies=_AUTH)
async def list_verification(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[VerificationResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [VerificationResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{run_id}", response_model=VerificationResponse, dependencies=_AUTH)
async def get_verification(
    run_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> VerificationResponse:
    row = _STORE.get(run_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="verification run not found")
    return VerificationResponse.model_validate(row.as_dict())


def bind_store(store: MemVerificationStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
