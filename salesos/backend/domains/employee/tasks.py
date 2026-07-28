"""Celery background tasks for Employee 360 — sync, scoring, cleanup.

Requires: Celery worker + Celery Beat scheduler + Redis/RabbitMQ broker.

Schedule (Celery Beat config):
  - calendar_sync_all:    every 15 minutes
  - email_sync_all:       every 15 minutes
  - webhook_renewal:      every 60 minutes
  - score_rebuild_daily:  daily at 03:00 UTC
  - signal_cleanup:       daily at 02:00 UTC
  - gdpr_purge:           daily at 04:00 UTC
  - retention_purge:      daily at 04:30 UTC
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from domains.employee.oauth_service import EmployeeOAuthToken, OAuthTokenService
from domains.employee.db_models import EmployeeSignalModel, EmployeeScoreModel
from domains.employee.intelligence_models import EmployeeCalendarEventModel, EmployeeEmailEventModel
from domains.employee.retention import (
    RETENTION_DAYS_SOFT_DELETED, RETENTION_DAYS_INACTIVE,
    is_eligible_for_purge,
)
from app.modules.identity.models import User


_engine = None
_engine_lock = None

_FREE_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "live.com", "icloud.com", "me.com", "aol.com", "proton.me", "protonmail.com",
}


async def _get_session() -> AsyncSession:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.resolved_database_url, echo=False,
            pool_size=5, max_overflow=10, pool_recycle=3600,
        )
    factory = async_sessionmaker(_engine, expire_on_commit=False)
    return factory()


def _extract_email_address(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip().lower()
    if "<" in value and ">" in value:
        value = value[value.rfind("<") + 1:value.rfind(">")].strip()
    if "@" not in value:
        return None
    return value


def _domain_of(email: str | None) -> str | None:
    addr = _extract_email_address(email)
    if not addr or "@" not in addr:
        return None
    domain = addr.split("@", 1)[1].lower()
    if domain in _FREE_EMAIL_DOMAINS:
        return None
    return domain


async def _resolve_related_company_ids(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    emails: list[str | None],
) -> list[str]:
    """Map participant emails to company IDs via contacts and company website/email domains."""
    addresses = [a for a in (_extract_email_address(e) for e in emails) if a]
    if not addresses:
        return []

    company_ids: set[str] = set()
    try:
        from app.modules.contact.models import Contact
        from app.modules.company.models import Company

        contact_rows = await db.execute(
            select(Contact.company_id).where(
                Contact.tenant_id == tenant_id,
                Contact.email.in_(addresses),
                Contact.company_id.isnot(None),
            )
        )
        for cid in contact_rows.scalars().all():
            if cid:
                company_ids.add(str(cid))

        domains = {_domain_of(a) for a in addresses}
        domains.discard(None)
        if domains:
            companies = await db.execute(
                select(Company.id, Company.website, Company.email).where(
                    Company.tenant_id == tenant_id,
                )
            )
            for row in companies.all():
                site = (row.website or "").lower()
                cemail = (row.email or "").lower()
                for domain in domains:
                    if domain and (domain in site or cemail.endswith("@" + domain)):
                        company_ids.add(str(row.id))
                        break
    except Exception:
        return list(company_ids)

    return list(company_ids)


# ── Calendar Sync ──────────────────────────────────────────────────

@shared_task(name="calendar_sync_all", bind=True, max_retries=3, default_retry_delay=300)
def calendar_sync_all_employees_task(self) -> dict:
    """Celery task: sync calendar for all employees."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(calendar_sync_all_employees())


async def calendar_sync_employee(employee_id: str, tenant_id: str, provider: str = "google") -> None:
    """Sync calendar events for one employee from specified provider."""
    db = await _get_session()
    record = None
    try:
        svc = OAuthTokenService(db)
        token = await svc.get_access_token(employee_id, provider)
        if not token:
            return

        sync_token_record = await db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.employee_id == uuid.UUID(employee_id),
                EmployeeOAuthToken.provider == provider,
                EmployeeOAuthToken.is_active == True,
            ).limit(1)
        )
        record = sync_token_record.scalar_one_or_none()

        if provider == "google":
            await _sync_google_calendar(db, employee_id, tenant_id, token, record)
        else:
            await _sync_microsoft_calendar(db, employee_id, tenant_id, token, record)

        if record:
            record.record_success()
            await db.flush()
        await db.commit()
    except Exception as exc:
        if record:
            record.record_failure(str(exc))
            await db.commit()
        raise
    finally:
        await db.close()


