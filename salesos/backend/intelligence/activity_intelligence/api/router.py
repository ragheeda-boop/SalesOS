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
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    fourteen_days_ago = now - timedelta(days=14)
    seven_days_ago = now - timedelta(days=7)

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

    top_total_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) AS c FROM (
                SELECT company_id
                FROM employee_email_events e
                CROSS JOIN LATERAL jsonb_array_elements_text(e.related_company_ids) AS company_id
                WHERE e.tenant_id = :tid AND e.timestamp_utc >= :since
                  AND e.related_company_ids != '[]'::jsonb
                GROUP BY company_id
            ) t
        """),
        {"tid": tenant_id, "since": thirty_days_ago},
    )).mappings().one()

    top_companies = (await db.execute(
        sa_text("""
            SELECT
                company_id::text AS company_id,
                COALESCE(c.name_en, c.name_ar, '') AS name,
                COUNT(*) as email_count
            FROM employee_email_events e
            CROSS JOIN LATERAL jsonb_array_elements_text(e.related_company_ids) AS company_id
            LEFT JOIN companies c
              ON c.id::text = company_id AND c.tenant_id = e.tenant_id
            WHERE e.tenant_id = :tid AND e.timestamp_utc >= :since
              AND e.related_company_ids != '[]'::jsonb
            GROUP BY company_id, c.name_en, c.name_ar
            ORDER BY email_count DESC
            LIMIT :lim OFFSET :off
        """),
        {
            "tid": tenant_id,
            "since": thirty_days_ago,
            "lim": limit,
            "off": offset,
        },
    )).mappings().all()

    followup_row = (await db.execute(
        sa_text("""
            SELECT
                COUNT(*) FILTER (WHERE last_outbound < :since7) AS need_followup,
                COUNT(*) FILTER (WHERE last_outbound < :since14) AS overdue
            FROM (
                SELECT employee_id, MAX(timestamp_utc) AS last_outbound
                FROM employee_email_events
                WHERE tenant_id = :tid AND direction = 'outbound'
                GROUP BY employee_id
            ) s
            WHERE last_outbound < :since7
        """),
        {"tid": tenant_id, "since7": seven_days_ago, "since14": fourteen_days_ago},
    )).mappings().one()
    need_followup = int(followup_row["need_followup"] or 0)
    overdue_count = int(followup_row["overdue"] or 0)

    engagement_trend = (await db.execute(
        sa_text("""
            SELECT DATE(timestamp_utc) AS day, COUNT(*) AS count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
            GROUP BY day
            ORDER BY day
            LIMIT :lim OFFSET :off
        """),
        {
            "tid": tenant_id,
            "since": thirty_days_ago,
            "lim": limit,
            "off": offset,
        },
    )).mappings().all()

    return {
        "email_count": email_row["total"],
        "email_inbound": email_row["inbound"],
        "email_outbound": email_row["outbound"],
        "meeting_count": cal_row["total"],
        "meeting_active": cal_row["active"],
        "meeting_cancelled": cal_row["cancelled"],
        "meeting_hours": round((cal_row["total_minutes"] or 0) / 60, 1),
        "followup_count": need_followup,
        "overdue_count": overdue_count,
        "top_companies": [
            {
                "company_id": str(r["company_id"]),
                "name": r["name"] or "",
                "count": r["email_count"],
            }
            for r in top_companies
        ],
        "top_companies_total": int(top_total_row["c"] or 0),
        "engagement_trend": [
            {"date": str(r["day"]), "value": r["count"]} for r in engagement_trend
        ],
        "limit": limit,
        "offset": offset,
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
    params: dict = {"tid": tenant_id, "since": since}
    if employee_id:
        params["eid"] = employee_id

    if employee_id:
        count_sql = sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound,
                   COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound,
                   COUNT(CASE WHEN has_attachments THEN 1 END) as with_attachments,
                   COUNT(CASE WHEN is_read THEN 1 END) as read_count,
                   COUNT(CASE WHEN NOT is_read THEN 1 END) as unread_count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since AND employee_id = :eid
        """)
        reply_sql = sa_text("""
            SELECT
                COUNT(*) FILTER (WHERE has_in) AS inbound_threads,
                COUNT(*) FILTER (WHERE has_in AND has_out) AS replied_threads
            FROM (
                SELECT thread_id,
                       bool_or(direction IN ('inbound', 'received')) AS has_in,
                       bool_or(direction IN ('outbound', 'sent')) AS has_out
                FROM employee_email_events
                WHERE tenant_id = :tid AND timestamp_utc >= :since
                  AND thread_id IS NOT NULL AND thread_id <> ''
                  AND employee_id = :eid
                GROUP BY thread_id
            ) t
        """)
        avg_sql = sa_text("""
            SELECT AVG(EXTRACT(EPOCH FROM (first_out - first_in)) / 3600.0) AS avg_hours
            FROM (
                SELECT thread_id,
                       MIN(timestamp_utc) FILTER (
                         WHERE direction IN ('inbound', 'received')
                       ) AS first_in,
                       MIN(timestamp_utc) FILTER (
                         WHERE direction IN ('outbound', 'sent')
                       ) AS first_out
                FROM employee_email_events
                WHERE tenant_id = :tid AND timestamp_utc >= :since
                  AND thread_id IS NOT NULL AND thread_id <> ''
                  AND employee_id = :eid
                GROUP BY thread_id
            ) t
            WHERE first_in IS NOT NULL AND first_out IS NOT NULL AND first_out >= first_in
        """)
        top_sql = sa_text("""
            SELECT company_id::text AS company_id,
                   COALESCE(c.name_en, c.name_ar, '') AS name,
                   COUNT(*) AS email_count
            FROM employee_email_events e
            CROSS JOIN LATERAL jsonb_array_elements_text(e.related_company_ids) AS company_id
            LEFT JOIN companies c
              ON c.id::text = company_id AND c.tenant_id = e.tenant_id
            WHERE e.tenant_id = :tid AND e.timestamp_utc >= :since
              AND e.related_company_ids != '[]'::jsonb
              AND e.employee_id = :eid
            GROUP BY company_id, c.name_en, c.name_ar
            ORDER BY email_count DESC
            LIMIT 10
        """)
        daily_sql = sa_text("""
            SELECT DATE(timestamp_utc) as day, COUNT(*) as count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since AND employee_id = :eid
            GROUP BY day ORDER BY day
        """)
    else:
        count_sql = sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as inbound,
                   COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as outbound,
                   COUNT(CASE WHEN has_attachments THEN 1 END) as with_attachments,
                   COUNT(CASE WHEN is_read THEN 1 END) as read_count,
                   COUNT(CASE WHEN NOT is_read THEN 1 END) as unread_count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
        """)
        reply_sql = sa_text("""
            SELECT
                COUNT(*) FILTER (WHERE has_in) AS inbound_threads,
                COUNT(*) FILTER (WHERE has_in AND has_out) AS replied_threads
            FROM (
                SELECT thread_id,
                       bool_or(direction IN ('inbound', 'received')) AS has_in,
                       bool_or(direction IN ('outbound', 'sent')) AS has_out
                FROM employee_email_events
                WHERE tenant_id = :tid AND timestamp_utc >= :since
                  AND thread_id IS NOT NULL AND thread_id <> ''
                GROUP BY thread_id
            ) t
        """)
        avg_sql = sa_text("""
            SELECT AVG(EXTRACT(EPOCH FROM (first_out - first_in)) / 3600.0) AS avg_hours
            FROM (
                SELECT thread_id,
                       MIN(timestamp_utc) FILTER (
                         WHERE direction IN ('inbound', 'received')
                       ) AS first_in,
                       MIN(timestamp_utc) FILTER (
                         WHERE direction IN ('outbound', 'sent')
                       ) AS first_out
                FROM employee_email_events
                WHERE tenant_id = :tid AND timestamp_utc >= :since
                  AND thread_id IS NOT NULL AND thread_id <> ''
                GROUP BY thread_id
            ) t
            WHERE first_in IS NOT NULL AND first_out IS NOT NULL AND first_out >= first_in
        """)
        top_sql = sa_text("""
            SELECT company_id::text AS company_id,
                   COALESCE(c.name_en, c.name_ar, '') AS name,
                   COUNT(*) AS email_count
            FROM employee_email_events e
            CROSS JOIN LATERAL jsonb_array_elements_text(e.related_company_ids) AS company_id
            LEFT JOIN companies c
              ON c.id::text = company_id AND c.tenant_id = e.tenant_id
            WHERE e.tenant_id = :tid AND e.timestamp_utc >= :since
              AND e.related_company_ids != '[]'::jsonb
            GROUP BY company_id, c.name_en, c.name_ar
            ORDER BY email_count DESC
            LIMIT 10
        """)
        daily_sql = sa_text("""
            SELECT DATE(timestamp_utc) as day, COUNT(*) as count
            FROM employee_email_events
            WHERE tenant_id = :tid AND timestamp_utc >= :since
            GROUP BY day ORDER BY day
        """)

    row = (await db.execute(count_sql, params)).mappings().one()

    # Thread-based reply rate: inbound threads that also have outbound.
    reply_row = (await db.execute(reply_sql, params)).mappings().one()
    inbound_threads = int(reply_row["inbound_threads"] or 0)
    replied_threads = int(reply_row["replied_threads"] or 0)
    reply_rate = round(replied_threads / inbound_threads, 4) if inbound_threads else 0.0

    # Avg hours from first inbound to first subsequent outbound in same thread.
    avg_resp = (await db.execute(avg_sql, params)).mappings().one()
    avg_hours = avg_resp["avg_hours"]
    avg_response_hours = round(float(avg_hours), 2) if avg_hours is not None else None

    top_companies = (await db.execute(top_sql, params)).mappings().all()
    daily = (await db.execute(daily_sql, params)).mappings().all()

    outbound = int(row["outbound"] or 0)
    inbound = int(row["inbound"] or 0)

    return {
        "total": row["total"],
        "total_sent": outbound,
        "total_received": inbound,
        "inbound": inbound,
        "outbound": outbound,
        "reply_rate": reply_rate,
        "reply_rate_definition": "replied_inbound_threads / inbound_threads",
        "outbound_inbound_ratio": round(outbound / max(1, inbound), 4),
        "avg_response_hours": avg_response_hours,
        "with_attachments": row["with_attachments"],
        "read_count": row["read_count"],
        "unread_count": row["unread_count"],
        "top_companies": [
            {
                "company_id": str(r["company_id"]),
                "name": r["name"] or "",
                "count": r["email_count"],
            }
            for r in top_companies
        ],
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
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    params: dict = {"tid": tenant_id, "since": since, "now": now}
    if employee_id:
        params["eid"] = employee_id

    if employee_id:
        count_sql = sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_cancelled = false THEN 1 END) as active,
                   COUNT(CASE WHEN is_cancelled = true THEN 1 END) as cancelled,
                   COALESCE(SUM(duration_minutes), 0) as total_minutes,
                   COALESCE(AVG(duration_minutes), 0) as avg_minutes,
                   COUNT(CASE WHEN is_internal THEN 1 END) as internal,
                   COUNT(CASE WHEN NOT is_internal THEN 1 END) as external
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND start_utc >= :since AND employee_id = :eid
        """)
        upcoming_sql = sa_text("""
            SELECT id::text, title, start_utc, end_utc, duration_minutes, location
            FROM employee_calendar_events
            WHERE tenant_id = :tid
              AND is_cancelled = false
              AND start_utc >= :now
              AND employee_id = :eid
            ORDER BY start_utc ASC
            LIMIT 10
        """)
    else:
        count_sql = sa_text("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_cancelled = false THEN 1 END) as active,
                   COUNT(CASE WHEN is_cancelled = true THEN 1 END) as cancelled,
                   COALESCE(SUM(duration_minutes), 0) as total_minutes,
                   COALESCE(AVG(duration_minutes), 0) as avg_minutes,
                   COUNT(CASE WHEN is_internal THEN 1 END) as internal,
                   COUNT(CASE WHEN NOT is_internal THEN 1 END) as external
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND start_utc >= :since
        """)
        upcoming_sql = sa_text("""
            SELECT id::text, title, start_utc, end_utc, duration_minutes, location
            FROM employee_calendar_events
            WHERE tenant_id = :tid
              AND is_cancelled = false
              AND start_utc >= :now
            ORDER BY start_utc ASC
            LIMIT 10
        """)

    row = (await db.execute(count_sql, params)).mappings().one()
    upcoming = (await db.execute(upcoming_sql, params)).mappings().all()

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
        "upcoming": [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "start_utc": str(r["start_utc"]),
                "end_utc": str(r["end_utc"]),
                "duration_minutes": r["duration_minutes"],
                "location": r["location"],
            }
            for r in upcoming
        ],
        "period": f"{days}d",
    }


# ── Follow-ups ─────────────────────────────────────────────────────

@router.get("/followups", response_model=dict)
async def get_followups(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    stale = (await db.execute(
        sa_text("""
            SELECT employee_id,
                   last_activity,
                   last_direction,
                   EXTRACT(EPOCH FROM (:now - last_activity)) / 86400.0 AS last_outbound_days
            FROM (
                SELECT employee_id,
                       MAX(timestamp_utc) AS last_activity,
                       (ARRAY_AGG(direction ORDER BY timestamp_utc DESC))[1] AS last_direction
                FROM employee_email_events
                WHERE tenant_id = :tid
                GROUP BY employee_id
            ) s
            WHERE last_activity < :since7
            ORDER BY last_activity ASC
            LIMIT :lim OFFSET :off
        """),
        {
            "tid": tenant_id,
            "since7": seven_days_ago,
            "now": now,
            "lim": limit,
            "off": offset,
        },
    )).mappings().all()

    counts = (await db.execute(
        sa_text("""
            SELECT
                COUNT(*) FILTER (WHERE last_activity < :since7) AS need_followup,
                COUNT(*) FILTER (WHERE last_activity < :since14) AS overdue,
                COUNT(*) FILTER (
                    WHERE last_activity < :since7
                      AND last_direction IN ('inbound', 'received')
                ) AS waiting_you,
                COUNT(*) FILTER (
                    WHERE last_activity < :since7
                      AND last_direction IN ('outbound', 'sent')
                ) AS waiting_customer
            FROM (
                SELECT employee_id,
                       MAX(timestamp_utc) AS last_activity,
                       (ARRAY_AGG(direction ORDER BY timestamp_utc DESC))[1] AS last_direction
                FROM employee_email_events
                WHERE tenant_id = :tid
                GROUP BY employee_id
            ) s
        """),
        {"tid": tenant_id, "since7": seven_days_ago, "since14": fourteen_days_ago},
    )).mappings().one()

    need_followup = int(counts["need_followup"] or 0)
    overdue = int(counts["overdue"] or 0)
    waiting_you = int(counts["waiting_you"] or 0)
    waiting_customer = int(counts["waiting_customer"] or 0)

    items = []
    for r in stale:
        days = float(r["last_outbound_days"] or 0)
        is_overdue = days >= 14
        last_dir = (r["last_direction"] or "").lower()
        wait_you = last_dir in ("inbound", "received")
        priority = "high" if is_overdue else ("medium" if days >= 10 else "low")
        items.append(
            {
                # Company linkage not derived from employee-level stale query yet.
                "company_id": None,
                "company_id_available": False,
                "assigned": False,
                "need_followup": True,
                "waiting_customer": not wait_you and last_dir in ("outbound", "sent"),
                "waiting_you": wait_you,
                "overdue": is_overdue,
                "last_outbound_days": round(days, 1),
                "priority": priority,
                "priority_definition": "high>=14d, medium>=10d, else low (days since last activity)",
                "employee_id": str(r["employee_id"]),
                "last_outbound": str(r["last_activity"]),
            }
        )

    return {
        "total": need_followup,
        "overdue": overdue,
        "need_followup": need_followup,
        "waiting_you": waiting_you,
        "waiting_customer": waiting_customer,
        "stale_count": need_followup,
        "stale_employees": [
            {"employee_id": str(r["employee_id"]), "last_outbound": str(r["last_activity"])}
            for r in stale
        ],
        "items": items,
        "limit": limit,
        "offset": offset,
    }


# ── Engagement ─────────────────────────────────────────────────────

@router.get("/engagement", response_model=dict)
async def get_engagement_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    employee_rows = (await db.execute(
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

    company_rows = (await db.execute(
        sa_text("""
            SELECT company_id::text AS company_id,
                   COALESCE(c.name_en, c.name_ar, '') AS name,
                   COUNT(*) AS email_count
            FROM employee_email_events e
            CROSS JOIN LATERAL jsonb_array_elements_text(e.related_company_ids) AS company_id
            LEFT JOIN companies c
              ON c.id::text = company_id AND c.tenant_id = e.tenant_id
            WHERE e.tenant_id = :tid AND e.timestamp_utc >= :since
              AND e.related_company_ids != '[]'::jsonb
            GROUP BY company_id, c.name_en, c.name_ar
            ORDER BY email_count DESC
            LIMIT 20
        """),
        {"tid": tenant_id, "since": since},
    )).mappings().all()

    totals = (await db.execute(
        sa_text("""
            SELECT
                (
                    SELECT COUNT(DISTINCT company_id)
                    FROM employee_email_events e
                    CROSS JOIN LATERAL jsonb_array_elements_text(e.related_company_ids)
                        AS company_id
                    WHERE e.tenant_id = :tid AND e.timestamp_utc >= :since
                      AND e.related_company_ids != '[]'::jsonb
                ) AS total_companies,
                (
                    SELECT COUNT(DISTINCT employee_id)
                    FROM employee_email_events
                    WHERE tenant_id = :tid AND timestamp_utc >= :since
                ) AS total_employees
        """),
        {"tid": tenant_id, "since": since},
    )).mappings().one()

    total_companies = int(totals["total_companies"] or 0)
    total_employees = int(totals["total_employees"] or 0)
    active_companies = len([r for r in company_rows if r["email_count"] > 0])
    # Honest: health / stagnant not modeled yet — expose null / unavailable, not fake zeros.
    return {
        "total_companies": total_companies,
        "total_employees": total_employees,
        # Backward-compatible alias: older clients misread total_companies as employees.
        "total_companies_definition": "distinct companies linked via related_company_ids",
        "active_companies": active_companies,
        "avg_relationship_health": None,
        "relationship_health_available": False,
        "stagnant_companies": None,
        "stagnant_companies_available": False,
        "top_engaged": [
            {
                "company_id": str(r["company_id"]),
                "name": r["name"] or "",
                "health": None,
                "health_available": False,
                "email_count": r["email_count"],
            }
            for r in company_rows[:5]
        ],
        "employees": [
            {
                "employee_id": str(r["employee_id"]),
                "email_count": r["email_count"],
                "inbound": r["inbound"],
                "outbound": r["outbound"],
            }
            for r in employee_rows
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
    offset: int = Query(0, ge=0),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    params = {
        "tid": tenant_id,
        "eid": employee_id,
        "since": since,
        "lim": limit,
        "off": offset,
    }

    total_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) AS c
            FROM employee_email_events
            WHERE tenant_id = :tid AND employee_id = :eid AND timestamp_utc >= :since
        """),
        params,
    )).mappings().one()

    rows = (await db.execute(
        sa_text("""
            SELECT id, provider_message_id, direction, from_address,
                   to_addresses, subject, snippet, has_attachments,
                   is_read, timestamp_utc, labels
            FROM employee_email_events
            WHERE tenant_id = :tid AND employee_id = :eid AND timestamp_utc >= :since
            ORDER BY timestamp_utc DESC
            LIMIT :lim OFFSET :off
        """),
        params,
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
        "total": int(total_row["c"] or 0),
        "limit": limit,
        "offset": offset,
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
    offset: int = Query(0, ge=0),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    params = {
        "tid": tenant_id,
        "eid": employee_id,
        "since": since,
        "lim": limit,
        "off": offset,
    }

    total_row = (await db.execute(
        sa_text("""
            SELECT COUNT(*) AS c
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND employee_id = :eid AND start_utc >= :since
        """),
        params,
    )).mappings().one()

    rows = (await db.execute(
        sa_text("""
            SELECT id, provider_event_id, title, start_utc, end_utc,
                   duration_minutes, is_cancelled, is_internal,
                   attendees_count, organizer_email, location,
                   conference_link, response_status
            FROM employee_calendar_events
            WHERE tenant_id = :tid AND employee_id = :eid AND start_utc >= :since
            ORDER BY start_utc DESC
            LIMIT :lim OFFSET :off
        """),
        params,
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
        "total": int(total_row["c"] or 0),
        "limit": limit,
        "offset": offset,
        "period": f"{days}d",
    }
