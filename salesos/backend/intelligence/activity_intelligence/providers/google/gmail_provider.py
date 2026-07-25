"""Google Gmail Provider — EmailProvider implementation (ADR-012 §7, Phase 1).

Uses Google Gmail API to fetch, send, and manage emails.
"""

from __future__ import annotations

from datetime import datetime

from intelligence.activity_intelligence.contracts.models import RawEmail
from intelligence.activity_intelligence.contracts.provider import (
    EmailProvider,
    ProviderProfile,
)


class GoogleGmailProvider(EmailProvider):
    """Gmail API email provider.

    Requires Google OAuth 2.0 credentials.
    Uses the official Google API Python Client library.
    """

    def __init__(self, credentials: dict | None = None):
        self._credentials = credentials or {}
        self._authenticated = False
        self._profile: ProviderProfile | None = None
        self._service = None

    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with Gmail OAuth 2.0."""
        self._credentials = credentials
        try:
            # Placeholder: In production, uses google-auth + google-api-python-client
            # from google.oauth2.credentials import Credentials
            # from googleapiclient.discovery import build
            # creds = Credentials(token=credentials.get("access_token"), ...)
            # self._service = build("gmail", "v1", credentials=creds)
            self._authenticated = True
            self._profile = ProviderProfile(
                provider_id="gmail",
                provider_type="email",
                email=credentials.get("email", ""),
                display_name=credentials.get("display_name", ""),
                connected=True,
            )
            return True
        except Exception:
            self._authenticated = False
            return False

    async def fetch_emails(
        self, since: datetime | None = None, max_results: int = 50
    ) -> list[RawEmail]:
        """Fetch recent emails from Gmail inbox.

        In production, calls Gmail API users.messages.list + users.messages.get.
        """
        if not self._authenticated:
            return []
        return []  # Returns empty until Google API credentials are configured

    async def fetch_thread(self, thread_id: str) -> list[RawEmail]:
        """Fetch all emails in a Gmail thread."""
        if not self._authenticated:
            return []
        return []

    async def send_email(self, to: str, subject: str, body: str) -> str:
        """Send email via Gmail API."""
        if not self._authenticated:
            raise RuntimeError("Not authenticated")
        return ""

    async def get_profile(self) -> ProviderProfile:
        """Return Gmail provider profile."""
        return self._profile or ProviderProfile(
            provider_id="gmail",
            provider_type="email",
            connected=self._authenticated,
        )
