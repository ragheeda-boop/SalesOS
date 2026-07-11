"""Health Score Algorithm for Customer Success Portal.

Formula: 40% Feature Adoption + 30% Search Success + 30% NBA Acceptance
Thresholds: >80 Green, >50 Yellow, <50 Red
Renewal Risk: if health < 50 for 30+ days, flag as high risk
"""

from datetime import datetime, timedelta, timezone
from typing import Any


def compute_health_score(
    feature_adoption_pct: float,
    search_success_rate: float,
    nba_acceptance_rate: float,
    low_health_since: datetime | None = None,
) -> dict[str, Any]:
    score = round(
        0.4 * feature_adoption_pct
        + 0.3 * search_success_rate
        + 0.3 * nba_acceptance_rate,
        1,
    )

    if score > 80:
        status = "healthy"
        color = "green"
    elif score > 50:
        status = "warning"
        color = "yellow"
    else:
        status = "critical"
        color = "red"

    renewal_risk = False
    days_in_low_health = 0
    if low_health_since and score < 50:
        days_in_low_health = (datetime.now(timezone.utc) - low_health_since).days
        if days_in_low_health >= 30:
            renewal_risk = True

    return {
        "score": score,
        "status": status,
        "color": color,
        "components": {
            "feature_adoption": {"weight": 0.4, "value": feature_adoption_pct, "contribution": round(0.4 * feature_adoption_pct, 1)},
            "search_success": {"weight": 0.3, "value": search_success_rate, "contribution": round(0.3 * search_success_rate, 1)},
            "nba_acceptance": {"weight": 0.3, "value": nba_acceptance_rate, "contribution": round(0.3 * nba_acceptance_rate, 1)},
        },
        "renewal_risk": renewal_risk,
        "days_in_low_health": days_in_low_health,
    }


def compute_tenant_health(
    tenant_id: str,
    tenant_name: str,
    feature_adoption_pct: float,
    search_success_rate: float,
    nba_acceptance_rate: float,
    low_health_since: datetime | None = None,
    user_count: int = 0,
    last_active: str | None = None,
) -> dict[str, Any]:
    health = compute_health_score(
        feature_adoption_pct,
        search_success_rate,
        nba_acceptance_rate,
        low_health_since,
    )
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant_name,
        **health,
        "user_count": user_count,
        "last_active": last_active,
    }
