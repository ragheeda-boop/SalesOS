import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from app.application.dashboard.dto.widget_contract import DashboardWidget, WidgetAction
from app.application.dashboard.dto.widget_state import WidgetStatus


class SourceReader:
    def __init__(self, widget_id: str, title: str, timeout: float = 0.5):
        self.widget_id = widget_id
        self.title = title
        self.timeout = timeout

    async def read(self, fetcher: Callable[[], Any]) -> DashboardWidget:
        _ = datetime.now(UTC)
        try:
            data = await asyncio.wait_for(fetcher(), timeout=self.timeout)
            return DashboardWidget(
                id=self.widget_id,
                title=self.title,
                status=WidgetStatus.ready,
                lastUpdated=datetime.now(UTC),
                data=data.model_dump() if hasattr(data, "model_dump") else data,
                actions=self._default_actions(),
            )
        except TimeoutError:
            return DashboardWidget(
                id=self.widget_id,
                title=self.title,
                status=WidgetStatus.degraded,
                lastUpdated=None,
                data=None,
                actions=self._default_actions(),
            )
        except Exception:
            return DashboardWidget(
                id=self.widget_id,
                title=self.title,
                status=WidgetStatus.error,
                lastUpdated=None,
                data=None,
                actions=self._default_actions(),
            )

    def _default_actions(self) -> list[WidgetAction]:
        return [
            WidgetAction(id=f"{self.widget_id}.refresh", label="Refresh", type="refresh"),
        ]
