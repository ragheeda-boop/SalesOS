import io
import uuid
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import openpyxl
import pytest

from app.modules.excel_import.service import ExcelImportService


def make_excel(headers: list[str], rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestParseExcel:
    def test_parses_basic_columns(self):
        content = make_excel(
            ["Name", "Email", "Phone"],
            [["شركة الأمل", "info@alamal.com", "0555000111"]],
        )
        svc = ExcelImportService(db=MagicMock())
        records, errors = svc.parse_excel(content, "test.xlsx")
        assert len(records) == 1
        assert records[0]["Name"] == "شركة الأمل"
        assert records[0]["Email"] == "info@alamal.com"
        assert not errors

    def test_skips_empty_rows(self):
        content = make_excel(
            ["Name"],
            [["شركة"], [""], ["شركة أخرى"]],
        )
        svc = ExcelImportService(db=MagicMock())
        records, errors = svc.parse_excel(content, "test.xlsx")
        assert len(records) == 2

    def test_handles_empty_spreadsheet(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        buf = io.BytesIO()
        wb.save(buf)
        content = buf.getvalue()
        svc = ExcelImportService(db=MagicMock())
        records, errors = svc.parse_excel(content, "empty.xlsx")
        assert len(records) == 0


class TestSuggestMapping:
    def test_maps_arabic_column_names(self):
        svc = ExcelImportService(db=MagicMock())
        mapping = svc.suggest_mapping(["اسم", "هاتف", "البريد"])
        assert mapping.get("name_ar") == "اسم"
        assert mapping.get("phone") in ("هاتف",)
        assert mapping.get("email") == "البريد"

    def test_maps_english_column_names(self):
        svc = ExcelImportService(db=MagicMock())
        mapping = svc.suggest_mapping(["Company Name", "Email", "Phone"])
        assert mapping.get("name_ar") == "Company Name"
        assert mapping.get("email") == "Email"
        assert mapping.get("phone") == "Phone"

    def test_returns_empty_for_unrecognized(self):
        svc = ExcelImportService(db=MagicMock())
        mapping = svc.suggest_mapping(["Column A", "Column B"])
        assert mapping == {}


@pytest.mark.asyncio
class TestPreview:
    async def test_returns_sample_rows(self):
        content = make_excel(
            ["اسم", "الهاتف", "البريد", "الموقع"],
            [
                ["شركة أ", "055", "a@a.com", "www.a.com"],
                ["شركة ب", "056", "b@b.com", "www.b.com"],
                ["شركة ج", "057", "c@c.com", "www.c.com"],
            ],
        )
        svc = ExcelImportService(db=MagicMock())
        result = await svc.preview(content, "test.xlsx")
        assert result["filename"] == "test.xlsx"
        assert result["total_rows"] == 3
        assert len(result["sample_rows"]) == 3
        assert "name_ar" in result["suggested_mapping"]

    async def test_limits_to_five_samples(self):
        content = make_excel(
            ["Name"],
            [[f"Company {i}"] for i in range(100)],
        )
        svc = ExcelImportService(db=MagicMock())
        result = await svc.preview(content, "large.xlsx")
        assert result["total_rows"] == 100
        assert len(result["sample_rows"]) == 5


@pytest.mark.asyncio
async def test_import_companies_with_mocked_db():
    content = make_excel(
        ["Company Name", "Phone", "City"],
        [["شركة البرج", "0551234567", "الرياض"]],
    )
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    svc = ExcelImportService(db=db)
    result = await svc.import_companies(content, "test.xlsx", str(uuid.uuid4()))
    assert result["imported"] == 1
    assert result["skipped"] == 0
