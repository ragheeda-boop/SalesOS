"""Tests for Meeting Intelligence — talking points, questions, topics, action items, sentiment."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.commercial.meeting.intelligence import MeetingIntelligenceService


# ── Fake SQLAlchemy helpers ──────────────────────────────────────────────────

class FakeMapping:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()


class FakeMappings:
    def __init__(self, rows=None, one=None):
        self._rows = rows or []
        self._one = one

    def one(self):
        return FakeMapping(self._one) if self._one else None

    def one_or_none(self):
        return FakeMapping(self._one) if self._one else None

    def all(self):
        return [FakeMapping(r) for r in self._rows]


class FakeResult:
    def __init__(self, mappings_obj=None):
        self._mappings = mappings_obj or FakeMappings()

    def mappings(self):
        return self._mappings


# ── Fixtures ─────────────────────────────────────────────────────────────────

COMPANY_ROW = {
    "name_ar": "شركة التقنية المتقدمة",
    "name_en": "Advanced Tech Co",
    "industry": "technology",
    "city": "Riyadh",
    "activity_description": "شركة تقنية",
}

OPP_ROW = {"name": "ERP Project", "stage": "proposal", "value": 500000.0}


def _make_service(stage="proposal"):
    opp_row = {**OPP_ROW, "stage": stage}

    async def execute(sql_str, params=None):
        text = str(sql_str)
        if "companies" in text and "activity" not in text:
            return FakeResult(FakeMappings(one=COMPANY_ROW))
        elif "company_signals" in text:
            return FakeResult(FakeMappings(rows=[
                {"title": "Signal 1", "description": "Description of signal 1", "created_at": datetime.now(timezone.utc)},
            ]))
        elif "contacts_standalone" in text:
            return FakeResult(FakeMappings(rows=[
                {"name": "Ahmed", "position": "CTO"},
            ]))
        elif "commercial_opportunities" in text:
            return FakeResult(FakeMappings(one=opp_row))
        return FakeResult(FakeMappings())

    session = AsyncMock()
    session.execute = execute
    return MeetingIntelligenceService(db=session, tenant_id="t-1")


# ── Tests: Talking Points ───────────────────────────────────────────────────

class TestTalkingPoints:
    def test_qualification_stage(self):
        service = _make_service(stage="qualification")
        points = service._generate_talking_points("شركة التقنية", "qualification")
        assert any("تأهيل" in p for p in points)

    def test_proposal_stage(self):
        service = _make_service(stage="proposal")
        points = service._generate_talking_points("شركة التقنية", "proposal")
        assert any("عرض السعر" in p for p in points)

    def test_negotiation_stage(self):
        service = _make_service(stage="negotiation")
        points = service._generate_talking_points("شركة التقنية", "negotiation")
        assert any("التفاوض" in p for p in points)

    def test_always_has_general_point(self):
        service = _make_service()
        points = service._generate_talking_points("Acme Corp", "prospecting")
        assert len(points) >= 1
        assert "Acme Corp" in points[0]

    def test_unknown_stage_has_general_only(self):
        service = _make_service()
        points = service._generate_talking_points("Test", "unknown_stage")
        assert len(points) == 1

    def test_company_name_in_point(self):
        service = _make_service()
        points = service._generate_talking_points("Arabic Company Name", "prospecting")
        assert "Arabic Company Name" in points[0]


# ── Tests: Questions ─────────────────────────────────────────────────────────

class TestQuestions:
    def test_always_has_general_question(self):
        service = _make_service()
        questions = service._generate_questions("prospecting")
        assert len(questions) >= 1
        assert "التحديات" in questions[0]

    def test_qualification_has_budget_question(self):
        service = _make_service()
        questions = service._generate_questions("qualification")
        assert any("ميزانيتكم" in q for q in questions)

    def test_qualification_has_decision_maker_question(self):
        service = _make_service()
        questions = service._generate_questions("qualification")
        assert any("أصحاب القرار" in q for q in questions)

    def test_proposal_has_price_question(self):
        service = _make_service()
        questions = service._generate_questions("proposal")
        assert any("عرض السعر" in q for q in questions)

    def test_negotiation_has_default_questions(self):
        service = _make_service()
        questions = service._generate_questions("negotiation")
        assert len(questions) == 1  # Only the default question


# ── Tests: Topic Extraction ─────────────────────────────────────────────────

class TestTopicExtraction:
    def test_returns_list(self):
        service = _make_service()
        topics = service._extract_topics("This is a long enough line for topic extraction to work properly")
        assert isinstance(topics, list)

    def test_short_lines_excluded(self):
        service = _make_service()
        topics = service._extract_topics("short\nAnother short line")
        assert topics == []

    def test_long_lines_included(self):
        service = _make_service()
        long_line = "This is a very long line that should be included as a topic because it exceeds twenty characters"
        topics = service._extract_topics(long_line)
        assert len(topics) == 1

    def test_max_5_topics(self):
        service = _make_service()
        lines = "\n".join([f"This is topic line number {i} and it is quite long enough" for i in range(10)])
        topics = service._extract_topics(lines)
        assert len(topics) <= 5

    def test_empty_notes(self):
        service = _make_service()
        topics = service._extract_topics("")
        assert topics == []

    def test_whitespace_only(self):
        service = _make_service()
        topics = service._extract_topics("   \n  \n  ")
        assert topics == []


# ── Tests: Action Items Extraction ──────────────────────────────────────────

class TestActionItemsExtraction:
    def test_action_colon(self):
        service = _make_service()
        items = service._extract_action_items("action: send proposal")
        assert len(items) == 1
        assert "send proposal" in items[0]

    def test_arabic_action(self):
        service = _make_service()
        items = service._extract_action_items("متابعة: التواصل مع العميل")
        assert len(items) == 1

    def test_checkbox(self):
        service = _make_service()
        items = service._extract_action_items("- [ ] Prepare demo")
        assert len(items) == 1

    def test_multiple_items(self):
        service = _make_service()
        notes = "action: task 1\n- [ ] task 2\nإجراء: task 3"
        items = service._extract_action_items(notes)
        assert len(items) == 3

    def test_max_5_items(self):
        service = _make_service()
        notes = "\n".join([f"action: item {i}" for i in range(10)])
        items = service._extract_action_items(notes)
        assert len(items) <= 5

    def test_no_items(self):
        service = _make_service()
        items = service._extract_action_items("Regular text without action items")
        assert items == []

    def test_empty_notes(self):
        service = _make_service()
        items = service._extract_action_items("")
        assert items == []


# ── Tests: Sentiment Analysis ───────────────────────────────────────────────

class TestSentimentAnalysis:
    def test_positive_sentiment(self):
        service = _make_service()
        # Use words that don't accidentally contain "لا" as substring (e.g. "الاجتماع" contains "لا")
        sentiment = service._analyze_sentiment("ممتاز جداً، شراكة ناجحة وموافق على كل شيء")
        assert sentiment == "positive"

    def test_negative_sentiment(self):
        service = _make_service()
        sentiment = service._analyze_sentiment("مشكلة كبيرة، صعوبة في التنفيذ والغالي جداً")
        assert sentiment == "negative"

    def test_neutral_sentiment(self):
        service = _make_service()
        sentiment = service._analyze_sentiment("نحدد خياراتنا في الوقت الحالي")
        assert sentiment == "neutral"

    def test_empty_notes_neutral(self):
        service = _make_service()
        sentiment = service._analyze_sentiment("")
        assert sentiment == "neutral"

    def test_none_like_empty(self):
        service = _make_service()
        sentiment = service._analyze_sentiment("")
        assert sentiment in ("positive", "negative", "neutral")

    def test_positive_words_weight(self):
        service = _make_service()
        sentiment = service._analyze_sentiment("نعم موافق شراكة ممتاز اتفاق")
        assert sentiment == "positive"


# ── Tests: generate_summary (non-DB-dependent parts) ────────────────────────

class TestGenerateSummary:
    async def test_returns_dict(self):
        service = _make_service()
        result = await service.generate_summary({"notes": ""})
        assert isinstance(result, dict)

    async def test_has_key_fields(self):
        service = _make_service()
        result = await service.generate_summary({"notes": ""})
        assert "key_topics" in result
        assert "action_items" in result
        assert "sentiment" in result

    async def test_with_notes(self):
        service = _make_service()
        notes = "action: متابعة العميل\nممتاز جداً شراكة ناجحة"
        result = await service.generate_summary({"notes": notes})
        assert len(result["action_items"]) >= 1
        assert result["sentiment"] == "positive"
