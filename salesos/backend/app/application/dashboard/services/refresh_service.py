from datetime import UTC

from app.application.dashboard.dto.widget_contract import DashboardWidget


class RefreshService:
    @staticmethod
    def should_refresh(widget: DashboardWidget, stale_time_seconds: int = 60) -> bool:
        if widget.lastUpdated is None:
            return True
        from datetime import datetime

        elapsed = (datetime.now(UTC) - widget.lastUpdated).total_seconds()
        return elapsed > stale_time_seconds
