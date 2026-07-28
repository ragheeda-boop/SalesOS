"""Activity Intelligence API — REST endpoints (ADR-012 §9).

All consumers (Dashboard, Company 360, Employee 360, Opportunity 360,
AI Copilot) use these endpoints.

Routes:
  GET /api/v1/activity/dashboard          — Tenant-wide activity summary
  GET /api/v1/activity/company/{id}       — Per-company engagement
  GET /api/v1/activity/email              — Email metrics
  GET /api/v1/activity/calendar           — Calendar metrics
  GET /api/v1/activity/followups          — Follow-up dashboard
  GET /api/v1/activity/engagement         — Engagement summary
  GET /api/v1/activity/employee/{id}/email     — Employee email events
  GET /api/v1/activity/employee/{id}/calendar  — Employee calendar events
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session

router = APIRouter(
    prefix="/api/v1/activity",
    tags=["Activity Intelligence"],
)


# ── Dashboard ──────────────────────────────────────────────────────

@router.get("/dashboard", response_model=dict)
async def get_dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    email_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound,
                   COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
        """),
        {"tid": tenant_id, "since": thirty_days_ago},
    )).mappings().one()

    cal_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_cancelled = false THEN 1 END) as active,
                   COUNT(CASE WHEN is_cancelled = true THEN 1 END) as cancelled,
                   COALESCE(SUM(duration_minutes), 0) as total_minutes
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND start_utc >= :since
        """),
        {"tid": tenant_id, "since": thirty_days_ago},
    )).mappings().one()

    top_companies = (await db.execute(
        sa_text("""
            SELECT
                unnest(related_company_ids) as company_id,
                COUNT(*) as email_count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
              AND related_company_ids != '[]'::jsonb
            GROUP BY company_id
            ORDER BY email_count DESC
            LIMIT 10
        """),
        {"tid": tenant_id, "since": thirty_days_ago},
    )).mappings().all()

    followup_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) AS stale_count
            FROM (
                SELECT employee_id
                FROM employee_email_events
                WHERE tenant_id = :tid AND direction = 'outbound'
                GROUP BY employee_id
                HAVING MAX(timestamp_utc) < :since7
            ) s
        """),
        {"tid": tenant_id, "since7": now - timedelta(days=7)},
    )).mappings().one()
    followup_count = followup_row["stale_count"] or 0
    overdue_count = followup_count

    engagement_trend = (await db.execute(
        sa_text("""
            SELECT DATE(timestamp_utc) AS day, COUNT(*) AS count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
            GROUP BY day
            ORDER BY day
        """),
        {"tid": tenant_id, "since": thirty_days_ago},
    )).mappings().all()

    return {
        "email_count": email_row["total"],
        "email_inbound": email_row["inbound"],
        "email_outbound": email_row["outbound"],
        "meeting_count": cal_row["total"],
        "meeting_active": cal_row["active"],
        "meeting_cancelled": cal_row["cancelled"],
        "meeting_hours": round((cal_row["total_minutes"] or 0) / 60, 1),
        "followup_count": followup_count,
        "overdue_count": overdue_count,
        "top_companies": [
            {
                "company_id": str(r["company_id"]),
                "name": "",
                "count": r["email_count"],
            }
            for r in top_companies
        ],
        "engagement_trend": [
            {"date": str(r["day"]), "value": r["count"]} for r in engagement_trend
        ],
        "period": "30d",
    }


# ── Company Engagement ─────────────────────────────────────────────

@router.get("/company/{company_id}", response_model=dict)
async def get_company_engagement(
    company_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    email_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound,
                   COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound,
                   MAX(timestamp_utc) as last_email
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
              AND related_company_ids @> to_jsonb(:company_id::text)
        """),
        {"tid": tenant_id, "since": since, "company_id": company_id},
    )).mappings().one()

    cal_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(duration_minutes), 0) as total_minutes,
                   MAX(start_utc) as last_meeting
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND start_utc >= :since
              AND related_company_ids @> to_jsonb(:company_id::text)
        """),
        {"tid": tenant_id, "since": since, "company_id": company_id},
    )).mappings().one()

    last_email = email_row["last_email"]
    last_meeting = cal_row["last_meeting"]
    last_activity = None
    if last_email and last_meeting:
        last_activity = max(last_email, last_meeting)
    else:
        last_activity = last_email or last_meeting

    return {
        "company_id": company_id,
        "email_count": email_row["total"],
        "email_inbound": email_row["inbound"],
        "email_outbound": email_row["outbound"],
        "meeting_count": cal_row["total"],
        "meeting_hours": round((cal_row["total_minutes"] or 0) / 60, 1),
        "last_email": str(last_email) if last_email else None,
        "last_meeting": str(last_meeting) if last_meeting else None,
        "last_activity": str(last_activity) if last_activity else None,
        "followup_status": (
            "overdue"
            if last_email and last_email < since
            else "ok"
        ),
        "period": f"{days}d",
    }


