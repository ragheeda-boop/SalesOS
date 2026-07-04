"""ActivityService — business logic for managing activity sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import (
    Activity,
    ActivityOutcome,
    ActivitySession,
    ActivityStatus,
    ActivityType,
)
from ..contracts.outcome_catalog import OutcomeCatalog
from ..contracts.repository import ActivityRepository, ActivitySessionQuery
from .rule_engine import ActivityRuleEngine


class ActivityService:

    def __init__(
        self,
        repository: ActivityRepository,
        rule_engine: ActivityRuleEngine | None = None,
        event_bus: Any = None,
    ):
        self._repository = repository
        self._rule_engine = rule_engine or ActivityRuleEngine()
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id,
                            aggregate_id=data.get("session_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    # ── Session Management ──

    async def create_session(
        self,
        tenant_id: str,
        title: str,
        target_id: str,
        target_type: str = "opportunity",
    ) -> ActivitySession:
        session = ActivitySession(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            target_id=target_id,
            target_type=target_type,
        )
        result = await self._repository.save_session(session)
        await self._emit("activity.session_created", tenant_id, {
            "session_id": session.id, "title": title,
            "target_id": target_id, "target_type": target_type,
        })
        return result

    async def get_session(self, session_id: str) -> ActivitySession | None:
        return await self._repository.get_session(session_id)

    async def query_sessions(self, query: ActivitySessionQuery) -> list[ActivitySession]:
        return await self._repository.query_sessions(query)

    async def count_sessions(self, query: ActivitySessionQuery) -> int:
        return await self._repository.count_sessions(query)

    # ── Activity Management ──

    async def add_activity(
        self,
        session_id: str,
        activity_type: ActivityType,
        owner_id: str,
        owner_name: str = "",
        scheduled_at: datetime | None = None,
    ) -> Activity:
        session = await self._repository.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        activity = Activity(
            id=str(uuid.uuid4()),
            activity_type=activity_type,
            owner_id=owner_id,
            owner_name=owner_name,
            scheduled_at=scheduled_at or datetime.now(timezone.utc),
        )
        session.activities.append(activity)
        session.updated_at = datetime.now(timezone.utc)
        await self._repository.save_session(session)
        return activity

    async def complete_activity(
        self,
        session_id: str,
        activity_id: str,
        outcome_id: str,
        notes: str = "",
    ) -> ActivityOutcome:
        """Complete an activity with an outcome. Triggers Rule Engine."""
        session = await self._repository.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        activity = next((a for a in session.activities if a.id == activity_id), None)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found in session {session_id}")

        if activity.is_completed:
            raise ValueError(f"Activity {activity_id} is already completed")

        outcome_def = OutcomeCatalog.get(outcome_id)
        if not outcome_def:
            raise ValueError(f"Outcome '{outcome_id}' not found in catalog")

        # Complete the activity
        activity.outcome_id = outcome_id
        activity.outcome_label = outcome_def.label_ar
        activity.notes = notes
        activity.status = ActivityStatus.COMPLETED
        activity.completed_at = datetime.now(timezone.utc)

        # Create outcome event for the Rule Engine
        outcome = ActivityOutcome(
            activity_id=activity_id,
            session_id=session_id,
            activity_type=activity.activity_type,
            outcome_id=outcome_id,
            outcome_label=outcome_def.label_ar,
            business_action=outcome_def.business_action,
            action_params=outcome_def.action_params,
            target_id=session.target_id,
            target_type=session.target_type,
            owner_id=activity.owner_id,
            completed_at=activity.completed_at,
        )

        session.updated_at = datetime.now(timezone.utc)
        await self._repository.save_session(session)

        # Emit event
        await self._emit("activity.completed", session.tenant_id, {
            "session_id": session_id, "activity_id": activity_id,
            "outcome_id": outcome_id, "business_action": outcome_def.business_action,
            "target_id": session.target_id, "target_type": session.target_type,
        })

        # Evaluate rules
        if self._rule_engine:
            triggered = await self._rule_engine.evaluate(outcome)
            if triggered:
                await self._emit("activity.rule_triggered", session.tenant_id, {
                    "session_id": session_id, "actions": triggered,
                })

        return outcome

    # ── KPIs ──

    async def kpi_summary(self, tenant_id: str) -> dict[str, Any]:
        return await self._repository.kpi_summary(tenant_id)

    async def get_activities_by_target(self, target_id: str, target_type: str, limit: int = 50) -> list[Activity]:
        return await self._repository.get_activities_by_target(target_id, target_type, limit)
