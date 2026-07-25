from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .models import EmployeeScore, EmployeeSignal
from .repository import EmployeeSignalRepository


class RiskFlag:
    DECLINING_SIGNALS = "declining_signals"
    LOW_ENGAGEMENT = "low_engagement"
    DECLINING_SCORE = "declining_score"


class EmployeePerformanceEngine:
    """Computes performance insights: trend, peer comparison, risk flags."""

    def __init__(self, repository: EmployeeSignalRepository):
        self._repository = repository

    async def compute_performance(
        self,
        employee_id: str,
        tenant_id: str,
        current_score: EmployeeScore | None = None,
        all_signals: list[EmployeeSignal] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)

        if all_signals is None:
            all_signals, _, _ = await self._repository.get_by_employee(
                employee_id, tenant_id, limit=500,
            )

        if current_score is None:
            current_score = await self._repository.get_latest_score(
                employee_id, tenant_id,
            )

        trend = await self._compute_trend(
            employee_id, tenant_id, current_score,
        )
        peer = await self._compute_peer_comparison(
            employee_id, tenant_id, current_score,
        )
        risk_flags = self._compute_risk_flags(
            all_signals, current_score, trend,
        )

        return {
            "trend": trend,
            "peer_comparison": peer,
            "risk_flags": risk_flags,
        }

    async def _compute_trend(
        self,
        employee_id: str,
        tenant_id: str,
        current_score: EmployeeScore | None,
    ) -> dict[str, Any]:
        if not current_score:
            return {
                "current_score": 0.0,
                "previous_score": 0.0,
                "delta": 0.0,
                "direction": "stable",
                "period_days": 30,
            }

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        old_signals, _, _ = await self._repository.get_by_employee(
            employee_id, tenant_id,
            until=thirty_days_ago, limit=500,
        )

        previous_score = 0.0
        if old_signals:
            from .scoring import EmployeeScoringEngine
            scorer = EmployeeScoringEngine(repository=self._repository)
            old_score = await scorer.compute_score(
                employee_id, tenant_id, old_signals,
            )
            previous_score = old_score.overall_score

        delta = current_score.overall_score - previous_score
        if delta > 0.02:
            direction = "improving"
        elif delta < -0.02:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "current_score": current_score.overall_score,
            "previous_score": round(previous_score, 4),
            "delta": round(delta, 4),
            "direction": direction,
            "period_days": 30,
        }

    async def _compute_peer_comparison(
        self,
        employee_id: str,
        tenant_id: str,
        current_score: EmployeeScore | None,
    ) -> dict[str, Any]:
        if not current_score:
            return {
                "employee_score": 0.0,
                "department_average": 0.0,
                "percentile": 0,
                "above_average": False,
            }

        peer_scores = await self._get_peer_scores(employee_id, tenant_id)

        if not peer_scores:
            return {
                "employee_score": current_score.overall_score,
                "department_average": current_score.overall_score,
                "percentile": 50,
                "above_average": True,
            }

        avg = sum(peer_scores) / len(peer_scores)
        above = current_score.overall_score >= avg
        below_count = sum(1 for s in peer_scores if s < current_score.overall_score)
        percentile = int((below_count / len(peer_scores)) * 100) if peer_scores else 50

        return {
            "employee_score": current_score.overall_score,
            "department_average": round(avg, 4),
            "percentile": percentile,
            "above_average": above,
        }

    async def _get_peer_scores(
        self, employee_id: str, tenant_id: str,
    ) -> list[float]:
        from sqlalchemy import select
        from app.modules.identity.models import User
        from .db_models import EmployeeScoreModel

        try:
            db_session = self._repository.db

            user_result = await db_session.execute(
                select(User).where(User.id == employee_id, User.tenant_id == tenant_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return []

            peers_result = await db_session.execute(
                select(User.id).where(
                    User.tenant_id == tenant_id,
                    User.role == user.role,
                    User.is_active == True,
                    User.id != employee_id,
                ).limit(50)
            )
            peer_ids = [str(row[0]) for row in peers_result.fetchall()]

            if not peer_ids:
                return []

            import uuid as uuid_mod
            scores_result = await db_session.execute(
                select(EmployeeScoreModel.overall_score).where(
                    EmployeeScoreModel.employee_id.in_([uuid_mod.UUID(pid) for pid in peer_ids]),
                    EmployeeScoreModel.tenant_id == uuid_mod.UUID(tenant_id),
                )
            )
            return [row[0] for row in scores_result.fetchall()]
        except Exception:
            return []

    def _compute_risk_flags(
        self,
        signals: list[EmployeeSignal],
        current_score: EmployeeScore | None,
        trend: dict[str, Any],
    ) -> list[dict[str, Any]]:
        flags = []
        now = datetime.now(timezone.utc)

        if len(signals) >= 2:
            sorted_signals = sorted(signals, key=lambda s: s.timestamp, reverse=True)
            recent_14d = [
                s for s in sorted_signals
                if (now - s.timestamp).total_seconds() < 14 * 86400
            ]
            older_14d = [
                s for s in sorted_signals
                if 14 * 86400 <= (now - s.timestamp).total_seconds() < 28 * 86400
            ]
            if older_14d and len(recent_14d) < len(older_14d) * 0.5:
                drop_pct = round(
                    (1 - len(recent_14d) / len(older_14d)) * 100, 1,
                )
                flags.append({
                    "flag": RiskFlag.DECLINING_SIGNALS,
                    "severity": "high",
                    "message": f"Signal volume dropped {drop_pct}% in last 14 days",
                    "detail": {
                        "recent_count": len(recent_14d),
                        "previous_count": len(older_14d),
                        "drop_percentage": drop_pct,
                    },
                })

        last_7d = [
            s for s in signals
            if (now - s.timestamp).total_seconds() < 7 * 86400
        ]
        if len(last_7d) < 3:
            flags.append({
                "flag": RiskFlag.LOW_ENGAGEMENT,
                "severity": "medium" if len(last_7d) > 0 else "high",
                "message": f"Low engagement: {len(last_7d)} signals in last 7 days (threshold: 3)",
                "detail": {
                    "recent_7d_count": len(last_7d),
                    "threshold": 3,
                },
            })

        if trend.get("direction") == "declining":
            delta = trend.get("delta", 0)
            flags.append({
                "flag": RiskFlag.DECLINING_SCORE,
                "severity": "high" if delta < -0.1 else "medium",
                "message": f"Score declined by {abs(delta):.2%} over {trend.get('period_days', 30)} days",
                "detail": {
                    "current_score": trend.get("current_score", 0),
                    "previous_score": trend.get("previous_score", 0),
                    "delta": delta,
                },
            })

        return flags