# ── Email Metrics ──────────────────────────────────────────────────

@router.get("/email", response_model=dict)
async def get_email_metrics(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
    employee_id: str | None = Query(None),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    conditions = "tenant_id = :tid AND timestamp_utc >= :since"
    params: dict = {"tid": tenant_id, "since": since}
    if employee_id:
        conditions += " AND employee_id = :eid"
        params["eid"] = employee_id

    row = (await db.execute(
        sa_text(f"""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound,
                   COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound,
                   COUNT(CASE WHEN has_attachments THEN 1 END) as with_attachments,
                   COUNT(CASE WHEN is_read THEN 1 END) as read_count,
                   COUNT(CASE WHEN NOT is_read THEN 1 END) as unread_count
            FROM employee_email_events
            WHERE {conditions}
        """),
        params,
    )).mappings().one()

    daily = (await db.execute(
        sa_text(f"""
            SELECT DATE(timestamp_utc) as day, COUNT(*) as count
            FROM employee_email_events
            WHERE {conditions}
            GROUP BY day ORDER BY day
        """),
        params,
    )).mappings().all()

    return {
        "total": row["total"],
        "total_sent": row["outbound"],
        "total_received": row["inbound"],
        "inbound": row["inbound"],
        "outbound": row["outbound"],
        "reply_rate": round((row["outbound"] or 0) / max(1, row["inbound"] or 0), 4),
        "avg_response_hours": None,
        "with_attachments": row["with_attachments"],
        "read_count": row["read_count"],
        "unread_count": row["unread_count"],
        "top_companies": [],
        "daily": [{"date": str(r["day"]), "count": r["count"]} for r in daily],
        "period": f"{days}d",
    }


# ── Calendar Metrics ───────────────────────────────────────────────

@router.get("/calendar", response_model=dict)
async def get_calendar_metrics(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
    employee_id: str | None = Query(None),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    conditions = "tenant_id = :tid AND start_utc >= :since"
    params: dict = {"tid": tenant_id, "since": since}
    if employee_id:
        conditions += " AND employee_id = :eid"
        params["eid"] = employee_id

    row = (await db.execute(
        sa_text(f"""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_cancelled = false THEN 1 END) as active,
                   COUNT(CASE WHEN is_cancelled = true THEN 1 END) as cancelled,
                   COALESCE(SUM(duration_minutes), 0) as total_minutes,
                   COALESCE(AVG(duration_minutes), 0) as avg_minutes,
                   COUNT(CASE WHEN is_internal THEN 1 END) as internal,
                   COUNT(CASE WHEN NOT is_internal THEN 1 END) as external
            FROM employee_calendar_events
            WHERE {conditions}
        """),
        params,
    )).mappings().one()

    return {
        "total": row["total"],
        "total_events": row["total"],
        "meeting_count": row["active"],
        "active": row["active"],
        "cancelled": row["cancelled"],
        "total_hours": round((row["total_minutes"] or 0) / 60, 1),
        "avg_duration_minutes": round(row["avg_minutes"] or 0),
        "avg_minutes": round(row["avg_minutes"] or 0),
        "internal": row["internal"],
        "external": row["external"],
        "upcoming": [],
        "period": f"{days}d",
    }


# ── Follow-ups ─────────────────────────────────────────────────────

@router.get("/followups", response_model=dict)
async def get_followups(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    stale = (await db.execute(
        sa_text("""
            SELECT employee_id, MAX(timestamp_utc) as last_activity
            FROM employee_email_events
            WHERE tenant_id = :tid AND direction = 'outbound'
            GROUP BY employee_id
            HAVING MAX(timestamp_utc) < :since
            ORDER BY last_activity ASC
            LIMIT 20
        """),
        {"tid": tenant_id, "since": seven_days_ago},
    )).mappings().all()

    return {
        "total": len(stale),
        "overdue": len(stale),
        "need_followup": len(stale),
        "waiting_you": 0,
        "waiting_customer": 0,
        "stale_count": len(stale),
        "stale_employees": [
            {"employee_id": str(r["employee_id"]), "last_outbound": str(r["last_activity"])}
            for r in stale
        ],
        "items": [
            {
                "company_id": "",
                "assigned": False,
                "need_followup": True,
                "waiting_customer": False,
                "waiting_you": True,
                "overdue": True,
                "last_outbound_days": None,
                "priority": "high",
                "employee_id": str(r["employee_id"]),
                "last_outbound": str(r["last_activity"]),
            }
            for r in stale
        ],
    }


# ── Engagement ─────────────────────────────────────────────────────

@router.get("/engagement", response_model=dict)
async def get_engagement_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (await db.execute(
        sa_text("""
            SELECT employee_id,
                   COUNT(*) as email_count,
                   COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound,
                   COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
            GROUP BY employee_id
            ORDER BY email_count DESC
            LIMIT 20
        """),
        {"tid": tenant_id, "since": since},
    )).mappings().all()

    return {
        "total_companies": len(rows),
        "active_companies": len([r for r in rows if r["email_count"] > 0]),
        "avg_relationship_health": 0,
        "stagnant_companies": 0,
        "top_engaged": [
            {
                "company_id": "",
                "name": str(r["employee_id"]),
                "health": 0,
                "employee_id": str(r["employee_id"]),
                "email_count": r["email_count"],
            }
            for r in rows[:5]
        ],
        "employees": [
            {
                "employee_id": str(r["employee_id"]),
                "email_count": r["email_count"],
                "inbound": r["inbound"],
                "outbound": r["outbound"],
            }
            for r in rows
        ],
        "period": f"{days}d",
    }


# ── Employee Email Events ──────────────────────────────────────────

@router.get("/employee/{employee_id}/email", response_model=dict)
async def get_employee_email_events(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (await db.execute(
        sa_text("""
            SELECT id, provider_message_id, direction, from_address,
                   to_addresses, subject, snippet, has_attachments,
                   is_read, timestamp_utc, labels
            FROM employee_email_events
            WHERE tenant_id = :tid AND employee_id = :eid AND timestamp_utc >= :since
            ORDER BY timestamp_utc DESC
            LIMIT :lim
        """),
        {"tid": tenant_id, "eid": employee_id, "since": since, "lim": limit},
    )).mappings().all()

    return {
        "employee_id": employee_id,
        "events": [
            {
                "id": str(r["id"]),
                "provider_message_id": r["provider_message_id"],
                "direction": r["direction"],
                "from_address": r["from_address"],
                "to_addresses": r["to_addresses"],
                "subject": r["subject"],
                "snippet": r["snippet"],
                "has_attachments": r["has_attachments"],
                "is_read": r["is_read"],
                "timestamp": str(r["timestamp_utc"]),
                "labels": r["labels"],
            }
            for r in rows
        ],
        "total": len(rows),
        "period": f"{days}d",
    }


# ── Employee Calendar Events ───────────────────────────────────────

@router.get("/employee/{employee_id}/calendar", response_model=dict)
async def get_employee_calendar_events(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (await db.execute(
        sa_text("""
            SELECT id, provider_event_id, title, start_utc, end_utc,
                   duration_minutes, is_cancelled, is_internal,
                   attendees_count, organizer_email, location,
                   conference_link, response_status
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND employee_id = :eid AND start_utc >= :since
            ORDER BY start_utc DESC
            LIMIT :lim
        """),
        {"tid": tenant_id, "eid": employee_id, "since": since, "lim": limit},
    )).mappings().all()

    return {
        "employee_id": employee_id,
        "events": [
            {
                "id": str(r["id"]),
                "provider_event_id": r["provider_event_id"],
                "title": r["title"],
                "start_utc": str(r["start_utc"]),
                "end_utc": str(r["end_utc"]),
                "duration_minutes": r["duration_minutes"],
                "is_cancelled": r["is_cancelled"],
                "is_internal": r["is_internal"],
                "attendees_count": r["attendees_count"],
                "organizer_email": r["organizer_email"],
                "location": r["location"],
                "conference_link": r["conference_link"],
                "response_status": r["response_status"],
            }
            for r in rows
        ],
        "total": len(rows),
        "period": f"{days}d",
    }