async def _sync_google_calendar(
    db: AsyncSession, employee_id: str, tenant_id: str, token: str, record: EmployeeOAuthToken | None,
) -> None:
    """Fetch Google Calendar events via Google Calendar API v3."""
    import httpx
    now = datetime.now(timezone.utc)
    time_min = (record.last_calendar_sync_at or now - timedelta(days=90)).isoformat()
    sync_token = record.calendar_sync_token if record else None

    params: dict[str, Any] = {"timeMin": time_min, "maxResults": 250, "singleEvents": "true", "orderBy": "startTime"}
    if sync_token:
        params["syncToken"] = sync_token
    else:
        params["showDeleted"] = "true"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        if resp.status_code == 410:
            await _sync_google_calendar(db, employee_id, tenant_id, token, None)
            return
        if resp.status_code != 200:
            raise Exception(f"Google Calendar API error: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        events = data.get("items", [])
        next_sync_token = data.get("nextSyncToken")

        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)
        for event in events:
            status = event.get("status", "")
            is_cancelled = status == "cancelled"
            start = event.get("start", {})
            end = event.get("end", {})
            start_dt = start.get("dateTime") or start.get("date")
            end_dt = end.get("dateTime") or end.get("date")

            attendee_emails = [a.get("email") for a in event.get("attendees", [])]
            attendee_emails.append(event.get("organizer", {}).get("email"))
            related_companies = await _resolve_related_company_ids(db, tid, attendee_emails)
            cal_event = EmployeeCalendarEventModel(
                id=uuid.uuid4(),
                employee_id=eid, tenant_id=tid, provider="google",
                provider_event_id=event.get("id", ""),
                title=event.get("summary", ""),
                start_utc=datetime.fromisoformat(start_dt) if start_dt else now,
                end_utc=datetime.fromisoformat(end_dt) if end_dt else now,
                is_cancelled=is_cancelled,
                is_recurring="recurringEventId" in event,
                recurrence_rule=event.get("recurrence", [None])[0],
                attendees_count=len(event.get("attendees", [])),
                is_internal=_all_internal_attendees(event.get("attendees", [])),
                conference_link=event.get("hangoutLink") or event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri"),
                organizer_email=event.get("organizer", {}).get("email"),
                response_status=event.get("attendees", [{}])[0].get("responseStatus", "accepted") if event.get("attendees") else "accepted",
                location=event.get("location"),
                related_company_ids=related_companies,
            )
            db.add(cal_event)

        if next_sync_token and record:
            record.calendar_sync_token = next_sync_token
            record.last_calendar_sync_at = now


