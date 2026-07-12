from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from .models import TelemetryEvent


EVENT_TYPES = frozenset({
    "page_view", "search_query", "nba_view", "nba_accept", "nba_reject",
    "workflow_run", "workflow_complete", "rag_query", "report_run", "api_call",
    "login", "logout",
})


class TelemetryRepository(ABC):
    @abstractmethod
    async def create(self, event: TelemetryEvent) -> TelemetryEvent: ...

    @abstractmethod
    async def query(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[list[TelemetryEvent], int]: ...

    @abstractmethod
    async def aggregate(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        granularity: str = "day",
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_all_events(self, tenant_id: str) -> list[TelemetryEvent]: ...

    @abstractmethod
    async def get_all_events_in_range(
        self,
        tenant_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[TelemetryEvent]: ...


class InMemoryTelemetryRepository(TelemetryRepository):
    def __init__(self):
        self._events: list[TelemetryEvent] = []
        self._counter = 0

    async def create(self, event: TelemetryEvent) -> TelemetryEvent:
        self._counter += 1
        event.id = self._counter
        self._events.append(event)
        return event

    async def query(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[list[TelemetryEvent], int]:
        filtered = [e for e in self._events if e.tenant_id == tenant_id]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if from_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp >= from_date]
        if to_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp <= to_date]
        filtered.sort(key=lambda e: e.timestamp or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        total = len(filtered)
        return filtered[offset:offset + limit], total

    async def aggregate(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        granularity: str = "day",
    ) -> list[dict[str, Any]]:
        filtered = [e for e in self._events if e.tenant_id == tenant_id]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if from_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp >= from_date]
        if to_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp <= to_date]

        buckets: dict[str, int] = {}
        for e in filtered:
            ts = e.timestamp
            if not ts:
                continue
            if granularity == "hour":
                key = ts.strftime("%Y-%m-%dT%H:00:00")
            elif granularity == "day":
                key = ts.strftime("%Y-%m-%d")
            elif granularity == "week":
                iso = ts.isocalendar()
                key = f"{iso[0]}-W{iso[1]:02d}"
            elif granularity == "month":
                key = ts.strftime("%Y-%m")
            else:
                key = ts.strftime("%Y-%m-%d")
            buckets[key] = buckets.get(key, 0) + 1

        result = [{"period": k, "count": v} for k, v in sorted(buckets.items())]
        return result

    async def get_all_events(self, tenant_id: str) -> list[TelemetryEvent]:
        return [e for e in self._events if e.tenant_id == tenant_id]

    async def get_all_events_in_range(
        self,
        tenant_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[TelemetryEvent]:
        filtered = self._events
        if tenant_id is not None:
            filtered = [e for e in filtered if e.tenant_id == tenant_id]
        if from_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp >= from_date]
        if to_date:
            filtered = [e for e in filtered if e.timestamp and e.timestamp <= to_date]
        return filtered


class TelemetryService:
    def __init__(self, repository: TelemetryRepository):
        self.repository = repository

    async def track(
        self,
        event_type: str,
        tenant_id: str,
        user_id: str,
        properties: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            event_type=event_type,
            tenant_id=tenant_id,
            user_id=user_id,
            properties=properties or {},
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        return await self.repository.create(event)

    async def query(
        self,
        tenant_id: str,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        granularity: str = "day",
    ) -> list[dict[str, Any]]:
        return await self.repository.aggregate(tenant_id, event_type, from_date, to_date, granularity)

    async def feature_adoption(
        self,
        tenant_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        events = await self.repository.get_all_events(tenant_id)
        if from_date:
            events = [e for e in events if e.timestamp and e.timestamp >= from_date]
        if to_date:
            events = [e for e in events if e.timestamp and e.timestamp <= to_date]

        counts: dict[str, set[str]] = defaultdict(set)
        type_labels = {
            "page_view": "صفحات العرض",
            "search_query": "البحث",
            "nba_view": "توصيات NBA",
            "nba_accept": "قبول NBA",
            "nba_reject": "رفض NBA",
            "workflow_run": "تشغيل سير العمل",
            "workflow_complete": "إكمال سير العمل",
            "rag_query": "استعلام RAG",
            "report_run": "تقارير",
            "api_call": "استدعاءات API",
            "login": "تسجيل دخول",
        }

        for e in events:
            if e.event_type in type_labels:
                counts[e.event_type].add(e.user_id)

        total_users = len(set(e.user_id for e in events))
        result = []
        for etype, label in type_labels.items():
            user_count = len(counts.get(etype, set()))
            pct = round(user_count / total_users * 100, 1) if total_users > 0 else 0.0
            result.append({
                "feature": etype,
                "label": label,
                "user_count": user_count,
                "total_users": total_users,
                "adoption_pct": pct,
            })
        return sorted(result, key=lambda x: x["adoption_pct"], reverse=True)

    async def search_success_rate(self, tenant_id: str) -> dict[str, Any]:
        events = await self.repository.get_all_events(tenant_id)
        searches = [e for e in events if e.event_type == "search_query"]
        total_searches = len(searches)
        searches_with_action = sum(
            1 for e in searches
            if e.properties and (e.properties.get("clicked") is True or e.properties.get("result_clicked") is True)
        )
        rate = round(searches_with_action / total_searches * 100, 1) if total_searches > 0 else 0.0
        return {
            "total_searches": total_searches,
            "searches_with_action": searches_with_action,
            "success_rate": rate,
        }

    async def nba_acceptance_rate(self, tenant_id: str) -> dict[str, Any]:
        events = await self.repository.get_all_events(tenant_id)
        views = [e for e in events if e.event_type == "nba_view"]
        accepts = [e for e in events if e.event_type == "nba_accept"]
        rejects = [e for e in events if e.event_type == "nba_reject"]
        total_decisions = len(accepts) + len(rejects)
        rate = round(len(accepts) / total_decisions * 100, 1) if total_decisions > 0 else 0.0
        return {
            "nba_views": len(views),
            "nba_accepts": len(accepts),
            "nba_rejects": len(rejects),
            "acceptance_rate": rate,
        }

    async def time_to_insight(self, tenant_id: str) -> dict[str, Any]:
        events = await self.repository.get_all_events(tenant_id)
        user_logins: dict[str, datetime] = {}
        user_first_action: dict[str, datetime] = {}

        for e in sorted(events, key=lambda x: x.timestamp or datetime.min.replace(tzinfo=timezone.utc)):
            if not e.timestamp:
                continue
            if e.event_type == "login":
                if e.user_id not in user_logins:
                    user_logins[e.user_id] = e.timestamp
            elif e.event_type in ("search_query", "nba_view", "workflow_run", "rag_query", "report_run"):
                if e.user_id not in user_first_action and e.user_id in user_logins:
                    user_first_action[e.user_id] = e.timestamp

        times = []
        for uid in user_first_action:
            delta = (user_first_action[uid] - user_logins[uid]).total_seconds()
            times.append(delta)

        avg_seconds = round(sum(times) / len(times), 1) if times else 0.0
        return {
            "users_with_insight": len(user_first_action),
            "total_logins": len(user_logins),
            "avg_time_to_insight_seconds": avg_seconds,
            "avg_time_to_insight_display": self._format_duration(avg_seconds),
        }

    async def time_to_action(self, tenant_id: str) -> dict[str, Any]:
        events = await self.repository.get_all_events(tenant_id)
        user_nba_view: dict[str, datetime] = {}
        user_nba_accept: dict[str, datetime] = {}

        for e in sorted(events, key=lambda x: x.timestamp or datetime.min.replace(tzinfo=timezone.utc)):
            if not e.timestamp:
                continue
            if e.event_type == "nba_view":
                if e.user_id not in user_nba_view:
                    user_nba_view[e.user_id] = e.timestamp
            elif e.event_type == "nba_accept":
                if e.user_id not in user_nba_accept and e.user_id in user_nba_view:
                    user_nba_accept[e.user_id] = e.timestamp

        times = []
        for uid in user_nba_accept:
            delta = (user_nba_accept[uid] - user_nba_view[uid]).total_seconds()
            times.append(delta)

        avg_seconds = round(sum(times) / len(times), 1) if times else 0.0
        return {
            "users_with_action": len(user_nba_accept),
            "users_with_view": len(user_nba_view),
            "avg_time_to_action_seconds": avg_seconds,
            "avg_time_to_action_display": self._format_duration(avg_seconds),
        }

    async def active_users(self, days: int = 7) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        dau_cutoff = now - timedelta(days=1)
        wau_cutoff = now - timedelta(days=7)
        mau_cutoff = now - timedelta(days=30)

        daily: set[str] = set()
        weekly: set[str] = set()
        monthly: set[str] = set()

        all_events = await self.repository.get_all_events_in_range(
            to_date=now,
        )
        for e in all_events:
            if not e.timestamp:
                continue
            if e.timestamp >= dau_cutoff:
                daily.add(e.user_id)
            if e.timestamp >= wau_cutoff:
                weekly.add(e.user_id)
            if e.timestamp >= mau_cutoff:
                monthly.add(e.user_id)

        return {
            "dau": len(daily),
            "wau": len(weekly),
            "mau": len(monthly),
            "period_days": days,
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)}m {int(seconds % 60)}s"
        hours = minutes / 60
        return f"{int(hours)}h {int(minutes % 60)}m"
