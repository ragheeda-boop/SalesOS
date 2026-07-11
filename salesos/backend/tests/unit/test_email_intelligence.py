"""Tests for Email Intelligence — sentiment, topics, action items, urgency, empty text."""
from __future__ import annotations

import pytest

from domains.commercial.email import Email, EmailIntelligence


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def analyzer():
    return EmailIntelligence()


def _make_email(body: str) -> Email:
    return Email(
        id="em-1",
        tenant_id="t-1",
        opportunity_id="opp-1",
        subject="Test",
        from_address="sender@test.com",
        body=body,
    )


# ── Tests: Sentiment Analysis ───────────────────────────────────────────────

class TestSentiment:
    def test_positive_arabic(self, analyzer):
        email = _make_email("موافق على العرض، شكرا لكم على الممتاز")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "positive"

    def test_negative_arabic(self, analyzer):
        email = _make_email("لا أستطيع الموافقة، السعر غالي جداً")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "negative"

    def test_neutral(self, analyzer):
        email = _make_email("نبحث في الخيارات المتاحة حالياً")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "neutral"

    def test_positive_english(self, analyzer):
        email = _make_email("Great, I agree with the proposal. Thanks!")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "positive"

    def test_negative_english(self, analyzer):
        email = _make_email("No, this is a problem. The price is expensive and difficult.")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "negative"

    def test_equal_pos_neg_is_neutral(self, analyzer):
        email = _make_email("نعم لا")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "neutral"

    def test_empty_body(self, analyzer):
        email = _make_email("")
        result = analyzer.analyze(email)
        assert result["sentiment"] == "neutral"


# ── Tests: Topic Extraction ─────────────────────────────────────────────────

class TestTopicExtraction:
    def test_pricing_topic(self, analyzer):
        email = _make_email("نتحدث عن السعر والتسعير للمشروع")
        result = analyzer.analyze(email)
        assert "pricing" in result["topics"]

    def test_budget_topic(self, analyzer):
        email = _make_email("الميزانية المخصصة لهذا المشروع كبيرة")
        result = analyzer.analyze(email)
        assert "budget" in result["topics"]

    def test_timeline_topic(self, analyzer):
        email = _make_email("الجدول الزمني للتنفيذ في الموعد المحدد")
        result = analyzer.analyze(email)
        assert "timeline" in result["topics"]

    def test_contract_topic(self, analyzer):
        email = _make_email("نحتاج مراجعة العقد قبل التوقيع")
        result = analyzer.analyze(email)
        assert "contract" in result["topics"]

    def test_multiple_topics(self, analyzer):
        email = _make_email("السعر والعقد والتنفيذ جميعها مهمة")
        result = analyzer.analyze(email)
        assert "pricing" in result["topics"]
        assert "contract" in result["topics"]
        assert "implementation" in result["topics"]

    def test_no_topics(self, analyzer):
        email = _make_email("مرحبا كيف حالك")
        result = analyzer.analyze(email)
        assert result["topics"] == []

    def test_product_topic(self, analyzer):
        email = _make_email("نود معرفة تفاصيل المنتج والخدمة")
        result = analyzer.analyze(email)
        assert "product" in result["topics"]
        assert "service" in result["topics"]

    def test_partnership_topic(self, analyzer):
        email = _make_email("الشراكة بيننا ستكون مميزة")
        result = analyzer.analyze(email)
        assert "partnership" in result["topics"]


# ── Tests: Action Item Extraction ────────────────────────────────────────────

class TestActionItems:
    def test_action_colon_prefix(self, analyzer):
        email = _make_email("action: متابعة العرض下周")
        result = analyzer.analyze(email)
        assert len(result["action_items"]) == 1

    def test_checkbox_prefix(self, analyzer):
        email = _make_email("- [ ] إرسال العرض")
        result = analyzer.analyze(email)
        assert len(result["action_items"]) == 1

    def test_arabic_action_prefix(self, analyzer):
        email = _make_email("متابعة: التواصل مع العميل")
        result = analyzer.analyze(email)
        assert len(result["action_items"]) == 1

    def test_ajira_prefix(self, analyzer):
        email = _make_email("إجراء: تحديد موعد الاجتماع")
        result = analyzer.analyze(email)
        assert len(result["action_items"]) == 1

    def test_multiple_action_items(self, analyzer):
        email = _make_email("action: task 1\n- [ ] task 2\nمتابعة: task 3")
        result = analyzer.analyze(email)
        assert len(result["action_items"]) == 3

    def test_max_5_action_items(self, analyzer):
        lines = "\n".join([f"action: item {i}" for i in range(10)])
        email = _make_email(lines)
        result = analyzer.analyze(email)
        assert len(result["action_items"]) <= 5

    def test_no_action_items(self, analyzer):
        email = _make_email("رسالة عادية بدون مهام")
        result = analyzer.analyze(email)
        assert result["action_items"] == []


# ── Tests: Urgency Detection ────────────────────────────────────────────────

class TestUrgency:
    def test_high_urgency(self, analyzer):
        email = _make_email("هذا عاجل وضروري، نحتاج الرد ASAP")
        result = analyzer.analyze(email)
        assert result["urgency"] == "high"

    def test_medium_urgency(self, analyzer):
        email = _make_email("مهم جداً أن نرى هذا الملف")
        result = analyzer.analyze(email)
        assert result["urgency"] == "medium"

    def test_low_urgency(self, analyzer):
        email = _make_email("يمكنك الرد في الوقت المناسب")
        result = analyzer.analyze(email)
        assert result["urgency"] == "low"

    def test_english_urgent(self, analyzer):
        email = _make_email("This is urgent and important ASAP")
        result = analyzer.analyze(email)
        assert result["urgency"] == "high"

    def test_single_urgent_word(self, analyzer):
        email = _make_email("الرد مهم")
        result = analyzer.analyze(email)
        assert result["urgency"] == "medium"

    def test_no_urgency_words(self, analyzer):
        email = _make_email("نرحب بكم في مؤتمرنا السنوي")
        result = analyzer.analyze(email)
        assert result["urgency"] == "low"


# ── Tests: Empty / Edge Cases ────────────────────────────────────────────────

class TestEmptyHandling:
    def test_empty_body_returns_all_fields(self, analyzer):
        email = _make_email("")
        result = analyzer.analyze(email)
        assert "sentiment" in result
        assert "topics" in result
        assert "action_items" in result
        assert "urgency" in result
        assert "key_entities" in result

    def test_none_body(self, analyzer):
        email = _make_email("")
        email.body = ""
        result = analyzer.analyze(email)
        assert result["sentiment"] == "neutral"
        assert result["topics"] == []
        assert result["urgency"] == "low"

    def test_key_entities_empty(self, analyzer):
        email = _make_email("test body")
        result = analyzer.analyze(email)
        assert isinstance(result["key_entities"], list)

    def test_email_object_fields(self, analyzer):
        email = Email(
            id="em-2", tenant_id="t-1", opportunity_id="opp-1",
            subject="Subject", from_address="a@b.com", body="",
        )
        result = analyzer.analyze(email)
        assert isinstance(result, dict)
