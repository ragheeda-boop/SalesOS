"""Feature computer implementations — ICP, Funding, Hiring, Growth, Intent, Expansion, Revenue."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.feature_store import FeatureComputer, FeatureResult


class IcpComputer(FeatureComputer):
    """Ideal Customer Profile score (0-100).

    Factors:
      - Industry alignment     (max 30 pts)
      - Company size match     (max 25 pts)
      - Geographic proximity   (max 20 pts)
      - Revenue range match    (max 25 pts)
    """

    name = "icp_score"
    version = 1

    # Industries considered high-ICP for SalesOS
    HIGH_ICP_INDUSTRIES = {
        "technology", "software", "saas", "information technology",
        "telecommunications", "financial services", "banking",
        "insurance", "healthcare", "pharmaceuticals",
        "professional services", "consulting", "real estate",
        "construction", "manufacturing",
    }

    MODERATE_ICP_INDUSTRIES = {
        "retail", "e-commerce", "wholesale", "logistics",
        "transportation", "education", "hospitality",
    }

    EMPLOYEE_TIERS = {
        (1, 10): 40,
        (11, 50): 60,
        (51, 200): 85,
        (201, 1000): 100,
        (1001, 5000): 80,
        (5001, 999999): 50,
    }

    REVENUE_TIERS = {
        (0, 500000): 30,
        (500001, 2000000): 50,
        (2000001, 10000000): 75,
        (10000001, 50000000): 100,
        (50000001, 200000000): 80,
        (200000001, 999999999999): 60,
    }

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        # Industry alignment (30 pts)
        industry = (company.get("industry") or "").lower()
        if industry in self.HIGH_ICP_INDUSTRIES:
            score += 30
            signals["industry_match"] = "high"
        elif industry in self.MODERATE_ICP_INDUSTRIES:
            score += 15
            signals["industry_match"] = "moderate"
        else:
            signals["industry_match"] = "low"

        # Employee count (25 pts)
        employee_count = company.get("employee_count") or 0
        try:
            emp = int(employee_count)
            for (lo, hi), pts in self.EMPLOYEE_TIERS.items():
                if lo <= emp <= hi:
                    score += 25 * (pts / 100)
                    signals["employee_tier"] = f"{lo}-{hi}"
                    break
        except (ValueError, TypeError):
            signals["employee_tier"] = "unknown"

        # Geographic proximity — prefer Saudi Arabia / GCC (20 pts)
        country = (company.get("country") or "").lower()
        if country in ("saudi arabia", "sa"):
            score += 20
            signals["region"] = "primary"
        elif country in ("uae", "united arab emirates", "kuwait", "qatar", "bahrain", "oman"):
            score += 12
            signals["region"] = "gcc"
        else:
            signals["region"] = "other"

        # Revenue range (25 pts)
        revenue = float(company.get("annual_revenue") or 0)
        for (lo, hi), pts in self.REVENUE_TIERS.items():
            if lo <= revenue <= hi:
                score += 25 * (pts / 100)
                signals["revenue_tier"] = f"{lo}-{hi}"
                break

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100.0), 1),
            version=self.version,
            computed_at=now,
            confidence=0.85 if signals.get("industry_match") != "low" else 0.5,
            contributing_signals=signals,
            explanation=f"ICP score {round(min(score, 100), 1)} based on industry alignment, company size, region, and revenue range.",
        )


class FundingScoreComputer(FeatureComputer):
    """Funding Score (0-100).

    Factors:
      - Raised funding (yes/no)              (max 20 pts)
      - Total funding amount                  (max 30 pts)
      - Most recent round recency             (max 25 pts)
      - Number of rounds                      (max 25 pts)
    """

    name = "funding_score"
    version = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        company_id = company.get("id")
        tenant_id = company.get("tenant_id")

        # Query funding events if they exist
        total_funding = 0.0
        latest_round_date = None
        round_count = 0

        if company_id and tenant_id:
            rows = await session.execute(
                text("""
                    SELECT amount, date, round_type
                    FROM public.company_funding_events
                    WHERE company_id = :cid AND tenant_id = :tid
                    ORDER BY date DESC
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            events = rows.mappings().all()
            round_count = len(events)
            for ev in events:
                total_funding += float(ev.get("amount") or 0)
                if latest_round_date is None:
                    latest_round_date = ev.get("date") or None
        else:
            events = []

        # Has raised? (20 pts)
        if round_count > 0:
            score += 20
            signals["has_funding"] = True
        else:
            signals["has_funding"] = False

        # Total amount (30 pts)
        tiers = [(0, 0, 0), (1, 500_000, 10), (500_001, 2_000_000, 15),
                 (2_000_001, 10_000_000, 22), (10_000_001, 50_000_000, 28),
                 (50_000_001, 999_999_999_999, 30)]
        for lo, hi, pts in tiers:
            if lo <= total_funding <= hi:
                score += pts
                signals["total_funding"] = total_funding
                break

        # Recency (25 pts)
        if latest_round_date:
            try:
                if isinstance(latest_round_date, str):
                    latest = datetime.fromisoformat(latest_round_date)
                else:
                    latest = latest_round_date
                months_ago = (datetime.now(timezone.utc) - latest).days / 30
                if months_ago < 6:
                    score += 25
                elif months_ago < 12:
                    score += 18
                elif months_ago < 24:
                    score += 10
                else:
                    score += 5
                signals["latest_round_months_ago"] = round(months_ago, 1)
            except Exception:
                pass

        # Round count (25 pts)
        if round_count >= 4:
            score += 25
        elif round_count >= 2:
            score += 15
        elif round_count == 1:
            score += 8
        signals["round_count"] = round_count

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100), 1),
            version=self.version,
            computed_at=now,
            confidence=0.8 if round_count > 0 else 0.3,
            contributing_signals=signals,
            explanation=f"Funding score {round(min(score, 100), 1)} based on {round_count} rounds totaling ${total_funding:,.0f}.",
        )