async def _sync_microsoft_calendar(
    db: AsyncSession, employee_id: str, tenant_id: str, token: str, record: EmployeeOAuthToken | None,
) -> None:
    """Fetch Microsoft 365 Calendar events via Microsoft Graph delta API."""
    import httpx
    now = datetime.now(timezone.utc)
    delta_link = record.calendar_delta_link if record else None

    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {token}"}
        if delta_link:
            resp = await client.get(delta_link, headers=headers)
        else:
            start = (record.last_calendar_sync_at or now - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S")
            end_future = (now + timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S")
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me/calendarView/delta",
                headers=headers,
                params={
                    "startDateTime": start,
                    "endDateTime": end_future,
                },
            )
        if resp.status_code != 200:
            raise Exception(f"MS Graph API error: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        events = data.get("value", [])
        eid = uuid.UUID(employee_id)
        tid = uuid.UUID(tenant_id)

        for event in events:
            event_id = event.get("id", "")
            if not event_id:
                continue

            is_cancelled = event.get("isCancelled", False) or event.get("removed", {}).get("reason") is not None

            attendee_emails = [
                a.get("emailAddress", {}).get("address") for a in event.get("attendees", [])
            ]
            attendee_emails.append(event.get("organizer", {}).get("emailAddress", {}).get("address"))
            related_companies = await _resolve_related_company_ids(db, tid, attendee_emails)
            cal_event = EmployeeCalendarEventModel(
                id=uuid.uuid4(),
                employee_id=eid, tenant_id=tid, provider="microsoft",
                provider_event_id=event_id,
                title=event.get("subject", ""),
                start_utc=datetime.fromisoformat(event["start"]["dateTime"] + "Z") if event.get("start", {}).get("dateTime") else now,
                end_utc=datetime.fromisoformat(event["end"]["dateTime"] + "Z") if event.get("end", {}).get("dateTime") else now,
                is_cancelled=is_cancelled,
                is_recurring=event.get("type") == "seriesMaster",
                recurrence_rule=event.get("recurrence", {}).get("pattern", {}).get("type"),
                attendees_count=len(event.get("attendees", [])),
                is_internal=_all_internal_attendees(event.get("attendees", [])),
                conference_link=event.get("onlineMeeting", {}).get("joinUrl"),
                organizer_email=event.get("organizer", {}).get("emailAddress", {}).get("address"),
                location=event.get("location", {}).get("displayName"),
                related_company_ids=related_companies,
            )
            db.add(cal_event)

        next_delta_link = data.get("@odata.deltaLink")
        if next_delta_link and record:
            record.calendar_delta_link = next_delta_link
            record.last_calendar_sync_at = now


def _all_internal_attendees(attendees: list) -> bool:
    """Check if all attendees are from the same domain (internal meeting)."""
    if not attendees:
        return True
    domains = set()
    for a in attendees:
        email = a.get("email", "")
        if "@" in email:
            domains.add(email.split("@")[1].lower())
    return len(domains) <= 1


async def calendar_sync_all_employees() -> dict:
    """Sync calendar for all employees with active OAuth tokens."""
    db = await _get_session()
    try:
        result = await db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.is_active == True,
                EmployeeOAuthToken.is_connected == True,
            )
        )
        tokens = result.scalars().all()
        synced = 0
        failed = 0
        for t in tokens:
            try:
                await calendar_sync_employee(str(t.employee_id), str(t.tenant_id), t.provider)
                synced += 1
            except Exception:
                failed += 1
        return {"synced": synced, "failed": failed, "total": len(tokens)}
    finally:
        await db.close()


# ── Email Sync ─────────────────────────────────────────────────────

async def email_sync_employee(employee_id: str, tenant_id: str, provider: str = "google") -> None:
    """Sync email events for one employee."""
    db = await _get_session()
    record = None
    try:
        svc = OAuthTokenService(db)
        token = await svc.get_access_token(employee_id, provider)
        if not token:
            return
        result = await db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.employee_id == uuid.UUID(employee_id),
                EmployeeOAuthToken.provider == provider,
                EmployeeOAuthToken.is_active == True,
            ).limit(1)
        )
        record = result.scalar_one_or_none()
        if provider == "google":
            await _sync_gmail(db, employee_id, tenant_id, token, record)
        else:
            await _sync_outlook(db, employee_id, tenant_id, token)
        if record:
            record.record_success()
            await db.flush()
        await db.commit()
    except Exception as exc:
        if record:
            record.record_failure(str(exc)[:500])
            await db.commit()
        raise
    finally:
        await db.close()


