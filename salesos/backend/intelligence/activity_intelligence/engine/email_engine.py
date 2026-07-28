"""Email Engine — email intelligence and metrics (ADR-012 §3).

Provides:
- Reply detection
- Thread analysis
- Email counting and metrics
"""

from __future__ import annotations

from datetime import datetime, timezone


class EmailEngine:
    """Computes email intelligence from the email domain."""

    def __init__(self, email_reader=None):
        self._reader = email_reader

    async def get_count(
        self, company_id: str, tenant_id: str, direction: str | None = None
    ) -> int:
        """Get email count for a company."""
        if self._reader:
            return await self._reader.count_by_company(company_id, tenant_id, direction)
        return 0

    async def get_last_email(
        self, company_id: str, tenant_id: str
    ) -> dict | None:
        """Get the most recent email for a company."""
        if self._reader:
            return await self._reader.last_email(company_id, tenant_id)
        return None

    async def get_reply_rate(
        self, company_id: str, tenant_id: str
    ) -> float:
        """Thread-based reply rate: inbound threads that also have outbound.

        Falls back to inbound/total only when the reader cannot expose thread data.
        """
        if not self._reader:
            return 0.0

        # Prefer reader SQL if available via count + list heuristic is weak;
        # use inbound/total only as last resort (documented as volume share).
        if hasattr(self._reader, "db"):
            from sqlalchemy import text as sa_text

            row = (
                await self._reader.db.execute(
                    sa_text("""
                        SELECT
                            COUNT(*) FILTER (WHERE has_in) AS inbound_threads,
                            COUNT(*) FILTER (WHERE has_in AND has_out) AS replied_threads
                        FROM (
                            SELECT thread_id,
                                   bool_or(direction IN ('inbound', 'received')) AS has_in,
                                   bool_or(direction IN ('outbound', 'sent')) AS has_out
                            FROM employee_email_events
                            WHERE tenant_id = :tid
                              AND related_company_ids @> to_jsonb(:company_id::text)
                              AND thread_id IS NOT NULL AND thread_id <> ''
                            GROUP BY thread_id
                        ) t
                    """),
                    {"tid": tenant_id, "company_id": company_id},
                )
            ).mappings().one()
            inbound_threads = int(row["inbound_threads"] or 0)
            if inbound_threads == 0:
                return 0.0
            return round(int(row["replied_threads"] or 0) / inbound_threads, 4)

        total = await self._reader.count_by_company(company_id, tenant_id)
        if total == 0:
            return 0.0
        received = await self._reader.count_by_company(
            company_id, tenant_id, direction="inbound"
        )
        return round(received / total, 4)

    async def get_email_metrics(
        self, company_id: str, tenant_id: str
    ) -> dict:
        """Get comprehensive email metrics for a company."""
        sent = await self.get_count(company_id, tenant_id, "outbound")
        received = await self.get_count(company_id, tenant_id, "inbound")
        reply_rate = await self.get_reply_rate(company_id, tenant_id)
        last = await self.get_last_email(company_id, tenant_id)

        last_days = None
        if last and last.get("sent_at"):
            last_date = last["sent_at"]
            if isinstance(last_date, str):
                last_date = datetime.fromisoformat(last_date.replace("Z", "+00:00"))
            last_days = (datetime.now(timezone.utc) - last_date).days

        return {
            "company_id": company_id,
            "email_count_sent": sent,
            "email_count_received": received,
            "reply_rate": reply_rate,
            "last_email_days": last_days,
        }
