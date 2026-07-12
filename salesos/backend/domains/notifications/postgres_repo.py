"""PostgreSQL repository for Notifications domain."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import NotificationModel
from .models import Notification, NotificationRepository


class PostgresNotificationRepository(NotificationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, notification: Notification) -> Notification:
        model = NotificationModel(
            notification_id=notification.id,
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            read=notification.read,
        )
        self.session.add(model)
        await self.session.flush()
        return notification

    async def get(self, notification_id: str, tenant_id: str) -> Optional[Notification]:
        stmt = select(NotificationModel).where(
            NotificationModel.notification_id == notification_id,
            NotificationModel.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_user(self, tenant_id: str, user_id: str, limit: int = 50) -> list[Notification]:
        stmt = (
            select(NotificationModel)
            .where(
                NotificationModel.tenant_id == tenant_id,
                NotificationModel.user_id == user_id,
            )
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def mark_read(self, notification_id: str, tenant_id: str, user_id: str) -> bool:
        stmt = (
            select(NotificationModel)
            .where(
                NotificationModel.notification_id == notification_id,
                NotificationModel.tenant_id == tenant_id,
                NotificationModel.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return False
        model.read = True
        await self.session.flush()
        return True

    async def mark_all_read(self, tenant_id: str, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(NotificationModel)
            .where(
                NotificationModel.tenant_id == tenant_id,
                NotificationModel.user_id == user_id,
                NotificationModel.read == False,
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        if count > 0:
            await self.session.execute(
                update(NotificationModel)
                .where(
                    NotificationModel.tenant_id == tenant_id,
                    NotificationModel.user_id == user_id,
                    NotificationModel.read == False,
                )
                .values(read=True)
            )
            await self.session.flush()
        return count

    async def count_unread(self, tenant_id: str, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(NotificationModel)
            .where(
                NotificationModel.tenant_id == tenant_id,
                NotificationModel.user_id == user_id,
                NotificationModel.read == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    def _to_domain(self, model: NotificationModel) -> Notification:
        from .models import Notification as N
        return N(
            id=model.notification_id,
            tenant_id=model.tenant_id,
            user_id=model.user_id,
            type=model.type,
            title=model.title,
            body=model.body,
            data=model.data or {},
            read=model.read,
            created_at=model.created_at,
        )
