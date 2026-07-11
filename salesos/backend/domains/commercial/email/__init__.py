"""Email Intelligence — sentiment analysis, topic extraction, action detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Email:
    id: str
    tenant_id: str
    opportunity_id: str
    subject: str
    from_address: str
    to_addresses: list[str] = field(default_factory=list)
    body: str = ""
    sent_at: datetime | None = None
    direction: str = "outbound"  # outbound | inbound
    email_type: str = "general"  # general | follow_up | proposal | meeting
    intelligence: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EmailIntelligence:
    """Analyzes email content for sentiment, topics, and action items."""

    def analyze(self, email: Email) -> dict[str, Any]:
        body = email.body or ""
        return {
            "sentiment": self._sentiment(body),
            "topics": self._extract_topics(body),
            "action_items": self._extract_action_items(body),
            "urgency": self._detect_urgency(body),
            "key_entities": self._extract_entities(body),
        }

    def _sentiment(self, text: str) -> str:
        positive = ["موافق", "ممتاز", "نعم", "اتفاق", "شكرا", "ممتاز", "great", "yes", "agree", "thanks"]
        negative = ["لا", "مشكلة", "صعوبة", "غالي", "غير مناسب", "no", "problem", "expensive", "difficult"]
        pos = sum(1 for w in positive if w in text.lower())
        neg = sum(1 for w in negative if w in text.lower())
        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "neutral"

    def _extract_topics(self, text: str) -> list[str]:
        topics = []
        keywords = {
            "السعر": "pricing",
            "التسعير": "pricing",
            "الميزانية": "budget",
            "الموعد": "timeline",
            "الجدول": "timeline",
            "المنتج": "product",
            "الخدمة": "service",
            "العقد": "contract",
            "الاتفاق": "agreement",
            "الشراكة": "partnership",
            "الدعم": "support",
            "التنفيذ": "implementation",
        }
        for word, topic in keywords.items():
            if word in text:
                if topic not in topics:
                    topics.append(topic)
        return topics

    def _extract_action_items(self, text: str) -> list[str]:
        items = []
        for line in text.split("\n"):
            stripped = line.strip()
            if any(stripped.lower().startswith(m) for m in ["action:", "- [ ]", "* [ ]", "متابعة:", "إجراء:"]):
                items.append(stripped)
        return items[:5]

    def _detect_urgency(self, text: str) -> str:
        urgent = ["عاجل", "مهم", "ضروري", "urgent", "important", "asap", "soon"]
        count = sum(1 for w in urgent if w in text.lower())
        if count >= 2:
            return "high"
        if count == 1:
            return "medium"
        return "low"

    def _extract_entities(self, text: str) -> list[dict]:
        return []  # Future: NER for organizations, people, dates
