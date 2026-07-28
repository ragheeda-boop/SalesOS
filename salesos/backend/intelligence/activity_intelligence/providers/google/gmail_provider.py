"""Google Gmail Provider — EmailProvider implementation (ADR-012 §7, Phase 1).

Uses Google Gmail API via httpx (no google-api-python-client required).
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from intelligence.activity_intelligence.contracts.models import RawEmail
from intelligence.activity_intelligence.contracts.provider import (
    EmailProvider,
    ProviderProfile,
)


class GoogleGmailProvider(EmailProvider):
    """Gmail API email provider using OAuth access tokens."""

    def __init__(self, credentials: dict | None = None):
        self._credentials = credentials or {}
        self._authenticated = False
        self._profile: ProviderProfile | None = None
        self._access_token: str | None = None

    async def authenticate(self, credentials: dict) -> bool:
        self._credentials = credentials
        token = credentials.get("access_token") or credentials.get("token")
        if not token:
            self._authenticated = False
            return False
        self._access_token = token
        self._authenticated = True
        self._profile = ProviderProfile(
            provider_id="gmail",
            provider_type="email",
            email=credentials.get("email", ""),
            display_name=credentials.get("display_name", ""),
            connected=True,
        )
        return True

    async def fetch_emails(
        self, since: datetime | None = None, max_results: int = 50
    ) -> list[RawEmail]:
        if not self._authenticated or not self._access_token:
            return []

        params: dict = {"maxResults": max_results}
        if since:
            # Gmail q uses epoch seconds for after:
            params["q"] = f"after:{int(since.timestamp())}"

        headers = {"Authorization": f"Bearer {self._access_token}"}
        emails: list[RawEmail] = []
        async with httpx.AsyncClient(timeout=30) as client:
            listing = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers=headers,
                params=params,
            )
            if listing.status_code != 200:
                return []
            for item in listing.json().get("messages", []):
                detail = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}",
                    headers=headers,
                    params={
                        "format": "metadata",
                        "metadataHeaders": "From,To,Cc,Subject,Date,Message-ID,In-Reply-To,References",
                    },
                )
                if detail.status_code != 200:
                    continue
                msg = detail.json()
                hdrs = {
                    h["name"].lower(): h["value"]
                    for h in msg.get("payload", {}).get("headers", [])
                }
                received_at = None
                if msg.get("internalDate"):
                    try:
                        received_at = datetime.fromtimestamp(
                            int(msg["internalDate"]) / 1000, tz=timezone.utc
                        )
                    except (TypeError, ValueError):
                        received_at = None
                emails.append(
                    RawEmail(
                        message_id=item["id"],
                        thread_id=msg.get("threadId"),
                        subject=hdrs.get("subject", ""),
                        from_address=hdrs.get("from", ""),
                        to_addresses=[a.strip() for a in hdrs.get("to", "").split(",") if a.strip()],
                        cc_addresses=[a.strip() for a in hdrs.get("cc", "").split(",") if a.strip()],
                        body_text=msg.get("snippet", ""),
                        in_reply_to=hdrs.get("in-reply-to"),
                        references=hdrs.get("references"),
                        received_at=received_at,
                        labels=msg.get("labelIds", []),
                        headers=hdrs,
                    )
                )
        return emails

    async def fetch_thread(self, thread_id: str) -> list[RawEmail]:
        if not self._authenticated or not self._access_token:
            return []
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}",
                headers=headers,
                params={"format": "metadata"},
            )
            if resp.status_code != 200:
                return []
            emails: list[RawEmail] = []
            for msg in resp.json().get("messages", []):
                hdrs = {
                    h["name"].lower(): h["value"]
                    for h in msg.get("payload", {}).get("headers", [])
                }
                emails.append(
                    RawEmail(
                        message_id=msg.get("id", ""),
                        thread_id=thread_id,
                        subject=hdrs.get("subject", ""),
                        from_address=hdrs.get("from", ""),
                        to_addresses=[a.strip() for a in hdrs.get("to", "").split(",") if a.strip()],
                        body_text=msg.get("snippet", ""),
                        labels=msg.get("labelIds", []),
                        headers=hdrs,
                    )
                )
            return emails

    async def send_email(self, to: str, subject: str, body: str) -> str:
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        # Read-only Gmail scope in Hub OAuth — sending intentionally unsupported.
        raise NotImplementedError("Gmail send requires gmail.send scope (not granted)")

    async def get_profile(self) -> ProviderProfile:
        return self._profile or ProviderProfile(
            provider_id="gmail",
            provider_type="email",
            connected=self._authenticated,
        )
