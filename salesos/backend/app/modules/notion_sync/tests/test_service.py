"""Unit tests for NotionSyncService — no DB required."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.notion_sync.service import NotionSyncService


def make_notion_prop(ptype: str, value):
    if ptype == "title":
        return {"type": "title", "title": [{"plain_text": value or ""}]}
    elif ptype == "rich_text":
        return {"type": "rich_text", "rich_text": [{"plain_text": value or ""}]}
    elif ptype == "select":
        return {"type": "select", "select": {"name": value} if value else None}
    elif ptype == "phone_number":
        return {"type": "phone_number", "phone_number": value}
    elif ptype == "email":
        return {"type": "email", "email": value}
    elif ptype == "url":
        return {"type": "url", "url": value}
    return {"type": ptype}


class TestExtractCompany:
    def setup_method(self):
        self.svc = NotionSyncService(db=MagicMock())

    def test_extracts_basic_fields(self):
        props = {
            "Name": make_notion_prop("title", "شركة الأفق"),
            "Phone": make_notion_prop("phone_number", "+966551234567"),
            "Email": make_notion_prop("email", "info@horizon.com"),
            "Website": make_notion_prop("url", "https://horizon.com"),
            "City": make_notion_prop("rich_text", "الرياض"),
        }
        result = self.svc._extract_company(props)
        assert result["name"] == "شركة الأفق"
        assert result["phone"] == "+966551234567"
        assert result["email"] == "info@horizon.com"
        assert result["website"] == "https://horizon.com"
        assert result["city"] == "الرياض"

    def test_handles_arabic_field_names(self):
        props = {
            "اسم": make_notion_prop("title", "شركة النور"),
            "هاتف": make_notion_prop("phone_number", "0555000111"),
        }
        result = self.svc._extract_company(props)
        assert result["name"] == "شركة النور"
        assert result["phone"] == "0555000111"

    def test_skips_missing_optional_fields(self):
        props = {
            "Name": make_notion_prop("title", "شركة بسيطة"),
        }
        result = self.svc._extract_company(props)
        assert result["name"] == "شركة بسيطة"
        assert "email" not in result
        assert "website" not in result

    def test_extracts_select_fields(self):
        props = {
            "Company Name": make_notion_prop("title", "شركة"),
            "City": make_notion_prop("select", "جدة"),
            "Region": make_notion_prop("select", "مكة المكرمة"),
        }
        result = self.svc._extract_company(props)
        assert result["city"] == "جدة"
        assert result["region"] == "مكة المكرمة"

    def test_parses_tags_from_rich_text(self):
        props = {
            "Name": make_notion_prop("title", "شركة"),
            "Tags": make_notion_prop("rich_text", "تكنولوجيا, برمجيات, ذكاء اصطناعي"),
        }
        result = self.svc._extract_company(props)
        assert "tags" in result
        assert len(result["tags"]) == 3
        assert "تكنولوجيا" in result["tags"]
