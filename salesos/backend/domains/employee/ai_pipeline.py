"""AI Pipeline for Employee 360 — meeting summaries, email analysis, coaching.

Integrates with SalesOS AI provider (OpenAI, Anthropic, Azure, Ollama, Gemini).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import User
from domains.employee.db_models import EmployeeSignalModel, EmployeeScoreModel
from domains.employee.intelligence_models import EmployeeCalendarEventModel, EmployeeEmailEventModel


class EmployeeAIPipeline:
    """AI-powered intelligence pipeline for Employee 360.

    Uses SalesOS AI provider for:
      - Meeting summaries
      - Email summaries & sentiment
      - Action item extraction
      - Weekly digest generation
      - Personalized coaching
    """

    def __init__(self, db: AsyncSession, ai_provider: Any = None):
        self.db = db
        self._ai = ai_provider
        self._model = "gpt-4o-mini"

    async def generate_meeting_summary(self, event_id: str) -> dict:
        """Generate AI summary for a single meeting."""
        event = (await self.db.execute(
            select(EmployeeCalendarEventModel).where(EmployeeCalendarEventModel.id == uuid.UUID(event_id))
        )).scalar_one_or_none()
        if not event or not event.description_md:
            return {"summary": "", "action_items": [], "sentiment": "neutral"}

        prompt = f"""Summarize this meeting in 2-3 sentences. Extract action items.
Meeting title: {event.title or 'Untitled'}
Description: {event.description_md[:2000]}

Respond as JSON: {{"summary": "...", "action_items": ["..."], "sentiment": "positive|neutral|negative"}}"""

        result = await self._call_ai(prompt)
        try:
            parsed = json.loads(result)
            return {"summary": parsed.get("summary", ""), "action_items": parsed.get("action_items", []), "sentiment": parsed.get("sentiment", "neutral")}
        except json.JSONDecodeError:
            return {"summary": result[:500], "action_items": [], "sentiment": "neutral"}

    async def generate_email_summary(self, event_id: str) -> dict:
        """Generate AI summary + sentiment for an email."""
        email = (await self.db.execute(
            select(EmployeeEmailEventModel).where(EmployeeEmailEventModel.id == uuid.UUID(event_id))
        )).scalar_one_or_none()
        if not email:
            return {"summary": "", "sentiment": "neutral", "action_items": []}

        prompt = f"""Analyze this email. Provide summary, sentiment, and action items if any.
Subject: {email.subject or 'No subject'}
Body preview: {email.snippet or ''} {email.body_preview or ''}

Respond as JSON: {{"summary": "...", "sentiment": "positive|neutral|negative", "action_items": ["..."]}}"""

        result = await self._call_ai(prompt)
        try:
            parsed = json.loads(result)
            return {"summary": parsed.get("summary", ""), "sentiment": parsed.get("sentiment", "neutral"), "action_items": parsed.get("action_items", [])}
        except json.JSONDecodeError:
            return {"summary": result[:500], "sentiment": "neutral", "action_items": []}

    async def generate_weekly_digest(self, employee_id: str, tenant_id: str) -> dict:
        """Generate a weekly performance digest for an employee."""
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Gather metrics
        signal_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid,
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= week_ago,
            )
        )).scalar() or 0

        meetings = (await self.db.execute(
            select(func.count()).select_from(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.employee_id == eid,
                EmployeeCalendarEventModel.tenant_id == tid,
                EmployeeCalendarEventModel.is_cancelled == False,
                EmployeeCalendarEventModel.start_utc >= week_ago,
            )
        )).scalar() or 0

        emails = (await self.db.execute(
            select(func.count()).select_from(EmployeeEmailEventModel).where(
                EmployeeEmailEventModel.employee_id == eid,
                EmployeeEmailEventModel.tenant_id == tid,
                EmployeeEmailEventModel.timestamp_utc >= week_ago,
            )
        )).scalar() or 0

        latest_score = (await self.db.execute(
            select(EmployeeScoreModel).where(
                EmployeeScoreModel.employee_id == eid,
                EmployeeScoreModel.tenant_id == tid,
            ).order_by(desc(EmployeeScoreModel.generated_at)).limit(1)
        )).scalar_one_or_none()

        score_val = round((latest_score.overall_score or 0) * 100, 1) if latest_score else 0

        user = (await self.db.execute(
            select(User).where(User.id == eid, User.tenant_id == tid)
        )).scalar_one_or_none()
        name = user.full_name if user else "Employee"

        prompt = f"""Write a concise weekly performance digest for {name}.