async def _sync_gmail(
    db: AsyncSession,
    employee_id: str,
    tenant_id: str,
    token: str,
    record: EmployeeOAuthToken | None,
) -> None:
    """Sync Gmail via History API when possible; fall back to recent message list."""
    import httpx

    eid = uuid.UUID(employee_id)
    tid = uuid.UUID(tenant_id)
    history_id = record.email_history_id if record else None
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        message_ids: list[str] = []
        new_history_id: str | None = None

        if history_id:
            hist_resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/history",
                headers=headers,
                params={
                    "startHistoryId": history_id,
                    "historyTypes": "messageAdded",
                    "maxResults": 100,
                },
            )
            if hist_resp.status_code == 404:
                # History expired — full recent sync
                history_id = None
            elif hist_resp.status_code != 200:
                raise Exception(f"Gmail History API error: {hist_resp.status_code} {hist_resp.text[:200]}")
            else:
                hist_data = hist_resp.json()
                new_history_id = hist_data.get("historyId") or history_id
                for entry in hist_data.get("history", []):
                    for added in entry.get("messagesAdded", []):
                        msg = added.get("message") or {}
                        if msg.get("id"):
                            message_ids.append(msg["id"])

        if not history_id:
            list_resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers=headers,
                params={"maxResults": 100, "q": "newer_than:7d"},
            )
            if list_resp.status_code != 200:
                raise Exception(f"Gmail messages.list error: {list_resp.status_code} {list_resp.text[:200]}")
            list_data = list_resp.json()
            message_ids = [m["id"] for m in list_data.get("messages", []) if m.get("id")]
            profile = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                headers=headers,
            )
            if profile.status_code == 200:
                new_history_id = str(profile.json().get("historyId") or "")

        seen: set[str] = set()
        for msg_id in message_ids:
            if msg_id in seen:
                continue
            seen.add(msg_id)

            existing = await db.execute(
                select(EmployeeEmailEventModel.id).where(
                    EmployeeEmailEventModel.provider == "google",
                    EmployeeEmailEventModel.provider_message_id == msg_id,
                    EmployeeEmailEventModel.tenant_id == tid,
                ).limit(1)
            )
            if existing.scalar_one_or_none():
                continue

            detail = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                headers=headers,
                params={
                    "format": "metadata",
                    "metadataHeaders": "From,To,Cc,Subject,Date,Message-ID,In-Reply-To,References",
                },
            )
            if detail.status_code != 200:
                continue
            msg_data = detail.json()
            headers_map = {
                h["name"].lower(): h["value"]
                for h in msg_data.get("payload", {}).get("headers", [])
            }
            labels = msg_data.get("labelIds", [])
            ts = datetime.now(timezone.utc)
            if msg_data.get("internalDate"):
                try:
                    ts = datetime.fromtimestamp(int(msg_data["internalDate"]) / 1000, tz=timezone.utc)
                except (TypeError, ValueError):
                    pass

            related_companies = await _resolve_related_company_ids(
                db,
                tid,
                [headers_map.get("from"), headers_map.get("to"), headers_map.get("cc")],
            )
            email = EmployeeEmailEventModel(
                id=uuid.uuid4(),
                employee_id=eid,
                tenant_id=tid,
                provider="google",
                provider_message_id=msg_id,
                thread_id=msg_data.get("threadId"),
                in_reply_to=headers_map.get("in-reply-to"),
                direction="sent" if "SENT" in labels else "received",
                from_address=headers_map.get("from"),
                to_addresses=[headers_map.get("to", "")],
                subject=headers_map.get("subject", ""),
                snippet=msg_data.get("snippet", ""),
                timestamp_utc=ts,
                labels=labels,
                is_read="UNREAD" not in labels,
                sync_history_id=new_history_id,
                last_synced_at=datetime.now(timezone.utc),
                related_company_ids=related_companies,
            )
            db.add(email)

        if new_history_id and record:
            record.email_history_id = new_history_id
            record.last_email_sync_at = datetime.now(timezone.utc)


async def _sync_outlook(db: AsyncSession, employee_id: str, tenant_id: str, token: str) -> None:
    """Sync Outlook messages via Microsoft Graph API."""
    import httpx
    url = "https://graph.microsoft.com/v1.0/me/messages"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            url, headers={"Authorization": f"Bearer {token}"},
            params={"$top": 100, "$filter": "receivedDateTime ge 2026-01-01", "$orderby": "receivedDateTime desc"},
        )
        if resp.status_code != 200:
            return
        data = resp.json()
        for msg in data.get("value", []):
            to_addrs = [r.get("emailAddress", {}).get("address") for r in msg.get("toRecipients", [])]
            cc_addrs = [r.get("emailAddress", {}).get("address") for r in msg.get("ccRecipients", [])]
            from_addr = msg.get("from", {}).get("emailAddress", {}).get("address")
            related_companies = await _resolve_related_company_ids(
                db, uuid.UUID(tenant_id), [from_addr, *to_addrs, *cc_addrs]
            )
            email = EmployeeEmailEventModel(
                id=uuid.uuid4(),
                employee_id=uuid.UUID(employee_id), tenant_id=uuid.UUID(tenant_id), provider="microsoft",
                provider_message_id=msg.get("id"),
                thread_id=msg.get("conversationId"),
                direction="sent" if msg.get("sender", {}).get("emailAddress", {}).get("address", "").endswith("@") else "received",
                from_address=from_addr,
                to_addresses=to_addrs,
                cc_addresses=cc_addrs,
                subject=msg.get("subject"),
                snippet=msg.get("bodyPreview"),
                has_attachments=msg.get("hasAttachments", False),
                is_read=msg.get("isRead", True),
                timestamp_utc=datetime.fromisoformat(msg.get("receivedDateTime", "").replace("Z", "+00:00")),
                related_company_ids=related_companies,
            )
            db.add(email)


