import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.config import settings
from app.modules.company.models import Company
from app.modules.contact.models import Contact
from app.modules.identity.models import User


class NotionSyncService:
    NOTION_API = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, db: AsyncSession, logger: Any = None):
        self.db = db
        self.logger = logger

    async def import_companies(
        self,
        database_id: str,
        token: str,
        tenant_id: str,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }

        entities_found = 0
        entities_imported = 0
        entities_skipped = 0
        errors = []

        has_more = True
        start_cursor = None

        while has_more:
            payload: dict = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.NOTION_API}/databases/{database_id}/query",
                    headers=headers,
                    json=payload,
                    timeout=settings.notion_request_timeout,
                )

            if r.status_code != 200:
                errors.append(f"Notion API error: {r.status_code} {r.text[:200]}")
                break

            data = r.json()
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

            for page in data.get("results", []):
                entities_found += 1
                props = page.get("properties", {})
                try:
                    company_data = self._extract_company(props)
                    if not company_data.get("name"):
                        entities_skipped += 1
                        continue

                    exists = await self.db.execute(
                        select(Company).where(
                            Company.tenant_id == uuid.UUID(tenant_id),
                            Company.name_ar == company_data["name"],
                        )
                    )
                    if exists.scalar_one_or_none():
                        entities_skipped += 1
                        continue

                    company = Company(
                        tenant_id=uuid.UUID(tenant_id),
                        name_ar=company_data["name"],
                        name_en=company_data.get("name_ar"),
                        email=company_data.get("email"),
                        phone=company_data.get("phone"),
                        website=company_data.get("website"),
                        city=company_data.get("city"),
                        region=company_data.get("region"),
                        cr_number=f"NOTION-{uuid.uuid4().hex[:12].upper()}",
                        status="active",
                        tags=company_data.get("tags", []),
                    )
                    self.db.add(company)
                    await self.db.flush()
                    entities_imported += 1

                except Exception as e:
                    errors.append(f"Error importing page {page.get('id')}: {str(e)[:200]}")

        await self.db.commit()

        return {
            "entities_found": entities_found,
            "entities_imported": entities_imported,
            "entities_skipped": entities_skipped,
            "errors": errors[:50],
        }

    def _extract_company(self, props: dict) -> dict:
        data = {}

        for field, config in [
            ("name", ["Name", "name", "Company Name", "company_name", "اسم"]),
            ("name_ar", ["Name AR", "name_ar", "الاسم", "اسم_عربي"]),
            ("email", ["Email", "email", "البريد"]),
            ("phone", ["Phone", "phone", "Phone Number", "هاتف"]),
            ("website", ["Website", "website", "Web", "موقع"]),
            ("city", ["City", "city", "المدينة"]),
            ("region", ["Region", "region", "المنطقة"]),
        ]:
            val = self._get_notion_prop(props, config)
            if val:
                data[field] = val

        tags = self._get_notion_prop(props, ["Tags", "tags", "العلامات"])
        if tags and isinstance(tags, str):
            data["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

        return data

    def _get_notion_prop(self, props: dict, possible_names: list[str]) -> Optional[str]:
        for name in possible_names:
            prop = props.get(name)
            if not prop:
                continue
            ptype = prop.get("type")
            if ptype == "title":
                parts = prop.get("title", [])
                return " ".join(p.get("plain_text", "") for p in parts) if parts else None
            elif ptype == "rich_text":
                parts = prop.get("rich_text", [])
                return " ".join(p.get("plain_text", "") for p in parts) if parts else None
            elif ptype == "select":
                sel = prop.get("select")
                return sel.get("name") if sel else None
            elif ptype == "phone_number":
                return prop.get("phone_number")
            elif ptype == "email":
                return prop.get("email")
            elif ptype == "url":
                return prop.get("url")
            elif ptype in ("number",):
                val = prop.get("number")
                return str(val) if val is not None else None
        return None
