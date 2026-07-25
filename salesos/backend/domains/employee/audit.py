"""Employee-specific audit logging.

Wraps the existing app.modules.audit.AuditService to record:
  - Employee 360 page views (who viewed whom)
  - Employee mutations (bulk edit, bulk delete, score compute)
  - Signal collection events

Follows the established audit_logs table + PostgresAuditRepository pattern.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.audit.service import AuditService, PostgresAuditRepository


class EmployeeAuditLogger:
    """Lightweight audit logger for employee domain operations.

    Usage as FastAPI dependency:
        audit = EmployeeAuditLogger(db)
        await audit.log_view(employee_id, viewer_id, tenant_id)
    """

    def __init__(self, db: AsyncSession):
        self._service = AuditService(PostgresAuditRepository(db))

    async def log_view(
        self,
        employee_id: str,
        viewer_id: str,
        tenant_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        return await self._service.log(
            tenant_id=tenant_id,
            user_id=viewer_id,
            action="employee.viewed",
            resource_type="employee",
            resource_id=employee_id,
            details={"viewer_id": viewer_id},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_collect_signals(
        self,
        employee_id: str,
        collected_count: int,
        triggered_by: str,
        tenant_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        return await self._service.log(
            tenant_id=tenant_id,
            user_id=triggered_by,
            action="employee.signals_collected",
            resource_type="employee",
            resource_id=employee_id,
            details={"collected_count": collected_count, "triggered_by": triggered_by},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_score_compute(
        self,
        employee_id: str,
        score: float,
        triggered_by: str,
        tenant_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        return await self._service.log(
            tenant_id=tenant_id,
            user_id=triggered_by,
            action="employee.score_computed",
            resource_type="employee",
            resource_id=employee_id,
            details={"score": score, "triggered_by": triggered_by},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_bulk_edit(
        self,
        employee_ids: list[str],
        updates: dict[str, Any],
        triggered_by: str,
        tenant_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        return await self._service.log(
            tenant_id=tenant_id,
            user_id=triggered_by,
            action="employee.bulk_edited",
            resource_type="employee",
            resource_id=",".join(employee_ids[:10]),
            details={
                "employee_ids": employee_ids,
                "count": len(employee_ids),
                "updates": updates,
                "triggered_by": triggered_by,
            },
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_bulk_delete(
        self,
        employee_ids: list[str],
        triggered_by: str,
        tenant_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        return await self._service.log(
            tenant_id=tenant_id,
            user_id=triggered_by,
            action="employee.bulk_deleted",
            resource_type="employee",
            resource_id=",".join(employee_ids[:10]),
            details={
                "employee_ids": employee_ids,
                "count": len(employee_ids),
                "triggered_by": triggered_by,
            },
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_export(
        self,
        fields: list[str],
        employee_ids: list[str] | None,
        triggered_by: str,
        tenant_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        return await self._service.log(
            tenant_id=tenant_id,
            user_id=triggered_by,
            action="employee.exported",
            resource_type="employee",
            resource_id=None,
            details={
                "fields": fields,
                "employee_ids": employee_ids,
                "count": len(employee_ids) if employee_ids else "all",
                "triggered_by": triggered_by,
            },
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