# ── Webhook Renewal ────────────────────────────────────────────────

async def webhook_renewal_all() -> dict:
    """Renew expiring webhook subscriptions for Google and Microsoft."""
    db = await _get_session()
    try:
        now = datetime.now(timezone.utc)
        soon = now + timedelta(hours=2)
        result = await db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.is_active == True,
                EmployeeOAuthToken.webhook_channel_id.isnot(None),
                EmployeeOAuthToken.webhook_expires_at <= soon,
            )
        )
        tokens = result.scalars().all()
        renewed = 0
        for t in tokens:
            try:
                await _renew_webhook(db, t)
                renewed += 1
            except Exception:
                pass
        return {"renewed": renewed, "total": len(tokens)}
    finally:
        await db.close()


async def _renew_webhook(db: AsyncSession, token: EmployeeOAuthToken) -> None:
    import httpx
    import uuid as uuid_mod
    new_channel = str(uuid_mod.uuid4())
    expiry = datetime.now(timezone.utc) + timedelta(hours=24)

    if token.provider == "google":
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch"
        access = await OAuthTokenService(db).get_access_token(str(token.employee_id), token.provider)
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, headers={"Authorization": f"Bearer {access}"}, json={
                "id": new_channel, "type": "web_hook", "address": f"{settings.BASE_URL}/api/v1/webhooks/google-calendar",
            })
    else:
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        access = await OAuthTokenService(db).get_access_token(str(token.employee_id), token.provider)
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, headers={"Authorization": f"Bearer {access}"}, json={
                "changeType": "created,updated,deleted",
                "notificationUrl": f"{settings.BASE_URL}/api/v1/webhooks/microsoft-calendar",
                "resource": "me/events",
                "expirationDateTime": expiry.isoformat(),
                "clientState": new_channel,
            })

    token.webhook_channel_id = new_channel
    token.webhook_expires_at = expiry
    await db.flush()


# ── Score Rebuild ──────────────────────────────────────────────────

async def score_rebuild_all_employees() -> dict:
    """Daily score recalculation for all active employees."""
    db = await _get_session()
    try:
        from domains.employee.scoring import EmployeeScoringEngine
        from domains.employee.postgres_repo import PostgresEmployeeSignalRepository

        repo = PostgresEmployeeSignalRepository(db)
        engine = EmployeeScoringEngine(repository=repo)

        users_result = await db.execute(
            select(User).where(User.is_active == True, User.deleted_at.is_(None))
        )
        users = users_result.scalars().all()

        scored = 0
        for user in users:
            try:
                await engine.compute_score(str(user.id), str(user.tenant_id))
                scored += 1
            except Exception:
                pass
        return {"scored": scored, "total": len(users)}
    finally:
        await db.close()


# ── Cleanup & Retention ────────────────────────────────────────────

