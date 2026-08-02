"""STORY-11-01 — Deterministic ICP fit scoring (rules-based, not ML backtest).

Honesty: no historical won/lost Opportunity backtest claimed.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.gtm.icp import ICPCriteria, ICPError, ICPProfile, ICPWeights


def _norm(value: str) -> str:
    return (value or "").strip().lower()


@dataclass(frozen=True)
class ICPScoreResult:
    profile_id: str
    schema_version: int
    score: float
    max_score: float
    fit_ratio: float
    matched: dict[str, bool]
    company: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "schema_version": self.schema_version,
            "score": self.score,
            "max_score": self.max_score,
            "fit_ratio": self.fit_ratio,
            "matched": dict(self.matched),
            "company": dict(self.company),
        }


def score_company_against_profile(
    profile: ICPProfile,
    company: dict[str, Any],
) -> ICPScoreResult:
    """Score a firmographic company payload against a versioned ICPProfile."""
    if not isinstance(profile, ICPProfile):
        raise ICPError("profile required")
    if not isinstance(company, dict):
        raise ICPError("company payload required")

    criteria = profile.criteria
    weights = profile.weights
    industry = _norm(str(company.get("industry") or ""))
    city = _norm(str(company.get("city") or ""))
    title = _norm(str(company.get("title") or company.get("contact_title") or ""))
    blob = _norm(
        " ".join(
            str(company.get(k) or "")
            for k in ("name", "company_name", "description", "keywords", "notes")
        )
    )
    emp_raw = company.get("employees_count", company.get("employees"))
    try:
        emp = int(emp_raw) if emp_raw is not None else None
    except (TypeError, ValueError):
        emp = None

    matched: dict[str, bool] = {}
    earned = 0.0
    maximum = 0.0

    def _band(
        key: str,
        active: bool,
        weight: float,
        ok: bool,
    ) -> None:
        nonlocal earned, maximum
        if not active or weight <= 0:
            matched[key] = False
            return
        maximum += weight
        matched[key] = ok
        if ok:
            earned += weight

    _band(
        "industry",
        bool(criteria.industries),
        weights.industry,
        industry in criteria.industries if criteria.industries else False,
    )
    _band(
        "city",
        bool(criteria.cities),
        weights.city,
        city in criteria.cities if criteria.cities else False,
    )

    emp_active = criteria.employees_min is not None or criteria.employees_max is not None
    emp_ok = False
    if emp_active and emp is not None:
        emp_ok = True
        if criteria.employees_min is not None and emp < criteria.employees_min:
            emp_ok = False
        if criteria.employees_max is not None and emp > criteria.employees_max:
            emp_ok = False
    _band("employees", emp_active, weights.employees, emp_ok)

    title_ok = any(t in title for t in criteria.titles) if criteria.titles else False
    _band("titles", bool(criteria.titles), weights.titles, title_ok)

    kw_ok = any(k in blob for k in criteria.keywords) if criteria.keywords else False
    _band("keywords", bool(criteria.keywords), weights.keywords, kw_ok)

    # Empty ICP (no bands) → neutral full fit so profiles remain usable scaffolding.
    if maximum <= 0:
        maximum = 1.0
        earned = 1.0
        matched["empty_profile"] = True

    fit = earned / maximum if maximum else 0.0
    return ICPScoreResult(
        profile_id=profile.id,
        schema_version=profile.schema_version,
        score=round(earned, 4),
        max_score=round(maximum, 4),
        fit_ratio=round(fit, 4),
        matched=matched,
        company={
            "industry": industry,
            "city": city,
            "employees_count": emp,
            "title": title,
        },
    )


def assert_weights_usable(weights: ICPWeights) -> None:
    if sum(weights.as_dict().values()) <= 0:
        raise ICPError("at least one positive weight required")


# Re-export for type checkers / callers that need criteria shape.
__all__ = [
    "ICPCriteria",
    "ICPScoreResult",
    "assert_weights_usable",
    "score_company_against_profile",
]
