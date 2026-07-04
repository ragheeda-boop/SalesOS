import io
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company


class ExcelImportService:
    SUGGESTED_MAPPING = {
        "name_ar": ["name", "company", "company name", "company_name", "اسم", "الاسم", "اسم الشركة", "company_ar"],
        "name_en": ["name_en", "english name", "name english", "الاسم الإنجليزي"],
        "email": ["email", "e-mail", "البريد", "البريد الالكتروني", "mail"],
        "phone": ["phone", "phone number", "telephone", "tel", "mobile", "هاتف", "جوال", "رقم الهاتف"],
        "website": ["website", "web", "url", "موقع", "الموقع"],
        "city": ["city", "المدينة", "مدينة"],
        "region": ["region", "area", "المنطقة", "منطقة"],
        "cr_number": ["cr", "cr number", "commercial register", "سجل تجاري", "رقم السجل"],
        "postal_code": ["zip", "zip code", "postal code", "الرمز البريدي"],
        "address": ["address", "عنوان", "العنوان"],
        "status": ["status", "الحالة", "حالة"],
    }

    def __init__(self, db: AsyncSession, logger: Any = None):
        self.db = db
        self.logger = logger

    def parse_excel(self, content: bytes, filename: str) -> tuple[list[dict], list[str]]:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return [], ["Empty spreadsheet"]

        headers = [str(h).strip() if h else f"column_{i}" for i, h in enumerate(rows[0])]
        data = []
        errors = []
        for i, row in enumerate(rows[1:], start=2):
            row_data = {}
            row_errors = []
            for j, val in enumerate(row):
                col_name = headers[j] if j < len(headers) else f"column_{j}"
                row_data[col_name] = str(val) if val is not None else ""
            if any(v.strip() for v in row_data.values()):
                data.append(row_data)
        return data, errors

    def suggest_mapping(self, columns: list[str]) -> dict[str, str]:
        mapping = {}
        lower_cols = {c: c.lower().strip() for c in columns}
        for target, source_names in self.SUGGESTED_MAPPING.items():
            for col_orig, col_lower in lower_cols.items():
                if col_lower in source_names:
                    mapping[target] = col_orig
                    break
        return mapping

    async def import_companies(
        self,
        content: bytes,
        filename: str,
        tenant_id: str,
        column_mapping: Optional[dict[str, str]] = None,
    ) -> dict:
        records, parse_errors = self.parse_excel(content, filename)
        if parse_errors:
            return {"total": 0, "imported": 0, "skipped": 0, "errors": parse_errors}

        if not column_mapping:
            column_mapping = self.suggest_mapping(list(records[0].keys()) if records else [])

        imported = 0
        skipped = 0
        errors = []

        for row in records:
            try:
                company_data = {}
                for target_field, source_col in column_mapping.items():
                    val = row.get(source_col, "").strip()
                    if val:
                        company_data[target_field] = val

                name_ar = company_data.get("name_ar") or company_data.get("name_en")
                if not name_ar:
                    skipped += 1
                    continue

                exists = await self.db.execute(
                    select(Company).where(
                        Company.tenant_id == uuid.UUID(tenant_id),
                        Company.cr_number == company_data.get("cr_number", name_ar),
                    )
                )
                if exists.scalar_one_or_none():
                    skipped += 1
                    continue

                company = Company(
                    tenant_id=uuid.UUID(tenant_id),
                    name_ar=name_ar,
                    name_en=company_data.get("name_en"),
                    email=company_data.get("email"),
                    phone=company_data.get("phone"),
                    website=company_data.get("website"),
                    city=company_data.get("city"),
                    region=company_data.get("region"),
                    cr_number=company_data.get("cr_number", f"EXCEL-{uuid.uuid4().hex[:12].upper()}"),
                    postal_code=company_data.get("postal_code"),
                    address=company_data.get("address"),
                    status=company_data.get("status", "active"),
                )
                self.db.add(company)
                await self.db.flush()
                imported += 1

            except Exception as e:
                errors.append(f"Row error: {str(e)[:200]}")
                skipped += 1

        await self.db.commit()
        return {
            "total": len(records),
            "imported": imported,
            "skipped": skipped,
            "errors": errors[:50],
        }

    async def preview(
        self, content: bytes, filename: str
    ) -> dict:
        records, errors = self.parse_excel(content, filename)
        if errors:
            return {"filename": filename, "total_rows": 0, "sample_rows": [], "detected_columns": [], "suggested_mapping": {}, "errors": errors}

        columns = list(records[0].keys()) if records else []
        mapping = self.suggest_mapping(columns)

        sample = []
        for i, row in enumerate(records[:5]):
            sample.append({"row_number": i + 1, "data": row, "validation_errors": []})

        return {
            "filename": filename,
            "total_rows": len(records),
            "sample_rows": sample,
            "detected_columns": columns,
            "suggested_mapping": mapping,
        }