async def gdpr_purge_expired_users() -> dict:
    """Hard-delete users whose deleted_at exceeds retention period."""
    db = await _get_session()
    try:
        from datetime import timezone as tz
        cutoff = datetime.now(tz.utc) - timedelta(days=RETENTION_DAYS_SOFT_DELETED)

        expired_result = await db.execute(
            select(User.id).where(
                User.deleted_at.isnot(None),
                User.deleted_at <= cutoff,
            )
        )
        expired_ids = [str(row[0]) for row in expired_result.fetchall()]
        if not expired_ids:
            return {"purged": 0}

        eids = [uuid.UUID(eid) for eid in expired_ids]
        await db.execute(delete(EmployeeSignalModel).where(EmployeeSignalModel.employee_id.in_(eids)))
        await db.execute(delete(EmployeeScoreModel).where(EmployeeScoreModel.employee_id.in_(eids)))
        await db.execute(delete(EmployeeCalendarEventModel).where(EmployeeCalendarEventModel.employee_id.in_(eids)))
        await db.execute(delete(EmployeeEmailEventModel).where(EmployeeEmailEventModel.employee_id.in_(eids)))
        await db.execute(delete(EmployeeOAuthToken).where(EmployeeOAuthToken.employee_id.in_(eids)))

        for eid in expired_ids:
            await db.execute(
                select(User).where(User.id == uuid.UUID(eid))
            )
            # Hard mask PII before user deletion
            user_result = await db.execute(select(User).where(User.id == uuid.UUID(eid)))
            user = user_result.scalar_one_or_none()
            if user:
                user.full_name = "[deleted]"
                user.full_name_ar = "[deleted]"
                user.email = f"deleted_{user.id}@purged.local"
                user.phone = None
                user.avatar_url = None
                user.preferences = {}
                await db.flush()

        await db.commit()
        return {"purged": len(expired_ids)}
    finally:
        await db.close()


async def signal_retention_cleanup() -> dict:
    """Remove orphaned signals for deleted employees."""
    db = await _get_session()
    try:
        active_ids = (await db.execute(select(User.id).where(User.deleted_at.is_(None)))).scalars().all()
        if not active_ids:
            return {"removed": 0}
        result = await db.execute(
            delete(EmployeeSignalModel).where(EmployeeSignalModel.employee_id.notin_(active_ids))
        )
        await db.commit()
        return {"removed": result.rowcount}
    finally:
        await db.close()


# ── Celery Task Wrappers (registered in Beat schedule) ────────────

@shared_task(name="email_sync_all", bind=True, max_retries=3, default_retry_delay=300)
def email_sync_all_task(self):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_email_sync_all_wrapper())


@shared_task(name="webhook_renewal_all", bind=True, max_retries=1)
def webhook_renewal_all_task(self):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(webhook_renewal_all())


@shared_task(name="score_rebuild_all_employees", bind=True, max_retries=1, time_limit=3600)
def score_rebuild_task(self):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(score_rebuild_all_employees())


@shared_task(name="gdpr_purge_expired_users", bind=True, max_retries=1, time_limit=1800)
def gdpr_purge_task(self):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(gdpr_purge_expired_users())


@shared_task(name="signal_retention_cleanup", bind=True, max_retries=1, time_limit=600)
def signal_cleanup_task(self):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(signal_retention_cleanup())


@shared_task(name="worker_health_ping", bind=True, max_retries=0)
def worker_health_ping_task(self) -> dict:
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_health_ping())


@shared_task(name="calendar_event_cleanup", bind=True, max_retries=1, time_limit=600)
def calendar_event_cleanup_task(self):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_calendar_cleanup())


async def _calendar_cleanup() -> dict:
    """Remove calendar events older than 365 days."""
    db = await _get_session()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        result = await db.execute(
            delete(EmployeeCalendarEventModel).where(
                EmployeeCalendarEventModel.start_utc < cutoff,
            )
        )
        await db.commit()
        return {"removed": result.rowcount, "older_than_days": 365}
    finally:
        await db.close()


async def _email_sync_all_wrapper() -> dict:
    db = await _get_session()
    try:
        result = await db.execute(
            select(EmployeeOAuthToken).where(
                EmployeeOAuthToken.is_active == True,
                EmployeeOAuthToken.is_connected == True,
            )
        )
        tokens = result.scalars().all()
        synced = 0
        failed = 0
        for t in tokens:
            try:
                await email_sync_employee(str(t.employee_id), str(t.tenant_id), t.provider)
                synced += 1
            except Exception:
                failed += 1
        return {"synced": synced, "failed": failed, "total": len(tokens)}
    finally:
        await db.close()


async def _health_ping() -> dict:
    try:
        db = await _get_session()
        await db.execute(select(func.now()))
        await db.close()
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "database": "connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
