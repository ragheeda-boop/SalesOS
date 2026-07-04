"""Tests for QueryParser — handles Arabic, English, field prefixes, quoted phrases."""

from domains.search.engine.parser import QueryParser


def test_empty_query():
    p = QueryParser.default()
    parsed = p.parse("")
    assert not parsed.has_content
    assert parsed.tokens == []
    assert parsed.phrases == []
    assert parsed.field_filters == {}


def test_whitespace_query():
    p = QueryParser.default()
    parsed = p.parse("   ")
    assert not parsed.has_content


def test_single_token():
    p = QueryParser.default()
    parsed = p.parse("شركة")
    assert parsed.has_content
    assert parsed.tokens == ["شركة"]
    assert parsed.phrases == []


def test_multiple_tokens():
    p = QueryParser.default()
    parsed = p.parse("شركة الرياض")
    assert parsed.tokens == ["شركة", "الرياض"]


def test_quoted_phrase():
    p = QueryParser.default()
    parsed = p.parse('"شركة الأمل"')
    assert parsed.phrases == ["شركة الأمل"]
    assert parsed.tokens == []


def test_mixed_tokens_and_phrases():
    p = QueryParser.default()
    parsed = p.parse('شركة "نقليات البركة" الرياض')
    assert "شركة" in parsed.tokens
    assert "الرياض" in parsed.tokens
    assert "نقليات البركة" in parsed.phrases


def test_field_prefix_cr():
    p = QueryParser.default()
    parsed = p.parse("cr:1234567890")
    assert parsed.field_filters.get("cr") == "1234567890"
    assert parsed.tokens == []


def test_field_prefix_cr_number():
    p = QueryParser.default()
    parsed = p.parse("cr_number:1010123456")
    assert parsed.field_filters.get("cr_number") == "1010123456"


def test_field_prefix_city():
    p = QueryParser.default()
    parsed = p.parse("city:الرياض")
    assert parsed.field_filters.get("city") == "الرياض"


def test_field_prefix_region():
    p = QueryParser.default()
    parsed = p.parse("region:Riyadh")
    assert parsed.field_filters.get("region") == "Riyadh"


def test_field_prefix_status():
    p = QueryParser.default()
    parsed = p.parse("status:active")
    assert parsed.field_filters.get("status") == "active"


def test_mixed_free_text_and_field_prefix():
    p = QueryParser.default()
    parsed = p.parse("شركة نقل city:جدة status:active")
    assert "شركة" in parsed.tokens
    assert "نقل" in parsed.tokens
    assert parsed.field_filters.get("city") == "جدة"
    assert parsed.field_filters.get("status") == "active"


def test_unknown_field_prefix_goes_to_tokens():
    p = QueryParser.default()
    parsed = p.parse("unknown_field:value")
    assert parsed.tokens == ["unknown_field:value"]
    assert parsed.field_filters == {}


def test_english_query():
    p = QueryParser.default()
    parsed = p.parse("ALBAIK")
    assert parsed.tokens == ["ALBAIK"]


def test_full_text_property():
    p = QueryParser.default()
    parsed = p.parse('شركة "نقليات البركة"')
    assert parsed.full_text == 'شركة "نقليات البركة"'


def test_custom_known_fields():
    p = QueryParser(known_fields={"custom_field"})
    parsed = p.parse("custom_field:value")
    assert parsed.field_filters.get("custom_field") == "value"


def test_has_content_with_field_filter():
    p = QueryParser.default()
    parsed = p.parse("cr:123")
    assert parsed.has_content
