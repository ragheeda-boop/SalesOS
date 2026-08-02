"""STORY-06-01 — Plan.entitlements schema (CAP-070 packaging).

Maps COMMERCIAL_LAUNCH_PLAN §2 packaging → structured JSONB on admin_plans.
Feature flags remain a separate layer (DEC two-layer model). No request middleware
here (STORY-06-02). Not Production GO.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = 1

# Core CRM / revenue domains always entitled on paid-ish tiers (incl. free browse).
CORE_DOMAINS = ("DOM-001", "DOM-002", "DOM-003", "DOM-004", "DOM-005", "DOM-006")


class DomainEntitlement(BaseModel):
    """Per-domain commercial gate."""

    enabled: bool = False
    # Optional soft mode: limited | full (Tenant Studio DOM-022).
    mode: Literal["limited", "full"] | None = None
    # Numeric quota when domain is metered (e.g. connectors on DOM-021).
    quota: int | None = None
    # Unlimited sentinel (Enterprise connectors / negotiated).
    unlimited: bool = False
    # Marketplace publish rights (DOM-024 Enterprise post-GA).
    publish: bool = False

    @field_validator("quota")
    @classmethod
    def _quota_non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("quota must be >= 0")
        return v


class EntitlementQuotas(BaseModel):
    # Plain defaults — pydantic mypy plugin treats Field(default=...) as required.
    seats: int = 1
    ai_tokens_monthly: int = 0
    connectors: int = 0
    storage_mb: int = 100
    api_calls_monthly: int = 1000
    ai_tokens_unlimited: bool = False
    connectors_unlimited: bool = False

    @field_validator(
        "seats",
        "ai_tokens_monthly",
        "connectors",
        "storage_mb",
        "api_calls_monthly",
    )
    @classmethod
    def _non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("quota values must be >= 0")
        return v


def _default_quotas() -> EntitlementQuotas:
    return EntitlementQuotas(
        seats=1,
        ai_tokens_monthly=0,
        connectors=0,
        storage_mb=100,
        api_calls_monthly=1000,
        ai_tokens_unlimited=False,
        connectors_unlimited=False,
    )


class PlanEntitlements(BaseModel):
    """Canonical Plan.entitlements document (versioned)."""

    version: Literal[1] = 1
    domains: dict[str, DomainEntitlement] = Field(default_factory=dict)
    quotas: EntitlementQuotas = Field(default_factory=_default_quotas)
    deployment_tier: Literal["pooled", "siloed"] = "pooled"
    support_sla: str = Field(default="community", min_length=1, max_length=64)

    @field_validator("domains")
    @classmethod
    def _normalize_domain_keys(
        cls, v: dict[str, DomainEntitlement]
    ) -> dict[str, DomainEntitlement]:
        out: dict[str, DomainEntitlement] = {}
        for key, ent in v.items():
            k = str(key).strip().upper()
            if not k.startswith("DOM-"):
                raise ValueError(f"domain key must start with DOM-: {key!r}")
            out[k] = ent
        return out


def domain_enabled(entitlements: PlanEntitlements | dict[str, Any], domain: str) -> bool:
    doc = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    key = str(domain).strip().upper()
    row = doc.domains.get(key)
    return bool(row and row.enabled)


def parse_entitlements(raw: Any) -> PlanEntitlements:
    if raw is None or raw == {}:
        return default_entitlements_for_tier("free")
    if isinstance(raw, PlanEntitlements):
        return raw
    if not isinstance(raw, dict):
        raise ValueError("entitlements must be an object")
    return PlanEntitlements.model_validate(raw)


def entitlements_to_dict(doc: PlanEntitlements) -> dict[str, Any]:
    return doc.model_dump(mode="json")


def _core_domains(enabled: bool = True) -> dict[str, DomainEntitlement]:
    return {d: DomainEntitlement(enabled=enabled) for d in CORE_DOMAINS}


def default_entitlements_for_tier(tier: str) -> PlanEntitlements:
    """Commercial packaging defaults (COMMERCIAL_LAUNCH_PLAN §2)."""
    t = str(tier or "free").strip().lower()

    if t == "starter":
        domains = _core_domains(True)
        domains["DOM-011"] = DomainEntitlement(enabled=False)
        domains["DOM-012"] = DomainEntitlement(enabled=False)
        domains["DOM-021"] = DomainEntitlement(enabled=True, quota=1)
        domains["DOM-022"] = DomainEntitlement(enabled=True, mode="limited")
        domains["DOM-023"] = DomainEntitlement(enabled=False)
        domains["DOM-024"] = DomainEntitlement(enabled=True, publish=False)
        return PlanEntitlements(
            domains=domains,
            quotas=EntitlementQuotas(
                seats=5,
                ai_tokens_monthly=10_000,
                connectors=1,
                storage_mb=1000,
                api_calls_monthly=10_000,
            ),
            deployment_tier="pooled",
            support_sla="community",
        )

    if t == "growth":
        domains = _core_domains(True)
        domains["DOM-011"] = DomainEntitlement(enabled=True)
        domains["DOM-012"] = DomainEntitlement(enabled=True)
        domains["DOM-021"] = DomainEntitlement(enabled=True, quota=5)
        domains["DOM-022"] = DomainEntitlement(enabled=True, mode="full")
        domains["DOM-023"] = DomainEntitlement(enabled=True)
        domains["DOM-024"] = DomainEntitlement(enabled=True, publish=False)
        return PlanEntitlements(
            domains=domains,
            quotas=EntitlementQuotas(
                seats=25,
                ai_tokens_monthly=500_000,
                connectors=5,
                storage_mb=10_000,
                api_calls_monthly=100_000,
            ),
            deployment_tier="pooled",
            support_sla="business_hours_p1",
        )

    if t == "enterprise":
        domains = _core_domains(True)
        domains["DOM-011"] = DomainEntitlement(enabled=True)
        domains["DOM-012"] = DomainEntitlement(enabled=True)
        domains["DOM-021"] = DomainEntitlement(enabled=True, unlimited=True)
        domains["DOM-022"] = DomainEntitlement(enabled=True, mode="full")
        domains["DOM-023"] = DomainEntitlement(enabled=True)
        domains["DOM-024"] = DomainEntitlement(enabled=True, publish=True)
        return PlanEntitlements(
            domains=domains,
            quotas=EntitlementQuotas(
                seats=999,
                ai_tokens_monthly=0,
                ai_tokens_unlimited=True,
                connectors=0,
                connectors_unlimited=True,
                storage_mb=100_000,
                api_calls_monthly=1_000_000,
            ),
            deployment_tier="pooled",  # siloed available via negotiated override
            support_sla="dedicated_p0",
        )

    # free / unknown — browse-only packaging
    domains = _core_domains(True)
    domains["DOM-011"] = DomainEntitlement(enabled=False)
    domains["DOM-012"] = DomainEntitlement(enabled=False)
    domains["DOM-021"] = DomainEntitlement(enabled=False, quota=0)
    domains["DOM-022"] = DomainEntitlement(enabled=False)
    domains["DOM-023"] = DomainEntitlement(enabled=False)
    domains["DOM-024"] = DomainEntitlement(enabled=True, publish=False)
    return PlanEntitlements(
        domains=domains,
        quotas=EntitlementQuotas(
            seats=1,
            ai_tokens_monthly=0,
            connectors=0,
            storage_mb=100,
            api_calls_monthly=1000,
        ),
        deployment_tier="pooled",
        support_sla="community",
    )
