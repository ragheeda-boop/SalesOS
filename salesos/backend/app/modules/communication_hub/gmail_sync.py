"""Gmail Sync Service — orchestrates Gmail email synchronization.

Flow:
  1. Fetch valid token from GoogleAccount (refresh if needed)
  2. Call Gmail API to list messages (incremental via historyId or time-based)
  3. Parse each message into RawEmail
  4. Upsert into employee_email_events (with company domain linking)
  5. Update GoogleAccount.history_id and last_sync_at

Note: ActivityRuntime / TimelineRuntime ingest is intentionally out of this
path until mapping confidence gates are production-validated. Downstream
Activity Intelligence APIs read employee_*_events directly.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.communication_hub.company_linker import resolve_company_ids_for_addresses
from app.modules.communication_hub.contact_sync import upsert_contacts_from_addresses
from app.modules.communication_hub.models import GoogleAccount
from app.modules.communication_hub.repository import GoogleAccountRepository
from app.modules.communication_hub.service import GoogleOAuthService
from intelligence.activity_intelligence.contracts.models import RawEmail
from intelligence.activity_intelligence.providers.google.gmail_provider import (
    GmailAPIError,
    GoogleGmailProvider,
)

logger = logging.getLogger(__name__)


class GmailSyncError(Exception):
    pass


class GmailSyncService:
    """Orchestrates Gmail email sync for a connected Google account."""

    def __init__(self, db: AsyncSession, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.repo = GoogleAccountRepository(db)
        self._oauth = GoogleOAuthService(db, tenant_id, user_id)
        self._provider: GoogleGmailProvider | None = None

    async def _ensure_provider(self, account: GoogleAccount) -> GoogleGmailProvider:
        token = await self._oauth.get_valid_token(account)
        provider = GoogleGmailProvider(access_token=token, email=account.email)
        self._provider = provider
        return provider

    async def sync(self, days_lookback: int = 30, max_results: int = 100) -> dict:
        account = await self.repo.get_by_user(self.tenant_id, self.user_id)
        if not account:
            raise GmailSyncError("No active Google account connected")

        provider = await self._ensure_provider(account)

        try:
            if account.history_id:
                result = await self._sync_incremental(account, provider)
            else:
                result = await self._sync_initial(account, provider, days_lookback, max_results)

            new_history_id = await provider.get_history_id()
            if new_history_id:
                await self.repo.update_history_id(
                    account.id, new_history_id, tenant_id=self.tenant_id
                )
            await self.repo.update_last_sync(account.id, tenant_id=self.tenant_id)
            await self.db.commit()

            return result
        except GmailAPIError as e:
            if e.status in (401, 403):
                raise GmailSyncError(f"Gmail API authentication failed: {e}") from e
            raise GmailSyncError(f"Gmail API error: {e}") from e
        finally:
            await provider.close()

    async def _sync_initial(
        self,
        account: GoogleAccount,
        provider: GoogleGmailProvider,
        days_lookback: int,
        max_results: int,
    ) -> dict:
        since = datetime.now(UTC) - timedelta(days=days_lookback)
        emails = await provider.fetch_emails(since=since, max_results=max_results)
        return await self._process_emails(account, emails)

    async def _sync_incremental(
        self,
        account: GoogleAccount,
        provider: GoogleGmailProvider,
    ) -> dict:
        try:
            history_data = await provider.fetch_history(account.history_id)
        except GmailAPIError as e:
            # 404 = unknown historyId; 410 = history expired / gone — both need full resync.
            if e.status in (404, 410):
                logger.warning(
                    "gmail.history_id.stale",
                    extra={
                        "account_id": str(account.id),
                        "history_id": account.history_id,
                        "status": e.status,
                    },
                )
                await self.repo.update_history_id(account.id, None, tenant_id=self.tenant_id)
                account.history_id = None
                since = account.last_sync_at or (datetime.now(UTC) - timedelta(days=30))
                emails = await provider.fetch_emails(since=since, max_results=200)
                return await self._process_emails(account, emails)
            raise

        message_ids: set[str] = set()
        for record in history_data.get("history", []):
            for msg in record.get("messagesAdded", []):
                mid = msg.get("message", {}).get("id")
                if mid:
                    message_ids.add(mid)

        emails: list[RawEmail] = []
        for mid in list(message_ids)[:200]:
            try:
                raw = await provider.fetch_message(mid)
                if raw:
                    emails.append(raw)
            except GmailAPIError:
                logger.warning("gmail.fetch_message.failed", extra={"message_id": mid})

        return await self._process_emails(account, emails)

    async def _process_emails(self, account: GoogleAccount, emails: list[RawEmail]) -> dict:
        new_count = 0
        updated_count = 0
        errors: list[str] = []
        contact_addresses: list[str] = []

        for raw in emails:
            try:
                direction = self._determine_direction(raw, account.email)
                is_read = "UNREAD" not in raw.labels

                existing = await self._get_existing_email(raw.message_id)
                if existing:
                    await self._update_email(existing["id"], raw, is_read)
                    updated_count += 1
                else:
                    await self._insert_email(account, raw, direction, is_read)
                    new_count += 1
                contact_addresses.extend(
                    [raw.from_address, *(raw.to_addresses or []), *(raw.cc_addresses or [])]
                )
            except Exception as e:
                errors.append(f"Email {raw.message_id}: {e}")
                logger.exception(
                    "gmail_sync.email.failed",
                    extra={"message_id": raw.message_id, "error": str(e)},
                )

        contacts = {"created": 0, "updated": 0, "skipped": 0}
        try:
            contacts = await upsert_contacts_from_addresses(
                self.db, self.tenant_id, contact_addresses, source="gmail_sync"
            )
        except Exception as e:
            errors.append(f"contact_sync: {e}")
            logger.exception("gmail_sync.contact_upsert.failed", extra={"error": str(e)})

        return {
            "synced_count": len(emails),
            "new_count": new_count,
            "updated_count": updated_count,
            "contacts": contacts,
            "errors": errors,
        }

    async def _insert_email(
        self,
        account: GoogleAccount,
        raw: RawEmail,
        direction: str,
        is_read: bool,
    ) -> None:
        body_preview = (raw.body_text or "")[:500]
        addresses = [raw.from_address, *(raw.to_addresses or []), *(raw.cc_addresses or [])]
        company_ids = await resolve_company_ids_for_addresses(self.db, self.tenant_id, addresses)
        account_domain = account.email.rsplit("@", 1)[-1].lower() if "@" in account.email else ""
        is_internal = _is_internal_email(raw, account_domain)

        await self.db.execute(
            sa_text("""
                INSERT INTO employee_email_events (
                    id, employee_id, tenant_id, provider, provider_message_id,
                    thread_id, in_reply_to, direction, from_address, to_addresses,
                    cc_addresses, bcc_addresses, subject, snippet, body_preview,
                    has_attachments, is_internal, is_read, labels, timestamp_utc,
                    related_company_ids, sync_history_id, last_synced_at, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :employee_id, :tenant_id, 'gmail', :provider_message_id,
                    :thread_id, :in_reply_to, :direction, :from_address,
                    CAST(:to_addresses AS jsonb), CAST(:cc_addresses AS jsonb),
                    CAST(:bcc_addresses AS jsonb), :subject, :snippet, :body_preview,
                    :has_attachments, :is_internal, :is_read, CAST(:labels AS jsonb),
                    :timestamp_utc, CAST(:related_company_ids AS jsonb),
                    :sync_history_id, now(), now(), now()
                )
            """),
            {
                "employee_id": str(self.user_id),
                "tenant_id": str(self.tenant_id),
                "provider_message_id": raw.message_id,
                "thread_id": raw.thread_id,
                "in_reply_to": raw.in_reply_to,
                "direction": direction,
                "from_address": raw.from_address,
                "to_addresses": json.dumps(raw.to_addresses or []),
                "cc_addresses": json.dumps(raw.cc_addresses or []),
                "bcc_addresses": json.dumps(raw.bcc_addresses or []),
                "subject": raw.subject or "",
                "snippet": (raw.body_text or "")[:200],
                "body_preview": body_preview,
                "has_attachments": bool(raw.attachments),
                "is_internal": is_internal,
                "is_read": is_read,
                "labels": json.dumps(raw.labels or []),
                "timestamp_utc": raw.sent_at or datetime.now(UTC),
                "related_company_ids": json.dumps(company_ids),
                "sync_history_id": None,
            },
        )

    async def _update_email(self, email_id: str, raw: RawEmail, is_read: bool) -> None:
        await self.db.execute(
            sa_text("""
                UPDATE employee_email_events
                SET labels = CAST(:labels AS jsonb),
                    is_read = :is_read,
                    last_synced_at = now(),
                    updated_at = now()
                WHERE id = :id AND tenant_id = :tenant_id
            """),
            {
                "id": email_id,
                "tenant_id": str(self.tenant_id),
                "labels": json.dumps(raw.labels or []),
                "is_read": is_read,
            },
        )

    async def _get_existing_email(self, provider_message_id: str) -> dict | None:
        result = await self.db.execute(
            sa_text("""
                SELECT id FROM employee_email_events
                WHERE tenant_id = :tenant_id
                  AND provider = 'gmail'
                  AND provider_message_id = :msg_id
                LIMIT 1
            """),
            {"tenant_id": str(self.tenant_id), "msg_id": provider_message_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    @staticmethod
    def _determine_direction(raw: RawEmail, account_email: str) -> str:
        from_email = raw.from_address.lower()
        account_lower = account_email.lower()
        if account_lower in from_email:
            return "outbound"
        return "inbound"


def _is_internal_email(raw: RawEmail, account_domain: str) -> bool:
    if not account_domain:
        return False
    domains: set[str] = set()
    for addr in [raw.from_address, *(raw.to_addresses or []), *(raw.cc_addresses or [])]:
        if addr and "@" in addr:
            domains.add(addr.rsplit("@", 1)[-1].lower())
    if not domains:
        return True
    return domains <= {account_domain}
