from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_current_tenant_id

router = APIRouter()


class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    app_notifications: bool = True
    opportunity_alerts: bool = True
    company_updates: bool = True
    weekly_summary: bool = True


class NotificationPreferencesPatch(BaseModel):
    email_notifications: bool | None = None
    app_notifications: bool | None = None
    opportunity_alerts: bool | None = None
    company_updates: bool | None = None
    weekly_summary: bool | None = None


_notification_preferences: dict[str, NotificationPreferences] = {}


@router.get("/notifications", response_model=NotificationPreferences)
async def get_notification_preferences(
    tenant_id: str = Depends(get_current_tenant_id),
) -> NotificationPreferences:
    return _notification_preferences.get(tenant_id, NotificationPreferences())


@router.patch("/notifications", response_model=NotificationPreferences)
async def update_notification_preferences(
    body: NotificationPreferencesPatch,
    tenant_id: str = Depends(get_current_tenant_id),
) -> NotificationPreferences:
    current = _notification_preferences.get(tenant_id, NotificationPreferences())
    updated = current.model_copy(update=body.model_dump(exclude_unset=True))
    _notification_preferences[tenant_id] = updated
    return updated
