"""Executive Dashboard — aggregate employee metrics for leadership."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import User
from domains.employee.db_models import EmployeeSignalModel, EmployeeScoreModel


class ExecutiveDashboardService:
    """Computes aggregate employee metrics for the executive cockpit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, tenant_id: str) -> dict[str, Any]:
        tid = uuid.UUID(tenant_id)
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # Headcount
        total_employees = (await self.db.execute(
            select(func.count()).select_from(User).where(
                User.tenant_id == tid,
                User.deleted_at.is_(None),
            )
        )).scalar() or 0

        active_employees = (await self.db.execute(
            select(func.count()).select_from(User).where(
                User.tenant_id == tid,
                User.is_active == True,
                User.deleted_at.is_(None),
            )
        )).scalar() or 0

        # Department breakdown
        dept_result = await self.db.execute(
            select(User.department, func.count()).where(
                User.tenant_id == tid,
                User.is_active == True,
                User.deleted_at.is_(None),
            ).group_by(User.department).order_by(func.count().desc())
        )
        departments = [
            {"name": row[0] or "Unassigned", "headcount": row[1]}
            for row in dept_result.fetchall()
        ]

        # Role breakdown
        role_result = await self.db.execute(
            select(User.role, func.count()).where(
                User.tenant_id == tid,
                User.is_active == True,
                User.deleted_at.is_(None),
            ).group_by(User.role).order_by(func.count().desc())
        )
        roles = [
            {"role": row[0], "count": row[1]}
            for row in role_result.fetchall()
        ]

        # Average score across all employees
        avg_score_result = (await self.db.execute(
            select(func.avg(EmployeeScoreModel.overall_score)).where(
                EmployeeScoreModel.tenant_id == tid,
            )
        )).scalar()
        avg_score = round((avg_score_result or 0) * 100, 1)

        # Total signals last 30 days
        total_signals = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= thirty_days_ago,
            )
        )).scalar() or 0

        # Top performers (top 10 by score)
        top_performers_result = await self.db.execute(
            select(
                User.id, User.full_name, User.department, User.role,
                EmployeeScoreModel.overall_score,
            ).join(
                EmployeeScoreModel,
                and_(
                    User.id == EmployeeScoreModel.employee_id,
                    EmployeeScoreModel.tenant_id == tid,
                ),
                isouter=True,
            ).where(
                User.tenant_id == tid,
                User.is_active == True,
                User.deleted_at.is_(None),
            ).order_by(EmployeeScoreModel.overall_score.desc().nulls_last()).limit(10)
        )
        top_performers = [
            {
                "id": str(r[0]), "name": r[1], "department": r[2], "role": r[3],
                "score": round((r[4] or 0) * 100, 1),
            }
            for r in top_performers_result.fetchall()
        ]

        # Risk summary
        at_risk_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeScoreModel).where(
                EmployeeScoreModel.tenant_id == tid,
                EmployeeScoreModel.overall_score < 0.4,
            )
        )).scalar() or 0

        # New employees this month
        new_this_month = (await self.db.execute(
            select(func.count()).select_from(User).where(
                User.tenant_id == tid,
                User.deleted_at.is_(None),
                User.created_at >= thirty_days_ago,
            )
        )).scalar() or 0

        return {
            "total_employees": total_employees,
            "active_employees": active_employees,
            "new_this_month": new_this_month,
            "avg_score": avg_score,
            "total_signals_30d": total_signals,
            "at_risk_count": at_risk_count,
            "departments": departments,
            "roles": roles,
            "top_performers": top_performers,
            "generated_at": now.isoformat(),
        }
