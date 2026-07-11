"""Deal Health computer — Feature Store computer for opportunity health scoring."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from runtime.feature_store import FeatureComputer, FeatureResult


class DealHealthComputer(FeatureComputer):
    """Computes deal health score for an opportunity based on stagnation,
    engagement, competition, and timeline factors."""

    name: str = "deal_health"
    version: int = 1

    async def compute(self, opportunity: dict[str, Any], session: Any) -> FeatureResult:
        from sqlalchemy import text as sa_text

        opp_id = opportunity.get("id", "")
        tenant_id = opportunity.get("tenant_id", "")

        # Get recent activities
        rows = await session.execute(
            sa_text("""
                SELECT COUNT(*) as total,
                       MAX(timestamp) as last_activity
                FROM activity_records
                WHERE entity_id = :eid AND tenant_id = :tid
            """),
            {"eid": opp_id, "tid": tenant_id},
        )
        r = rows.mappings().one()
        total_activities = r["total"] or 0
        last_activity = r["last_activity"]

        # Stagnation score
        stagnation = 0
        if last_activity:
            days_since = (datetime.now(timezone.utc) - last_activity).days
            if days_since > 14:
                stagnation = min(1.0, days_since / 30)
        else:
            stagnation = 0.5  # No activity at all

        # Engagement score
        engagement = min(1.0, total_activities / 20)

        # Timeline pressure
        close_date = opportunity.get("expected_close_date")
        timeline_risk = 0
        if close_date:
            days_to_close = (close_date - datetime.now(timezone.utc).date()).days
            if days_to_close < 0:
                timeline_risk = 1.0  # Overdue
            elif days_to_close < 7:
                timeline_risk = 0.5
            elif days_to_close < 30:
                timeline_risk = 0.2

        # Composite score: lower = healthier, higher = more risk
        risk_score = stagnation * 0.4 + (1 - engagement) * 0.3 + timeline_risk * 0.3
        health_score = max(0, 1 - risk_score)

        # Signal detection
        signals = await session.execute(
            sa_text("""
                SELECT COUNT(*) as cnt FROM company_signals s
                JOIN commercial_opportunities o ON o.company_id = s.company_id
                WHERE o.id = :oid AND s.created_at >= :d30
            """),
            {"oid": opp_id, "d30": datetime.now(timezone.utc) - timedelta(days=30)},
        )
        signal_count = signals.mappings().one()["cnt"] or 0

        contributing_signals = {
            "stagnation": round(stagnation, 2),
            "engagement": round(engagement, 2),
            "timeline_risk": round(timeline_risk, 2),
            "signal_count": signal_count,
            "days_since_last_activity": (datetime.now(timezone.utc) - last_activity).days if last_activity else -1,
            "total_activities": total_activities,
        }

        if health_score >= 0.7:
            explanation = "حالة الفرصة جيدة — لا توجد مؤشرات خطر"
        elif health_score >= 0.4:
            explanation = "حالة الفرصة متوسطة — يوجد مؤشرات خطر تحتاج مراقبة"
        else:
            explanation = "حالة الفرصة حرجة — تحتاج تدخل فوري"

        return FeatureResult(
            score=health_score,
            version=self.version,
            computed_at=datetime.now(timezone.utc),
            confidence=0.8,
            contributing_signals=contributing_signals,
            explanation=explanation,
        )
