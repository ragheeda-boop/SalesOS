"""Google Gmail Provider — EmailProvider implementation (ADR-012 §7).

Uses Gmail REST API v1 via httpx to fetch emails.
Authenticates with stored OAuth 2.0 access tokens.
"""

from __future__ import annotations

import logging
import re
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from intelligence.activity_intelligence.contracts.models import RawEmail
from intelligence.activity_intelligence.contracts.provider import (
    EmailProvider,
    ProviderProfile,
)

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Gmail API error {status}: {message}")


class GoogleGmailProvider(EmailProvider):
    """Gmail API email provider using stored OAuth 2.0 tokens."""

    def __init__(self, access_token: str | None = None, email: str = ""):
        self._access_token = access_token
        self._email = email
        self._authenticated = bool(access_token)
        self._http = httpx.AsyncClient(timeout=30.0)
        self._profile = ProviderProfile(
            provider_id="gmail",
            provider_type="email",
            email=email,
            connected=bool(access_token),
        ) if access_token else None

    async def close(self) -> None:
        await self._http.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{GMAIL_API_BASE}{path}"
        resp = await self._http.get(url, headers=self._headers(), params=params or {})
        if resp.status_code == 401:
            raise GmailAPIError(401, "Token expired or revoked")
        if resp.status_code == 403:
            raise GmailAPIError(403, "Insufficient permissions — gmail.readonly scope required")
        if resp.status_code != 200:
            raise GmailAPIError(resp.status_code, resp.text[:500])
        return resp.json()

    async def authenticate(self, credentials: dict) -> bool:
        self._access_token = credentials.get("access_token", "")
        self._email = credentials.get("email", "")
        self._authenticated = bool(self._access_token)
        if self._authenticated:
            self._profile = ProviderProfile(
                provider_id="gmail",
                provider_type="email",
                email=self._email,
                display_name=credentials.get("display_name", ""),
                connected=True,
            )
        return self._authenticated

    async def get_profile(self) -> ProviderProfile:
        if self._profile:
            return self._profile
        try:
            profile_data = await self._get("/profile")
            self._profile = ProviderProfile(
                provider_id="gmail",
                provider_type="email",
                email=profile_data.get("emailAddress", ""),
                display_name="",
                connected=True,
            )
        except GmailAPIError:
            self._profile = ProviderProfile(
                provider_id="gmail", provider_type="email", connected=False
            )
        return self._profile

    async def fetch_emails(
        self, since: datetime | None = None, max_results: int = 50
    ) -> list[RawEmail]:
        if not self._authenticated:
            return []

        query_parts: list[str] = []
        if since:
            epoch_str = str(int(since.timestamp()))
            query_parts.append(f"after:{epoch_str}")
        query = " ".join(query_parts) if query_parts else None

        list_params: dict[str, Any] = {"maxResults": min(max_results, 100)}
        if query:
            list_params["q"] = query

        list_data = await self._get("/messages", list_params)
        message_ids = [m["id"] for m in list_data.get("messages", [])]

        emails: list[RawEmail] = []
        for mid in message_ids:
            try:
                raw_email = await self.fetch_message(mid)
                if raw_email:
                    emails.append(raw_email)
            except GmailAPIError as e:
                logger.warning("gmail.fetch_message.failed", extra={"message_id": mid, "error": str(e)})

        return emails

    async def fetch_message(self, message_id: str, format: str = "full") -> RawEmail | None:
        data = await self._get(f"/messages/{message_id}", {"format": format})

        headers_map = self._parse_headers(data.get("payload", {}).get("headers", []))

        from_addr = headers_map.get("From", "")
        to_raw = headers_map.get("To", "")
        cc_raw = headers_map.get("Cc", "")
        bcc_raw = headers_map.get("Bcc", "")

        snippet = data.get("snippet", "")
        body_text, body_html = self._extract_body(data.get("payload", {}))

        labels = data.get("labelIds", [])
        internal_ts = data.get("internalDate")
        sent_at = None
        if internal_ts:
            try:
                sent_at = datetime.fromtimestamp(int(internal_ts) / 1000, tz=timezone.utc)
            except (ValueError, TypeError):
                pass
        if not sent_at and headers_map.get("Date"):
            try:
                sent_at = parsedate_to_datetime(headers_map["Date"])
            except Exception:
                pass

        has_attachments = self._has_attachments(data.get("payload", {}))

        return RawEmail(
            message_id=data.get("id", message_id),
            thread_id=data.get("threadId"),
            subject=headers_map.get("Subject", ""),
            from_address=from_addr,
            to_addresses=self._parse_address_list(to_raw),
            cc_addresses=self._parse_address_list(cc_raw),
            bcc_addresses=self._parse_address_list(bcc_raw),
            body_text=body_text,
            body_html=body_html,
            attachments=[],
            in_reply_to=headers_map.get("In-Reply-To"),
            references=headers_map.get("References"),
            sent_at=sent_at,
            labels=labels,
            headers={k: v for k, v in headers_map.items()},
        )

    async def fetch_thread(self, thread_id: str) -> list[RawEmail]:
        if not self._authenticated:
            return []

        data = await self._get(f"/threads/{thread_id}", {"format": "full"})
        messages = data.get("messages", [])

        emails: list[RawEmail] = []
        for msg in messages:
            headers_map = self._parse_headers(msg.get("payload", {}).get("headers", []))
            body_text, body_html = self._extract_body(msg.get("payload", {}))

            internal_ts = msg.get("internalDate")
            sent_at = None
            if internal_ts:
                try:
                    sent_at = datetime.fromtimestamp(int(internal_ts) / 1000, tz=timezone.utc)
                except (ValueError, TypeError):
                    pass

            emails.append(RawEmail(
                message_id=msg.get("id", ""),
                thread_id=thread_id,
                subject=headers_map.get("Subject", ""),
                from_address=headers_map.get("From", ""),
                to_addresses=self._parse_address_list(headers_map.get("To", "")),
                cc_addresses=self._parse_address_list(headers_map.get("Cc", "")),
                bcc_addresses=self._parse_address_list(headers_map.get("Bcc", "")),
                body_text=body_text,
                body_html=body_html,
                in_reply_to=headers_map.get("In-Reply-To"),
                references=headers_map.get("References"),
                sent_at=sent_at,
                labels=msg.get("labelIds", []),
            ))

        return emails

    async def send_email(self, to: str, subject: str, body: str) -> str:
        raise NotImplementedError("Gmail send not implemented — readonly scope only")

    async def get_history_id(self) -> str | None:
        try:
            profile = await self._get("/profile")
            return str(profile.get("historyId", ""))
        except GmailAPIError:
            return None

    async def fetch_history(self, start_history_id: str, max_results: int = 100) -> dict:
        return await self._get("/history", {
            "startHistoryId": start_history_id,
            "maxResults": max_results,
            "labelId": "INBOX",
        })

    @staticmethod
    def _parse_headers(headers: list[dict[str, str]]) -> dict[str, str]:
        return {h["name"]: h["value"] for h in headers}

    @staticmethod
    def _extract_body(payload: dict) -> tuple[str, str]:
        body_text = ""
        body_html = ""
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data", "")

        if body_data:
            decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
            if mime_type == "text/plain":
                body_text = decoded
            elif mime_type == "text/html":
                body_html = decoded
            else:
                body_text = decoded

        parts = payload.get("parts", [])
        for part in parts:
            part_mime = part.get("mimeType", "")
            part_data = part.get("body", {}).get("data", "")
            if part_data:
                decoded = base64.urlsafe_b64decode(part_data).decode("utf-8", errors="replace")
                if part_mime == "text/plain" and not body_text:
                    body_text = decoded
                elif part_mime == "text/html" and not body_html:
                    body_html = decoded
            nested = part.get("parts", [])
            if nested:
                nested_text, nested_html = GoogleGmailProvider._extract_body(part)
                if nested_text and not body_text:
                    body_text = nested_text
                if nested_html and not body_html:
                    body_html = nested_html

        return body_text, body_html

    @staticmethod
    def _parse_address_list(raw: str) -> list[str]:
        if not raw:
            return []
        addresses = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', raw)
        return addresses

    @staticmethod
    def _has_attachments(payload: dict) -> bool:
        filename = payload.get("filename", "")
        if filename:
            return True
        for part in payload.get("parts", []):
            if part.get("filename"):
                return True
            if GoogleGmailProvider._has_attachments(part):
                return True
        return False