This week: {signal_count} activities, {meetings} meetings, {emails} emails. Score: {score_val}/100.

Provide 2-3 specific coaching tips in Arabic. Keep it encouraging and actionable.
Respond as JSON: {{"title": "...", "summary": "...", "strengths": ["..."], "improvements": ["..."], "coaching_tips_ar": ["..."]}}"""

        result = await self._call_ai(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"title": f"Weekly Digest for {name}", "summary": result[:500], "strengths": [], "improvements": [], "coaching_tips_ar": []}

    async def generate_executive_brief(self, tenant_id: str) -> dict:
        """Generate executive AI brief summarizing organization-wide trends."""
        tid = uuid.UUID(tenant_id)
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)

        total_users = (await self.db.execute(
            select(func.count()).select_from(User).where(
                User.tenant_id == tid, User.deleted_at.is_(None),
            )
        )).scalar() or 0

        total_signals = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= month_ago,
            )
        )).scalar() or 0

        avg_score = (await self.db.execute(
            select(func.avg(EmployeeScoreModel.overall_score)).where(
                EmployeeScoreModel.tenant_id == tid,
            )
        )).scalar() or 0

        at_risk = (await self.db.execute(
            select(func.count()).select_from(EmployeeScoreModel).where(
                EmployeeScoreModel.tenant_id == tid,
                EmployeeScoreModel.overall_score < 0.4,
            )
        )).scalar() or 0

        prompt = f"""Write an executive AI brief in Arabic for a sales organization.
Organization: {total_users} employees, {total_signals} activities this month.
Average score: {round(avg_score * 100, 1)}/100. At-risk employees: {at_risk}.

Provide: overall assessment, 2-3 key trends, 2-3 actionable recommendations.
Respond as JSON: {{"title_ar": "...", "assessment_ar": "...", "trends_ar": ["..."], "recommendations_ar": ["..."], "risk_level": "low|medium|high"}}"""

        result = await self._call_ai(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"title_ar": "الموجز التنفيذي", "assessment_ar": result[:500], "trends_ar": [], "recommendations_ar": [], "risk_level": "medium"}

    async def generate_coaching_insight(self, employee_id: str, tenant_id: str) -> dict:
        """Generate personalized coaching insight using AI."""
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)

        signal_count = (await self.db.execute(
            select(func.count()).select_from(EmployeeSignalModel).where(
                EmployeeSignalModel.employee_id == eid, EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= month_ago,
            )
        )).scalar() or 0

        signal_types = (await self.db.execute(
            select(EmployeeSignalModel.signal_type, func.count()).where(
                EmployeeSignalModel.employee_id == eid, EmployeeSignalModel.tenant_id == tid,
                EmployeeSignalModel.timestamp >= month_ago,
            ).group_by(EmployeeSignalModel.signal_type).order_by(desc(func.count())).limit(5)
        )).fetchall()

        type_summary = ", ".join(f"{t}: {c}" for t, c in signal_types)

        user = (await self.db.execute(select(User).where(User.id == eid))).scalar_one_or_none()
        name = user.full_name if user else "Employee"

        prompt = f"""Provide personalized sales coaching advice for {name} in Arabic.
Last 30 days: {signal_count} activities. Activity breakdown: {type_summary}.
Identify 2-3 specific, actionable improvements. Be encouraging but honest.
Respond as JSON: {{"focus_area_ar": "...", "advice_ar": ["..."], "motivation_ar": "..."}}"""

        result = await self._call_ai(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"focus_area_ar": "تحسين الأداء", "advice_ar": ["استمر في النشاط اليومي"], "motivation_ar": result[:300]}

    async def _call_ai(self, prompt: str) -> str:
        """Call SalesOS AI provider with fallback chain."""
        if not self._ai:
            return "{}"
        try:
            response = await self._ai.complete(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            return response.get("content", "{}")
        except Exception:
            try:
                response = await self._ai.complete(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500,
                )
                return response.get("content", "{}")
            except Exception:
                return "{}"
