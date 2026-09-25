import uuid
from typing import Any, cast

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.company.models import Company


class NotionSyncService:
    NOTION_API = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(
        self,
        db: AsyncSession,
        logger: Any = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.db = db
        self.logger = logger
        self.client = client

    async def import_companies(
        self,
        database_id: str,
        token: str,
        tenant_id: str,
    ) -> dict:
        if self.client is not None:
            return await self._import_companies_with_client(
                client=self.client,
                database_id=database_id,
                token=token,
                tenant_id=tenant_id,
            )
        async with httpx.AsyncClient() as client:
            return await self._import_companies_with_client(
                client=client,
                database_id=database_id,
                token=token,
                tenant_id=tenant_id,
            )

    async def _import_companies_with_client(
        self,
        *,
        client: httpx.AsyncClient,
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
        seen_cursors: set[str] = set()

        while has_more:
            payload: dict = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor

            try:
                r = await client.post(
                    f"{self.NOTION_API}/databases/{database_id}/query",
                    headers=headers,
                    json=payload,
                    timeout=settings.notion_request_timeout,
                )
            except httpx.HTTPError:
                errors.append("Notion API request failed")
                break

            if r.status_code != 200:
                # Do not echo provider response text; it may contain customer data.
                errors.append(f"Notion API error: HTTP {r.status_code}")
                break

            try:
                data = r.json()
            except ValueError:
                errors.append("Notion API returned invalid JSON")
                break
            if not isinstance(data, dict):
                errors.append("Notion API returned an invalid response")
                break
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
            if has_more and (not start_cursor or start_cursor in seen_cursors):
                errors.append("Notion pagination cursor was missing or repeated")
                break
            if start_cursor:
                seen_cursors.add(start_cursor)

            for page in data.get("results", []):
                entities_found += 1
                props = page.get("properties", {})
                try:
                    page_id = str(page.get("id") or "").strip()
                    if not page_id:
                        entities_skipped += 1
                        continue

                    company_data = self._extract_company(props)
                    if not company_data.get("name"):
                        entities_skipped += 1
                        continue

                    # Use the external page identity before name matching so reruns
                    # remain idempotent even when a company is renamed in Notion.
                    exists = await self.db.execute(
                        select(Company).where(
                            Company.tenant_id == uuid.UUID(tenant_id),
                            Company.extra_metadata["notion_page_id"].as_string() == page_id,
                            Company.extra_metadata["notion_database_id"].as_string()
                            == database_id,
                        )
                    )
                    if exists.scalar_one_or_none():
                        entities_skipped += 1
                        continue

                    display_name = company_data.get("name_ar") or company_data["name"]
                    existing_name = await self.db.execute(
                        select(Company.id).where(
                            Company.tenant_id == uuid.UUID(tenant_id),
                            Company.name_ar == display_name,
                        ).limit(1)
                    )
                    if existing_name.scalar_one_or_none():
                        entities_skipped += 1
                        continue

                    company = Company(
                        tenant_id=uuid.UUID(tenant_id),
                        name_ar=display_name,
                        name_en=company_data.get("name_en"),
                        email=company_data.get("email"),
                        phone=company_data.get("phone"),
                        website=company_data.get("website"),
                        city=company_data.get("city"),
                        region=company_data.get("region"),
                        # External page IDs are source references, never CR anchors.
                        cr_number=None,
                        status="active",
                        tags=company_data.get("tags", []),
                        extra_metadata={
                            "source": "notion",
                            "notion_database_id": database_id,
                            "notion_page_id": page_id,
                        },
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

    def _extract_company(self, props: dict) -> dict[str, Any]:
        data: dict[str, Any] = {}

        for field, config in [
            ("name", ["Name", "name", "Company Name", "company_name", "اسم"]),
            ("name_ar", ["Name AR", "name_ar", "الاسم", "اسم_عربي"]),
            ("name_en", ["Name EN", "name_en", "English Name"]),
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

    def _get_notion_prop(self, props: dict, possible_names: list[str]) -> str | None:
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
                return cast(str | None, prop.get("phone_number"))
            elif ptype == "email":
                return cast(str | None, prop.get("email"))
            elif ptype == "url":
                return cast(str | None, prop.get("url"))
            elif ptype in ("number",):
                val = prop.get("number")
                return str(val) if val is not None else None
        return None
