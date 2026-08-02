"""STORY-06-03 — Quota evaluation (pure).

Compares Plan.entitlements quotas to UsageMeter snapshots.
Clear over-quota contract (403/429). Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.admin.entitlements import EntitlementQuotas, PlanEntitlements, parse_entitlements


@dataclass(frozen=True)
class QuotaLimit:
    metric: str
    limit: int
    unlimited: bool = False


@dataclass(frozen=True)
class QuotaViolation:
    metric: str
    used: float
    limit: int
    status_code: int


# Rate-like counters use 429; capacity gauges use 403 (PROGRAM_PLAN 402/403 family).
_STATUS_BY_METRIC: dict[str, int] = {
    "seats": 403,
    "connectors": 403,
    "storage_mb": 403,
    "ai_tokens": 429,
    "api_calls": 429,
}


def limits_from_entitlements(
    entitlements: PlanEntitlements | dict[str, Any],
) -> dict[str, QuotaLimit]:
    doc = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    q: EntitlementQuotas = doc.quotas
    connectors_limit = int(q.connectors)
    connectors_unlimited = bool(q.connectors_unlimited)
    dom021 = doc.domains.get("DOM-021")
    if dom021 is not None:
        if dom021.unlimited:
            connectors_unlimited = True
        elif dom021.quota is not None:
            # Domain quota is the tighter commercial connector cap when set.
            connectors_limit = (
                min(connectors_limit, int(dom021.quota))
                if connectors_limit > 0
                else int(dom021.quota)
            )

    return {
        "seats": QuotaLimit(metric="seats", limit=int(q.seats)),
        "ai_tokens": QuotaLimit(
            metric="ai_tokens",
            limit=int(q.ai_tokens_monthly),
            unlimited=bool(q.ai_tokens_unlimited),
        ),
        "connectors": QuotaLimit(
            metric="connectors",
            limit=connectors_limit,
            unlimited=connectors_unlimited,
        ),
        "storage_mb": QuotaLimit(metric="storage_mb", limit=int(q.storage_mb)),
        "api_calls": QuotaLimit(metric="api_calls", limit=int(q.api_calls_monthly)),
    }


def evaluate_quota_violations(
    *,
    limits: dict[str, QuotaLimit],
    usage: dict[str, float],
    metrics: tuple[str, ...] | list[str],
) -> list[QuotaViolation]:
    """Return violations for requested metrics where used > limit (unless unlimited)."""
    out: list[QuotaViolation] = []
    for metric in metrics:
        key = str(metric).strip().lower()
        lim = limits.get(key)
        if lim is None or lim.unlimited:
            continue
        used = float(usage.get(key, 0.0) or 0.0)
        if used < 0:
            used = 0.0
        # limit 0 = hard deny on any attempt; otherwise block at/above capacity.
        exceeded = lim.limit <= 0 or used >= float(lim.limit)
        if exceeded:
            out.append(
                QuotaViolation(
                    metric=key,
                    used=used,
                    limit=int(lim.limit),
                    status_code=_STATUS_BY_METRIC.get(key, 403),
                )
            )
    return out


def over_quota_payload(
    violation: QuotaViolation,
    *,
    period: str | None = None,
    plan_id: str | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    detail = (
        f"Plan quota exceeded: {violation.metric} "
        f"(used {violation.used:g} / limit {violation.limit}). "
        "Upgrade plan or reduce usage."
    )
    body: dict[str, Any] = {
        "detail": detail,
        "error": "quota_exceeded",
        "metric": violation.metric,
        "used": violation.used,
        "limit": violation.limit,
    }
    if period:
        body["period"] = period
    if plan_id:
        body["plan_id"] = plan_id
    if tier:
        body["tier"] = tier
    return body