class HiringScoreComputer(FeatureComputer):
    """Hiring Velocity score (0-100).

    Factors:
      - Active job postings count            (max 30 pts)
      - Hiring growth rate (YoY)             (max 30 pts)
      - Seniority of roles being hired       (max 20 pts)
      - Department diversity of hires        (max 20 pts)
    """

    name = "hiring_score"
    version = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        company_id = company.get("id")
        tenant_id = company.get("tenant_id")

        active_postings = 0
        hiring_events = []
        if company_id and tenant_id:
            rows = await session.execute(
                text("""
                    SELECT role, seniority, department, posted_at
                    FROM public.company_job_postings
                    WHERE company_id = :cid AND tenant_id = :tid AND status = 'active'
                    ORDER BY posted_at DESC
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            hiring_events = rows.mappings().all()
            active_postings = len(hiring_events)

        # Active postings (30 pts)
        if active_postings >= 20:
            score += 30
        elif active_postings >= 10:
            score += 22
        elif active_postings >= 5:
            score += 15
        elif active_postings >= 1:
            score += 8
        signals["active_postings"] = active_postings

        # Seniority (20 pts)
        senior_roles = sum(1 for h in hiring_events if str(h.get("seniority", "")).lower() in ("senior", "lead", "head", "director", "vp", "c-level", "executive"))
        if senior_roles > 5:
            score += 20
        elif senior_roles > 2:
            score += 12
        elif senior_roles > 0:
            score += 6
        signals["senior_roles"] = senior_roles

        # Department diversity (20 pts)
        departments = set(h.get("department", "").lower() for h in hiring_events if h.get("department"))
        dept_count = len(departments)
        if dept_count >= 5:
            score += 20
        elif dept_count >= 3:
            score += 12
        elif dept_count >= 1:
            score += 6
        signals["departments_hiring"] = list(departments)[:5]

        # Growth rate (30 pts) — estimate from employee count change
        emp_prev = int(company.get("employee_count_prev_year") or 0)
        emp_curr = int(company.get("employee_count") or 0)
        if emp_prev > 0:
            growth_pct = ((emp_curr - emp_prev) / emp_prev) * 100
            if growth_pct > 50:
                score += 30
            elif growth_pct > 20:
                score += 22
            elif growth_pct > 5:
                score += 12
            else:
                score += 5
            signals["employee_growth_pct"] = round(growth_pct, 1)
        else:
            signals["employee_growth_pct"] = None

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100), 1),
            version=self.version,
            computed_at=now,
            confidence=0.75 if active_postings > 0 else 0.4,
            contributing_signals=signals,
            explanation=f"Hiring score {round(min(score, 100), 1)} with {active_postings} active postings across {dept_count} departments.",
        )


class GrowthScoreComputer(FeatureComputer):
    """Growth Score (0-100).

    Factors:
      - Employee growth rate                 (max 30 pts)
      - Revenue growth rate                  (max 30 pts)
      - Branch/office expansion              (max 20 pts)
      - Market presence indicators           (max 20 pts)
    """

    name = "growth_score"
    version = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        # Employee growth (30 pts)
        emp_prev = float(company.get("employee_count_prev_year") or 0)
        emp_curr = float(company.get("employee_count") or 0)
        if emp_prev > 0:
            growth = ((emp_curr - emp_prev) / emp_prev) * 100
            if growth > 50:
                score += 30
            elif growth > 20:
                score += 22
            elif growth > 5:
                score += 12
            elif growth > 0:
                score += 5
            signals["employee_growth_pct"] = round(growth, 1)

        # Revenue growth (30 pts)
        rev_prev = float(company.get("revenue_prev_year") or 0)
        rev_curr = float(company.get("annual_revenue") or 0)
        if rev_prev > 0:
            rev_growth = ((rev_curr - rev_prev) / rev_prev) * 100
            if rev_growth > 50:
                score += 30
            elif rev_growth > 20:
                score += 22
            elif rev_growth > 5:
                score += 12
            elif rev_growth > 0:
                score += 5
            signals["revenue_growth_pct"] = round(rev_growth, 1)

        # Branch count (20 pts)
        branch_count = int(company.get("branch_count") or 0)
        if branch_count >= 10:
            score += 20
        elif branch_count >= 5:
            score += 14
        elif branch_count >= 2:
            score += 8
        elif branch_count == 1:
            score += 3
        signals["branch_count"] = branch_count

        # Market presence (20 pts)
        has_website = bool(company.get("website"))
        has_linkedin = bool(company.get("linkedin_url"))
        gov_license = bool(company.get("cr_number"))
        market_score = sum([has_website, has_linkedin, gov_license])
        score += market_score * 7
        signals["presence_signals"] = market_score

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100), 1),
            version=self.version,
            computed_at=now,
            confidence=0.7,
            contributing_signals=signals,
            explanation=f"Growth score {round(min(score, 100), 1)} based on employee/revenue growth and market presence.",
        )


class IntentScoreComputer(FeatureComputer):
    """Buying Intent Score (0-100).

    Factors:
      - Recent RFP/tender activity           (max 30 pts)
      - Website/page visit activity          (max 25 pts)
      - Content consumption (case studies)   (max 20 pts)
      - Decision-maker engagement            (max 25 pts)
    """

    name = "intent_score"
    version = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        company_id = company.get("id")
        tenant_id = company.get("tenant_id")

        # Query intent signals
        recent_rfps = 0
        recent_visits = 0
        content_consumed = 0
        dm_interactions = 0

        if company_id and tenant_id:
            # RFPs / tenders
            rfp_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.company_intent_rfps
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND detected_at >= NOW() - INTERVAL '90 days'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            recent_rfps = rfp_rows.scalar() or 0

            # Web visits
            visit_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.company_intent_visits
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND visited_at >= NOW() - INTERVAL '30 days'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            recent_visits = visit_rows.scalar() or 0

            # Content consumption
            content_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.company_intent_content
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND consumed_at >= NOW() - INTERVAL '60 days'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            content_consumed = content_rows.scalar() or 0

            # Decision-maker interactions
            dm_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.company_intent_contacts
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND role IN ('cfo', 'cto', 'vp', 'director', 'ceo', 'cio')
                    AND last_interaction >= NOW() - INTERVAL '90 days'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            dm_interactions = dm_rows.scalar() or 0

        # RFPs (30 pts)
        if recent_rfps >= 3:
            score += 30
        elif recent_rfps >= 1:
            score += 18
        signals["recent_rfps"] = recent_rfps

        # Web visits (25 pts)
        if recent_visits >= 20:
            score += 25
        elif recent_visits >= 10:
            score += 18
        elif recent_visits >= 5:
            score += 10
        elif recent_visits >= 1:
            score += 5
        signals["recent_visits"] = recent_visits

        # Content (20 pts)
        if content_consumed >= 5:
            score += 20
        elif content_consumed >= 2:
            score += 12
        elif content_consumed >= 1:
            score += 6
        signals["content_consumed"] = content_consumed

        # DM engagement (25 pts)
        if dm_interactions >= 5:
            score += 25
        elif dm_interactions >= 2:
            score += 16
        elif dm_interactions >= 1:
            score += 8
        signals["dm_interactions"] = dm_interactions

        confidence = 0.3
        if recent_rfps > 0 or recent_visits > 0:
            confidence = 0.6
        if dm_interactions > 0:
            confidence = 0.8

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100), 1),
            version=self.version,
            computed_at=now,
            confidence=confidence,
            contributing_signals=signals,
            explanation=f"Intent score {round(min(score, 100), 1)} from {recent_rfps} RFPs, {recent_visits} visits, {dm_interactions} DM interactions in last 90 days.",
        )


class ExpansionScoreComputer(FeatureComputer):
    """Expansion Potential score (0-100).

    Factors:
      - Adjacent market presence             (max 25 pts)
      - Product/service diversity            (max 25 pts)
      - Subsidiary/affiliate count           (max 25 pts)
      - Contract renewal proximity           (max 25 pts)
    """

    name = "expansion_score"
    version = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        company_id = company.get("id")
        tenant_id = company.get("tenant_id")

        subsidiary_count = 0
        product_categories = set()
        has_renewal = False
        days_to_renewal = 365

        if company_id and tenant_id:
            sub_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.companies
                    WHERE parent_company_id = :cid AND tenant_id = :tid
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            subsidiary_count = sub_rows.scalar() or 0

            cat_rows = await session.execute(
                text("""
                    SELECT DISTINCT category FROM public.company_products
                    WHERE company_id = :cid AND tenant_id = :tid
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            product_categories = set(r[0] for r in cat_rows if r[0])

            renewal_rows = await session.execute(
                text("""
                    SELECT expires_at FROM public.company_licenses
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND status = 'active'
                    ORDER BY expires_at ASC LIMIT 1
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            renewal = renewal_rows.scalar_one_or_none()
            if renewal:
                has_renewal = True
                if isinstance(renewal, str):
                    renewal_dt = datetime.fromisoformat(renewal)
                else:
                    renewal_dt = renewal
                days_to_renewal = (renewal_dt - datetime.now(timezone.utc)).days

        # Subsidiary count (25 pts)
        if subsidiary_count >= 5:
            score += 25
        elif subsidiary_count >= 2:
            score += 15
        elif subsidiary_count >= 1:
            score += 8
        signals["subsidiary_count"] = subsidiary_count

        # Product diversity (25 pts)
        cat_count = len(product_categories)
        if cat_count >= 5:
            score += 25
        elif cat_count >= 3:
            score += 16
        elif cat_count >= 1:
            score += 8
        signals["product_categories"] = cat_count

        # Renewal proximity (25 pts)
        if has_renewal:
            if days_to_renewal <= 30:
                score += 25
            elif days_to_renewal <= 90:
                score += 18
            elif days_to_renewal <= 180:
                score += 10
            elif days_to_renewal <= 365:
                score += 5
            signals["days_to_renewal"] = days_to_renewal

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100), 1),
            version=self.version,
            computed_at=now,
            confidence=0.65,
            contributing_signals=signals,
            explanation=f"Expansion score {round(min(score, 100), 1)} based on {cat_count} product categories and {subsidiary_count} subsidiaries.",
        )


class RevenueScoreComputer(FeatureComputer):
    """Revenue Score (0-100).

    Factors:
      - Annual revenue                       (max 30 pts)
      - Revenue trend (3yr)                  (max 30 pts)
      - License count / deal value           (max 20 pts)
      - Payment history / consistency        (max 20 pts)
    """

    name = "revenue_score"
    version = 1

    async def compute(self, company: dict[str, Any], session: AsyncSession) -> FeatureResult:
        signals: dict[str, Any] = {}
        score = 0.0

        company_id = company.get("id")
        tenant_id = company.get("tenant_id")

        annual_rev = float(company.get("annual_revenue") or 0)
        rev_prev = float(company.get("revenue_prev_year") or 0)
        rev_2yr = float(company.get("revenue_2yr_ago") or 0)

        active_licenses = 0
        total_deal_value = 0.0
        payment_reliable = False

        if company_id and tenant_id:
            lic_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.company_licenses
                    WHERE company_id = :cid AND tenant_id = :tid AND status = 'active'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            active_licenses = lic_rows.scalar() or 0

            deal_rows = await session.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0) as total FROM public.company_deals
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND status IN ('closed_won', 'active')
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            total_deal_value = float(deal_rows.scalar() or 0)

            pay_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as reliable FROM public.company_payments
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND status = 'paid_on_time'
                    AND payment_date >= NOW() - INTERVAL '1 year'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            reliable_count = pay_rows.scalar() or 0
            total_pay_rows = await session.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM public.company_payments
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND payment_date >= NOW() - INTERVAL '1 year'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            total_payments = total_pay_rows.scalar() or 0
            payment_reliable = total_payments > 0 and (reliable_count / total_payments) >= 0.9

        # Annual revenue (30 pts)
        rev_tiers = [(0, 0, 0), (1, 500_000, 8), (500_001, 2_000_000, 14),
                     (2_000_001, 10_000_000, 20), (10_000_001, 50_000_000, 26),
                     (50_000_001, 999_999_999_999, 30)]
        for lo, hi, pts in rev_tiers:
            if lo <= annual_rev <= hi:
                score += pts
                signals["revenue_tier"] = f"${lo:,}-${hi:,}"
                break

        # Revenue trend (30 pts)
        if rev_prev > 0 and rev_2yr > 0:
            trend_1 = ((annual_rev - rev_prev) / rev_prev) * 100
            trend_2 = ((rev_prev - rev_2yr) / rev_2yr) * 100
            avg_trend = (trend_1 + trend_2) / 2
            if avg_trend > 30:
                score += 30
            elif avg_trend > 15:
                score += 22
            elif avg_trend > 5:
                score += 12
            elif avg_trend > 0:
                score += 5
            signals["avg_revenue_growth_pct"] = round(avg_trend, 1)
        elif rev_prev > 0:
            growth = ((annual_rev - rev_prev) / rev_prev) * 100
            if growth > 20:
                score += 20
            elif growth > 5:
                score += 10
            signals["revenue_growth_pct"] = round(growth, 1)

        # License/deal value (20 pts)
        deal_score = total_deal_value + (active_licenses * 50000)
        if deal_score > 1_000_000:
            score += 20
        elif deal_score > 200_000:
            score += 14
        elif deal_score > 50_000:
            score += 8
        elif deal_score > 0:
            score += 4
        signals["deal_equity"] = round(deal_score, 0)

        # Payment reliability (20 pts)
        if payment_reliable:
            score += 20
            signals["payment_reliability"] = "high"
        else:
            signals["payment_reliability"] = "unknown"

        now = datetime.now(timezone.utc)
        return FeatureResult(
            score=round(min(score, 100), 1),
            version=self.version,
            computed_at=now,
            confidence=0.8 if annual_rev > 0 else 0.3,
            contributing_signals=signals,
            explanation=f"Revenue score {round(min(score, 100), 1)} based on ${annual_rev:,.0f} annual revenue with {active_licenses} active licenses.",
        )
