"""Context Runtime — builds multi-dimensional context snapshots for a company."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class BusinessContext:
    industry: Optional[str] = None
    size: Optional[str] = None
    legal_form: Optional[str] = None
    incorporation_date: Optional[str] = None
    cr_number: Optional[str] = None
    status: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    is_gov: bool = False


@dataclass
class SalesContext:
    total_deals: int = 0
    active_deals: int = 0
    total_deal_value: float = 0.0
    won_deals: int = 0
    last_deal_date: Optional[str] = None
    avg_deal_cycle_days: Optional[float] = None


@dataclass
class MarketingContext:
    active_campaigns: int = 0
    email_opens: int = 0
    email_clicks: int = 0
    last_campaign_date: Optional[str] = None
    website_visits_30d: int = 0


@dataclass
class CustomerContext:
    is_existing_customer: bool = False
    licenses_active: int = 0
    support_tickets_open: int = 0
    last_contact_date: Optional[str] = None
    satisfaction_score: Optional[float] = None
    churn_risk: Optional[str] = None


@dataclass
class RevenueContext:
    annual_revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    contract_value: Optional[float] = None
    payment_reliability: Optional[str] = None
    days_to_renewal: Optional[int] = None


@dataclass
class CompanyContext:
    business: BusinessContext = field(default_factory=BusinessContext)
    sales: SalesContext = field(default_factory=SalesContext)
    marketing: MarketingContext = field(default_factory=MarketingContext)
    customer: CustomerContext = field(default_factory=CustomerContext)
    revenue: RevenueContext = field(default_factory=RevenueContext)
    features: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "business": {k: v for k, v in vars(self.business).items() if v is not None},
            "sales": {k: v for k, v in vars(self.sales).items() if v is not None and v != 0 and v != []},
            "marketing": {k: v for k, v in vars(self.marketing).items() if v is not None and v != 0},
            "customer": {k: v for k, v in vars(self.customer).items() if v is not None},
            "revenue": {k: v for k, v in vars(self.revenue).items() if v is not None},
            "features": self.features,
        }


class ContextBuilder:
    """Assembles full company context from DB + Feature Store + signals."""

    def __init__(self, session_factory: Callable[[], AsyncSession], feature_store: Any, logger: Any = None):
        self._session_factory = session_factory
        self._feature_store = feature_store
        self._logger = logger
        self._build_count = 0
        self._total_build_ms = 0.0

    async def build(self, company_id: str, tenant_id: str) -> CompanyContext:
        t0 = time.monotonic()
        ctx = CompanyContext()

        async with self._session_factory() as session:
            row = await session.execute(
                sa_text("""
                    SELECT c.*, COUNT(DISTINCT l.id) FILTER (WHERE l.status = 'active') as license_count
                    FROM companies c
                    LEFT JOIN licenses l ON l.company_id = c.id
                    WHERE c.id = :cid AND c.tenant_id = :tid
                    GROUP BY c.id
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            r = row.mappings().one_or_none()
            if not r:
                return ctx

            # Business context
            bc = ctx.business
            bc.industry = r.get("industry")
            bc.legal_form = r.get("legal_form")
            bc.incorporation_date = str(r.get("incorporation_date")) if r.get("incorporation_date") else None
            bc.cr_number = r.get("cr_number")
            bc.status = r.get("status")
            bc.city = r.get("city")
            bc.region = r.get("region")
            emp = r.get("employees_count") or 0
            bc.size = "small" if emp < 50 else "medium" if emp < 500 else "large"
            bc.is_gov = (r.get("legal_form") or "").lower() in ("government", "ministry", "public")

            # Sales context
            sales = await session.execute(
                sa_text("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status IN ('open','negotiation') THEN 1 ELSE 0 END) as active,
                           COALESCE(SUM(amount), 0) as total_value,
                           SUM(CASE WHEN status = 'closed_won' THEN 1 ELSE 0 END) as won,
                           MAX(created_at) as last_date
                    FROM company_deals
                    WHERE company_id = :cid AND tenant_id = :tid
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            sr = sales.mappings().one()
            sc = ctx.sales
            sc.total_deals = sr.get("total") or 0
            sc.active_deals = sr.get("active") or 0
            sc.total_deal_value = float(sr.get("total_value") or 0)
            sc.won_deals = sr.get("won") or 0
            sc.last_deal_date = str(sr.get("last_date")) if sr.get("last_date") else None

            # Marketing context
            visits = await session.execute(
                sa_text("""
                    SELECT COUNT(*) as cnt FROM company_intent_visits
                    WHERE company_id = :cid AND tenant_id = :tid
                    AND visited_at >= NOW() - INTERVAL '30 days'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            mc = ctx.marketing
            mc.website_visits_30d = visits.scalar() or 0

            # Customer context
            cc = ctx.customer
            cc.licenses_active = r.get("license_count") or 0
            cc.is_existing_customer = cc.licenses_active > 0

            # Revenue context
            rc = ctx.revenue
            rc.annual_revenue = r.get("annual_revenue")
            if r.get("revenue_prev_year") and r.get("annual_revenue"):
                rc.revenue_growth = ((float(r["annual_revenue"]) - float(r["revenue_prev_year"])) / float(r["revenue_prev_year"])) * 100

            expiry = await session.execute(
                sa_text("""
                    SELECT MIN(expiry_date) as nearest FROM licenses
                    WHERE company_id = :cid AND tenant_id = :tid AND status = 'active'
                """),
                {"cid": company_id, "tid": tenant_id},
            )
            exp = expiry.scalar()
            if exp:
                if isinstance(exp, str):
                    exp_dt = datetime.fromisoformat(exp)
                else:
                    exp_dt = exp
                rc.days_to_renewal = (exp_dt - datetime.now(timezone.utc)).days

        # Feature Store scores
        try:
            features = await self._feature_store.get_features(company_id=company_id, tenant_id=tenant_id)
            ctx.features = {name: result.score for name, result in features.items()}
        except Exception:
            pass

        elapsed = (time.monotonic() - t0) * 1000
        self._build_count += 1
        self._total_build_ms += elapsed

        return ctx

    def metrics(self) -> dict:
        return {
            "builds": self._build_count,
            "total_build_ms": round(self._total_build_ms, 2),
            "avg_build_ms": round(self._total_build_ms / max(self._build_count, 1), 2),
        }
