"""Unit tests for NotionSyncService — no DB required."""

from unittest.mock import MagicMock

from app.modules.notion_sync.service import NotionSyncService


def make_notion_prop(ptype: str, value):
    builders = {
        "title": lambda: {"type": "title", "title": [{"plain_text": value or ""}]},
        "rich_text": lambda: {"type": "rich_text", "rich_text": [{"plain_text": value or ""}]},
        "select": lambda: {"type": "select", "select": {"name": value} if value else None},
        "phone_number": lambda: {"type": "phone_number", "phone_number": value},
        "email": lambda: {"type": "email", "email": value},
        "url": lambda: {"type": "url", "url": value},
    }
    build = builders.get(ptype)
    return build() if build else {"type": ptype}


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
