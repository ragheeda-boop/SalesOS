"""
Celery Beat schedule for Employee 360 background tasks.

Register in celery_app.py:
    celery_app.conf.beat_schedule = BEAT_SCHEDULE

Or via command line:
    celery -A app.celery_app beat --loglevel=info
"""

from datetime import timedelta

from celery.schedules import crontab

BEAT_SCHEDULE = {
    # ── Calendar & Email Sync (Emp360 OAuth tokens) ────────────────
    "calendar-sync-every-15m": {
        "task": "calendar_sync_all",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 600, "retry": True, "max_retries": 3, "default_retry_delay": 300},
    },
    "email-sync-every-15m": {
        "task": "email_sync_all",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 600, "retry": True, "max_retries": 3, "default_retry_delay": 300},
    },
    # ── Communication Hub Google accounts ──────────────────────────
    "hub-gmail-sync-every-15m": {
        "task": "hub_gmail_sync_all",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 600, "retry": True, "max_retries": 3, "default_retry_delay": 300},
    },
    "hub-calendar-sync-every-15m": {
        "task": "hub_calendar_sync_all",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 600, "retry": True, "max_retries": 3, "default_retry_delay": 300},
    },
    # ── Webhook Renewal ────────────────────────────────────────
    "webhook-renewal-hourly": {
        "task": "webhook_renewal_all",
        "schedule": timedelta(hours=1),
        "options": {"expires": 300},
    },
    # ── Daily Scoring ──────────────────────────────────────────
    "score-rebuild-daily": {
        "task": "score_rebuild_all_employees",
        "schedule": crontab(hour=3, minute=0),
        "options": {"expires": 3600},
    },
    # ── Daily Cleanup ──────────────────────────────────────────
    "signal-cleanup-daily": {
        "task": "signal_retention_cleanup",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 600},
    },
    # ── GDPR Purge ─────────────────────────────────────────────
    "gdpr-purge-daily": {
        "task": "gdpr_purge_expired_users",
        "schedule": crontab(hour=4, minute=0),
        "options": {"expires": 1800},
    },
    # ── Health Check ───────────────────────────────────────────
    "worker-health-check": {
        "task": "worker_health_ping",
        "schedule": timedelta(minutes=5),
        "options": {"expires": 30},
    },
    # ── Retention ──────────────────────────────────────────────
    "calendar-event-cleanup-daily": {
        "task": "calendar_event_cleanup",
        "schedule": crontab(hour=2, minute=30),
        "options": {"expires": 600},
    },
    # ── Agent Runtime Dispatch ───────────────────────────────────
    "agent-dispatch-every-1m": {
        "task": "agent_dispatch_all",
        "schedule": timedelta(minutes=1),
        # expires < schedule so overlapping Beat ticks drop instead of stacking
        # under soft_time_limit=110 (IL-2B.2 dispatcher pile-up).
        "options": {"expires": 55},
    },
    # ── Odoo Integration Sync ───────────────────────────────────
    "odoo-sync-every-6h": {
        "task": "odoo_sync_all",
        "schedule": timedelta(hours=6),
        "options": {"expires": 1800},
    },
}
