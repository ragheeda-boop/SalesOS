"""STORY-10-01/10-02 — Tenant Studio custom field HTTP (CAP-082).

Definitions + auto-render form schema for Company/Contact/Opportunity UI.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.auto_render import (
    CUSTOM_FIELDS_BAG_KEY,
    auto_render_payload,
    merge_custom_field_values,
    read_custom_field_values,
)
from app.modules.tenant_studio.definitions import CustomFieldDefinitionError
from app.modules.tenant_studio.service import DEFAULT_STORE, MemCustomFieldDefinitionService

router = APIRouter(prefix="/studio/custom-fields", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_STORE


class CustomFieldCreate(BaseModel):
    object_key: Literal["company", "contact", "opportunity"]
    field_key: str = Field(..., min_length=1, max_length=64)
    field_type: Literal["string", "number", "date", "enum"]
    label: str = Field(default="", max_length=128)
    enum_values: list[str] | None = None


class CustomFieldResponse(BaseModel):
    id: str
    tenant_id: str
    object_key: str
    field_key: str
    field_type: str
    label: str
    schema_version: int
    enum_values: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class CustomObjectSchemaResponse(BaseModel):
    tenant_id: str
    object_key: str
    schema_version: int
    fields: list[CustomFieldResponse]


class CustomFieldValuesBody(BaseModel):
    """Merge custom field values into a metadata bag (known keys only)."""

    values: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomFieldValuesResponse(BaseModel):
    object_key: str
    bag_key: str = CUSTOM_FIELDS_BAG_KEY
    values: dict[str, Any]
    metadata: dict[str, Any]


@router.post("", response_model=CustomFieldResponse, dependencies=_AUTH)
async def define_custom_field(
    body: CustomFieldCreate,
    tenant_id: str = Depends(get_current_tenant_id),
) -> CustomFieldResponse:
    try:
        row = _STORE.define_field(
            tenant_id=str(tenant_id),
            object_key=body.object_key,
            field_key=body.field_key,
            field_type=body.field_type,
            label=body.label,
            enum_values=body.enum_values,
        )
    except CustomFieldDefinitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CustomFieldResponse.model_validate(row.as_dict())


@router.get("/{object_key}", response_model=CustomObjectSchemaResponse, dependencies=_AUTH)
async def get_custom_field_schema(
    object_key: Literal["company", "contact", "opportunity"],
    tenant_id: str = Depends(get_current_tenant_id),
) -> CustomObjectSchemaResponse:
    schema = _STORE.get_schema(tenant_id=str(tenant_id), object_key=object_key)
    return CustomObjectSchemaResponse.model_validate(schema.as_dict())


@router.get("/{object_key}/form-schema", dependencies=_AUTH)
async def get_auto_render_form_schema(
    object_key: Literal["company", "contact", "opportunity"],
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """STORY-10-02 — Form Engine schema for generic FE auto-render."""
    schema = _STORE.get_schema(tenant_id=str(tenant_id), object_key=object_key)
    return auto_render_payload(schema)


@router.post(
    "/{object_key}/values",
    response_model=CustomFieldValuesResponse,
    dependencies=_AUTH,
)
async def project_custom_field_values(
    object_key: Literal["company", "contact", "opportunity"],
    body: CustomFieldValuesBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> CustomFieldValuesResponse:
    """Merge/filter custom field values against tip definitions (no ORM write)."""
    schema = _STORE.get_schema(tenant_id=str(tenant_id), object_key=object_key)
    defs = list(schema.fields.values())
    merged = merge_custom_field_values(body.metadata, body.values, definitions=defs)
    values = read_custom_field_values(merged, definitions=defs)
    return CustomFieldValuesResponse(
        object_key=object_key,
        bag_key=CUSTOM_FIELDS_BAG_KEY,
        values=values,
        metadata=merged,
    )


def _reset_store_for_tests() -> MemCustomFieldDefinitionService:
    """Test helper — replace process store."""
    global _STORE
    from app.modules.tenant_studio import service as svc_mod

    svc_mod.DEFAULT_STORE = MemCustomFieldDefinitionService()
    _STORE = svc_mod.DEFAULT_STORE
    return _STORE


def store_snapshot() -> dict[str, Any]:
    return {k: v.as_dict() for k, v in _STORE._schemas.items()}
