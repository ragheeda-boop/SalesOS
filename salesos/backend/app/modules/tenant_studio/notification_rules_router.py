"""STORY-10-08 — Tenant Studio Notification Rules HTTP (CAP-093).

CRUD + compile + route via existing RulesEngine send_notification.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.notification_rules import (
    VALID_EVENT_TYPES,
    NotificationRuleError,
)
from app.modules.tenant_studio.notification_rules_store import (
    DEFAULT_NOTIFICATION_RULES_STORE,
    MemNotificationRulesStore,
)

router = APIRouter(prefix="/studio/notification-rules", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_NOTIFICATION_RULES_STORE


class ConditionIn(BaseModel):
    field: str = Field(..., min_length=1, max_length=64)
    operator: Literal[
        "equals",
        "not_equals",
        "greater_than",
        "less_than",
        "contains",
        "in",
        "not_in",
    ]
    value: Any = None


class RecipientIn(BaseModel):
    kind: Literal["role", "user", "owner"]
    value: str = Field(..., min_length=1, max_length=128)


class NotificationRuleUpsert(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    event_type: str = Field(..., min_length=1, max_length=64)
    channels: list[str] = Field(default_factory=list)
    recipients: list[RecipientIn] = Field(default_factory=list)
    conditions: list[ConditionIn] = Field(default_factory=list)
    message_template: str = ""
    priority: int = 100
    active: bool = True


class NotificationRuleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    event_type: str
    channels: list[str] = Field(default_factory=list)
    recipients: list[dict[str, Any]] = Field(default_factory=list)
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    message_template: str = ""
    priority: int = 100
    active: bool = True
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


class RouteEventBody(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)
    entity_id: str = "event"


@router.get("/events", dependencies=_AUTH)
async def list_notification_events() -> dict[str, Any]:
    return {"event_types": sorted(VALID_EVENT_TYPES), "channels": ["in_app", "email"]}


@router.post("", response_model=NotificationRuleResponse, dependencies=_AUTH)
async def upsert_notification_rule(
    body: NotificationRuleUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> NotificationRuleResponse:
    try:
        row = _STORE.upsert(
            tenant_id=str(tenant_id),
            name=body.name,
            event_type=body.event_type,
            channels=list(body.channels),
            recipients=[r.model_dump() for r in body.recipients],
            conditions=[c.model_dump() for c in body.conditions],
            message_template=body.message_template,
            priority=body.priority,
            active=body.active,
            rule_id=body.id,
        )
    except NotificationRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return NotificationRuleResponse.model_validate(row.as_dict())


@router.get("", response_model=list[NotificationRuleResponse], dependencies=_AUTH)
async def list_notification_rules(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[NotificationRuleResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [NotificationRuleResponse.model_validate(r.as_dict()) for r in rows]


@router.post("/route", dependencies=_AUTH)
async def route_notification_event_http(
    body: RouteEventBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    result = _STORE.route(
        tenant_id=str(tenant_id),
        event_type=body.event_type,
        payload=dict(body.payload),
        entity_id=body.entity_id,
    )
    return result.as_dict()


@router.get("/{rule_id}", response_model=NotificationRuleResponse, dependencies=_AUTH)
async def get_notification_rule(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> NotificationRuleResponse:
    row = _STORE.get(rule_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="notification rule not found")
    return NotificationRuleResponse.model_validate(row.as_dict())


@router.post("/{rule_id}/compile", dependencies=_AUTH)
async def compile_notification_rule_http(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    try:
        studio, engine = _STORE.compile(rule_id, tenant_id=str(tenant_id))
    except NotificationRuleError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "rule": studio.as_dict(),
        "engine_rule": engine.model_dump(mode="json"),
    }


def bind_store(store: MemNotificationRulesStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
