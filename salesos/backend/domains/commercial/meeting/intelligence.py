"""Meeting Intelligence — pre-meeting brief, post-meeting summary, action extraction."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sa_text


class MeetingIntelligenceService:
    """Generates pre-meeting intelligence and post-meeting summaries."""

    def __init__(self, db: AsyncSession, tenant_id: str, llm_service: Any = None):
        self.db = db
        self.tenant_id = tenant_id
        self._llm = llm_service

    async def generate_brief(self, opportunity_id: str, company_id: str) -> dict[str, Any]:
        """Generate pre-meeting intelligence brief."""
        # Company info
        company = await self.db.execute(
            sa_text("SELECT name_ar, name_en, industry, city, activity_description FROM companies WHERE id::text = :cid"),
            {"cid": company_id},
        )
        co = company.mappings().one_or_none()
        company_name = co["name_ar"] if co else ""

        # Recent signals
        signals = await self.db.execute(
            sa_text("""
                SELECT title, description, created_at FROM company_signals
                WHERE company_id = (SELECT company_id FROM commercial_opportunities WHERE id = :oid)
                ORDER BY created_at DESC LIMIT 5
            """),
            {"oid": opportunity_id},
        )
        recent_signals = [
            f"{s['title']}: {s['description'][:100]}" if s["description"] else s["title"]
            for s in signals.mappings().all()
        ]

        # Key contacts
        contacts = await self.db.execute(
            sa_text("SELECT name, position FROM contacts_standalone WHERE company_id = :cid AND tenant_id = :tid LIMIT 5"),
            {"cid": company_id, "tid": self.tenant_id},
        )
        key_contacts = [f"{c['name']} ({c['position'] or ''})" for c in contacts.mappings().all()]

        # Opportunity info
        opp = await self.db.execute(
            sa_text("SELECT name, stage, value FROM commercial_opportunities WHERE id = :oid"),
            {"oid": opportunity_id},
        )
        op = opp.mappings().one_or_none()

        brief = {
            "company_name": company_name,
            "opportunity_name": op["name"] if op else "",
            "opportunity_stage": op["stage"] if op else "",
            "opportunity_value": float(op["value"]) if op else 0,
            "recent_signals": recent_signals,
            "key_contacts": key_contacts,
            "talking_points": self._generate_talking_points(company_name, op["stage"] if op else ""),
            "questions_to_ask": self._generate_questions(op["stage"] if op else ""),
        }

        # AI-enhanced brief if LLM available
        if self._llm:
            try:
                ai_brief = await self._llm.chat([{
                    "role": "system",
                    "content": "Generate a pre-meeting brief in Arabic. Include: company overview, talking points, key questions.",
                }, {
                    "role": "user",
                    "content": f"Company: {company_name}, Opportunity: {brief['opportunity_name']}, Stage: {brief['opportunity_stage']}",
                }])
                brief["ai_summary"] = ai_brief
            except Exception:
                pass

        return brief

    async def generate_summary(self, meeting_data: dict[str, Any]) -> dict[str, Any]:
        """Generate post-meeting summary and extract action items."""
        notes = meeting_data.get("notes", "")
        summary = {
            "key_topics": self._extract_topics(notes),
            "action_items": self._extract_action_items(notes),
            "sentiment": self._analyze_sentiment(notes),
            "follow_up_email_draft": "",
        }

        if self._llm and notes:
            try:
                ai_summary = await self._llm.chat([{
                    "role": "system",
                    "content": "Summarize meeting notes in Arabic. Extract action items, decisions, and follow-ups.",
                }, {
                    "role": "user", "content": notes,
                }])
                summary["ai_summary"] = ai_summary
            except Exception:
                pass

        return summary

    def _generate_talking_points(self, company_name: str, stage: str) -> list[str]:
        points = [
            f"فهم احتياجات {company_name} الحالية والتحديات",
        ]
        if stage == "qualification":
            points.append("تأهيل الفرصة: الميزانية، الجدول الزمني، صانع القرار")
        elif stage == "proposal":
            points.append("مراجعة عرض السعر ومناقشة البنود")
        elif stage == "negotiation":
            points.append("التفاوض على الشروط والسعر النهائي")
        return points

    def _generate_questions(self, stage: str) -> list[str]:
        questions = ["ما هي أكبر التحديات التي تواجهكم حاليًا؟"]
        if stage == "qualification":
            questions.append("ما هي ميزانيتكم التقريبية لهذا المشروع؟")
            questions.append("من هم أصحاب القرار في هذه العملية؟")
        elif stage == "proposal":
            questions.append("هل هناك أي استفسارات حول عرض السعر؟")
        return questions

    def _extract_topics(self, notes: str) -> list[str]:
        if not notes:
            return []
        lines = [l.strip() for l in notes.split("\n") if l.strip()]
        return [l for l in lines if len(l) > 20][:5]

    def _extract_action_items(self, notes: str) -> list[str]:
        if not notes:
            return []
        items = []
        for line in notes.split("\n"):
            if any(marker in line for marker in ["action:", "Action:", "متابعة:", "إجراء:", "- [ ]", "* [ ]"]):
                items.append(line.strip())
        return items[:5]

    def _analyze_sentiment(self, notes: str) -> str:
        if not notes:
            return "neutral"
        positive_words = ["موافق", "ممتاز", "نعم", "اتفاق", "شراكة"]
        negative_words = ["لا", "مشكلة", "صعوبة", "ميزانية", "غالي"]
        pos_count = sum(1 for w in positive_words if w in notes)
        neg_count = sum(1 for w in negative_words if w in notes)
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
