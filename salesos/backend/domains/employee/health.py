"""Observability — health checks, metrics, structured logging for Employee 360.

Exposes health status for all sub-services: calendar sync, email sync,
scoring engine, OAuth connections, background workers.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class EmployeeHealthChecker:
    """Health check for Employee 360 sub-services."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def full_check(self) -> dict[str, Any]:
        start = time.time()
        checks = {
            "database": await self._check_database(),
            "signals_table": await self._check_table("employee_signals"),
            "scores_table": await self._check_table("employee_scores"),
            "oauth_tokens_active": await self._check_oauth_active(),
            "calendar_events_recent": await self._check_calendar_recent(),
            "email_events_recent": await self._check_email_recent(),
        }
        status = "healthy"
        if any(c.get("status") == "unhealthy" for c in checks.values()):
            status = "degraded"
        if all(c.get("status") == "unhealthy" for c in checks.values()):
            status = "unhealthy"

        return {
            "service": "employee-360",
            "status": status,
            "latency_ms": round((time.time() - start) * 1000, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }

    async def readiness(self) -> bool:
        result = await self.full_check()
        return result["status"] != "unhealthy"

    async def liveness(self) -> bool:
        return True

    async def _check_database(self) -> dict:
        try:
            await self.db.execute(select(func.now()))
            return {"status": "healthy", "message": "Database connected"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_table(self, table_name: str) -> dict:
        try:
            count = (await self.db.execute(select(func.count()).select_from(
                __import__("sqlalchemy", fromlist=["text"]).text(table_name)
            ))).scalar()
            return {"status": "healthy", "row_count": count or 0, "table": table_name}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e), "table": table_name}

    async def _check_oauth_active(self) -> dict:
        try:
            from domains.employee.oauth_service import EmployeeOAuthToken
            now = datetime.now(timezone.utc)
            active = (await self.db.execute(
                select(func.count()).select_from(EmployeeOAuthToken).where(
                    EmployeeOAuthToken.is_active == True,
                    EmployeeOAuthToken.is_connected == True,
                )
            )).scalar() or 0
            expiring = (await self.db.execute(
                select(func.count()).select_from(EmployeeOAuthToken).where(
                    EmployeeOAuthToken.is_active == True,
                    EmployeeOAuthToken.access_token_expires_at <= now + timedelta(hours=1),
                )
            )).scalar() or 0
            return {
                "status": "healthy" if active > 0 else "degraded",
                "active_connections": active,
                "tokens_expiring_soon": expiring,
            }
        except Exception as e:
            return {"status": "degraded", "message": str(e)}

    async def _check_calendar_recent(self) -> dict:
        try:
            from domains.employee.intelligence_models import EmployeeCalendarEventModel
            hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent = (await self.db.execute(
                select(func.count()).select_from(EmployeeCalendarEventModel).where(
                    EmployeeCalendarEventModel.created_at >= hour_ago,
                )
            )).scalar() or 0
            return {
                "status": "healthy",
                "events_synced_last_hour": recent,
            }
        except Exception as e:
            return {"status": "degraded", "message": str(e)}

    async def _check_email_recent(self) -> dict:
        try:
            from domains.employee.intelligence_models import EmployeeEmailEventModel
            hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent = (await self.db.execute(
                select(func.count()).select_from(EmployeeEmailEventModel).where(
                    EmployeeEmailEventModel.created_at >= hour_ago,
                )
            )).scalar() or 0
            return {
                "status": "healthy",
                "emails_synced_last_hour": recent,
            }
        except Exception as e:
            return {"status": "degraded", "message": str(e)}
