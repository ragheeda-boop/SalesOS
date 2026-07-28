"""Default engagement metric plugins for Activity Intelligence."""

from __future__ import annotations

from intelligence.activity_intelligence.engine.engagement_engine import (
    EngagementEngine,
    MetricContext,
    MetricPlugin,
    MetricValue,
)


class _EmailSentPlugin(MetricPlugin):
    id = "email_count_sent"
    label = "Emails Sent"
    category = "email"

    def __init__(self, email_engine):
        self._engine = email_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        value = await self._engine.get_count(ctx.company_id, ctx.tenant_id, "outbound")
        return MetricValue(plugin_id=self.id, value=value, unit="count", label=self.label)


class _EmailReceivedPlugin(MetricPlugin):
    id = "email_count_received"
    label = "Emails Received"
    category = "email"

    def __init__(self, email_engine):
        self._engine = email_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        value = await self._engine.get_count(ctx.company_id, ctx.tenant_id, "inbound")
        return MetricValue(plugin_id=self.id, value=value, unit="count", label=self.label)


class _ReplyRatePlugin(MetricPlugin):
    id = "reply_rate"
    label = "Reply Rate"
    category = "email"

    def __init__(self, email_engine):
        self._engine = email_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        value = await self._engine.get_reply_rate(ctx.company_id, ctx.tenant_id)
        return MetricValue(plugin_id=self.id, value=value, unit="percent", label=self.label)


class _MeetingCountPlugin(MetricPlugin):
    id = "meeting_count"
    label = "Meetings"
    category = "meeting"

    def __init__(self, calendar_engine):
        self._engine = calendar_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        value = await self._engine.get_count(ctx.company_id, ctx.tenant_id)
        return MetricValue(plugin_id=self.id, value=value, unit="count", label=self.label)


class _MeetingHoursPlugin(MetricPlugin):
    id = "meeting_hours"
    label = "Meeting Hours"
    category = "meeting"

    def __init__(self, calendar_engine):
        self._engine = calendar_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        value = await self._engine.get_meeting_hours(ctx.company_id, ctx.tenant_id)
        return MetricValue(plugin_id=self.id, value=value, unit="hours", label=self.label)


class _LastEmailPlugin(MetricPlugin):
    id = "last_email"
    label = "Days Since Last Email"
    category = "email"

    def __init__(self, email_engine):
        self._engine = email_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        metrics = await self._engine.get_email_metrics(ctx.company_id, ctx.tenant_id)
        return MetricValue(
            plugin_id=self.id,
            value=metrics.get("last_email_days"),
            unit="days",
            label=self.label,
        )


class _LastMeetingPlugin(MetricPlugin):
    id = "last_meeting"
    label = "Days Since Last Meeting"
    category = "meeting"

    def __init__(self, calendar_engine):
        self._engine = calendar_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        metrics = await self._engine.get_meeting_metrics(ctx.company_id, ctx.tenant_id)
        return MetricValue(
            plugin_id=self.id,
            value=metrics.get("last_meeting_days"),
            unit="days",
            label=self.label,
        )


class _LastActivityPlugin(MetricPlugin):
    id = "last_activity"
    label = "Days Since Last Activity"
    category = "communication"

    def __init__(self, email_engine, calendar_engine):
        self._email = email_engine
        self._calendar = calendar_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        email_m = await self._email.get_email_metrics(ctx.company_id, ctx.tenant_id)
        cal_m = await self._calendar.get_meeting_metrics(ctx.company_id, ctx.tenant_id)
        days = [
            d
            for d in (email_m.get("last_email_days"), cal_m.get("last_meeting_days"))
            if d is not None
        ]
        value = min(days) if days else None
        return MetricValue(plugin_id=self.id, value=value, unit="days", label=self.label)


class _CommunicationVelocityPlugin(MetricPlugin):
    id = "communication_velocity"
    label = "Communication Velocity"
    category = "communication"

    def __init__(self, email_engine, calendar_engine):
        self._email = email_engine
        self._calendar = calendar_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        sent = await self._email.get_count(ctx.company_id, ctx.tenant_id, "outbound")
        received = await self._email.get_count(ctx.company_id, ctx.tenant_id, "inbound")
        meetings = await self._calendar.get_count(ctx.company_id, ctx.tenant_id)
        value = float(sent + received + meetings)
        return MetricValue(plugin_id=self.id, value=value, unit="count", label=self.label)


class _MeetingCompletionPlugin(MetricPlugin):
    id = "meeting_completion_rate"
    label = "Meeting Completion Rate"
    category = "meeting"

    def __init__(self, calendar_engine):
        self._engine = calendar_engine

    async def compute(self, ctx: MetricContext) -> MetricValue:
        metrics = await self._engine.get_meeting_metrics(ctx.company_id, ctx.tenant_id)
        return MetricValue(
            plugin_id=self.id,
            value=metrics.get("meeting_completion_rate", 0.0),
            unit="percent",
            label=self.label,
        )


def register_default_plugins(engine: EngagementEngine) -> None:
    email = engine._email_engine
    calendar = engine._calendar_engine
    if not email or not calendar:
        return
    for plugin in (
        _EmailSentPlugin(email),
        _EmailReceivedPlugin(email),
        _ReplyRatePlugin(email),
        _MeetingCountPlugin(calendar),
        _MeetingHoursPlugin(calendar),
        _LastEmailPlugin(email),
        _LastMeetingPlugin(calendar),
        _LastActivityPlugin(email, calendar),
        _CommunicationVelocityPlugin(email, calendar),
        _MeetingCompletionPlugin(calendar),
    ):
        engine.register(plugin)
