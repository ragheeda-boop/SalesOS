from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.application.dashboard.dto.widget_state import WidgetStatus


class WidgetAction(BaseModel):
    id: str
    label: str
    type: str  # 'refresh' | 'navigate' | 'dismiss' | 'custom'
    payload: dict | None = None


class DashboardWidget(BaseModel):
    id: str
    title: str
    status: WidgetStatus = WidgetStatus.loading
    lastUpdated: datetime | None = None
    data: dict | None = None
    actions: list[WidgetAction] = Field(default_factory=list)
