import time
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 0.35  # seconds between API calls
NOTION_VERSION = "2022-06-28"


class MuhideNotion:
    def __init__(self, token: str):
        if not token:
            raise ValueError(
                "Notion token is required. Set the NOTION_TOKEN environment "
                "variable or configure it in config.py."
            )
        self._token = token

    def _new_client(self) -> httpx.Client:
        client = httpx.Client(
            base_url="https://api.notion.com/v1/",
            timeout=httpx.Timeout(timeout=30.0),
        )
        client.headers.update({
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        })
        return client

    def _call(self, path: str, method: str = "POST", body: dict = None, retries: int = 3) -> dict:
        for attempt in range(retries):
            time.sleep(RATE_LIMIT_DELAY)
            try:
                client = self._new_client()
                kwargs = {"method": method, "url": path}
                if method in ("POST", "PATCH"):
                    kwargs["json"] = body or {}
                resp = client.request(**kwargs)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                if attempt < retries - 1:
                    wait = (attempt + 1) * 2
                    logger.warning(
                        "API call failed (attempt %d/%d): %s. Retrying in %ds...",
                        attempt + 1, retries, exc, wait,
                    )
                    time.sleep(wait)
                else:
                    raise

    def query_database(self, database_id: str, **kwargs) -> dict:
        return self._call(
            path=f"databases/{database_id}/query",
            body=kwargs,
        )

    def get_page(self, page_id: str) -> dict:
        return self._call(
            path=f"pages/{page_id}",
            method="GET",
        )

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self._call(
            path=f"pages/{page_id}",
            method="PATCH",
            body={"properties": properties},
        )

    def create_page(self, database_id: str, properties: dict) -> dict:
        return self._call(
            path="pages",
            method="POST",
            body={
                "parent": {"database_id": database_id},
                "properties": properties,
            },
        )

    def add_property_to_database(
        self, database_id: str, property_name: str, property_config: dict
    ) -> dict:
        return self._call(
            path=f"databases/{database_id}",
            method="PATCH",
            body={"properties": {property_name: property_config}},
        )

    def get_all_pages(
        self, database_id: str, page_size: int = 100
    ) -> list:
        all_pages = []
        start_cursor = None

        while True:
            kwargs = {"page_size": page_size}
            if start_cursor:
                kwargs["start_cursor"] = start_cursor

            response = self._call(
                path=f"databases/{database_id}/query",
                body=kwargs,
            )
            all_pages.extend(response["results"])

            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

        return all_pages


# ---------------------------------------------------------------------------
# Property value extractors
# ---------------------------------------------------------------------------

def get_title(props: dict, field: str) -> str:
    objs = props.get(field, {}).get("title", [])
    return objs[0].get("plain_text", "") if objs else ""


def get_rich_text(props: dict, field: str) -> str:
    objs = props.get(field, {}).get("rich_text", [])
    return objs[0].get("plain_text", "") if objs else ""


def get_number(props: dict, field: str) -> Optional[float]:
    return props.get(field, {}).get("number")


def get_select(props: dict, field: str) -> str:
    obj = props.get(field, {}).get("select")
    return obj.get("name", "") if obj else ""


def get_multi_select(props: dict, field: str) -> list:
    return [
        item.get("name", "")
        for item in props.get(field, {}).get("multi_select", [])
    ]


def get_date(props: dict, field: str) -> Optional[str]:
    obj = props.get(field, {}).get("date")
    return obj.get("start") if obj else None


def get_email(props: dict, field: str) -> str:
    return props.get(field, {}).get("email", "") or ""


def get_phone(props: dict, field: str) -> str:
    return props.get(field, {}).get("phone_number", "") or ""


def get_checkbox(props: dict, field: str) -> bool:
    return props.get(field, {}).get("checkbox", False)


def get_url(props: dict, field: str) -> str:
    return props.get(field, {}).get("url", "") or ""


# ---------------------------------------------------------------------------
# Property value builders
# ---------------------------------------------------------------------------

def set_title(value: str) -> dict:
    return {"title": [{"text": {"content": value}}]}


def set_rich_text(value: str) -> dict:
    return {"rich_text": [{"text": {"content": value}}]}


def set_number(value: Optional[float]) -> dict:
    return {"number": value}


def set_select(value: str) -> dict:
    return {"select": {"name": value}}


def set_multi_select(values: list) -> dict:
    return {"multi_select": [{"name": v} for v in values]}


def set_checkbox(value: bool) -> dict:
    return {"checkbox": value}


def set_date(value: str) -> dict:
    return {"date": {"start": value}}


def set_email(value: str) -> dict:
    return {"email": value}


def set_phone(value: str) -> dict:
    return {"phone_number": value}
