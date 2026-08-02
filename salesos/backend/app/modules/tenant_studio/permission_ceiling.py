"""STORY-10-06 — Plan entitlement ceiling for tenant-custom roles.

Fail-closed: unknown / Owner-plane / disabled-domain permissions rejected.
Integrates Plan.entitlements (EPIC-06). Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.admin.entitlements import (
    PlanEntitlements,
    domain_enabled,
    parse_entitlements,
)
from app.modules.tenant_studio.permission_catalog import (
    FORBIDDEN_PERMISSION_KEYS,
    get_permission_def,
    list_catalog,
)


class PermissionCeilingError(ValueError):
    """Role permissions exceed tenant plan entitlement ceiling."""


@dataclass
class CeilingCheckResult:
    allowed: bool
    rejected: list[str] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)
    grantable: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "rejected": list(self.rejected),
            "reasons": dict(self.reasons),
            "grantable": list(self.grantable),
        }


def _domain_row(ents: PlanEntitlements, domain: str):
    return ents.domains.get(str(domain).strip().upper())


def permission_within_ceiling(
    key: str, entitlements: PlanEntitlements | dict[str, Any]
) -> tuple[bool, str]:
    """Return (ok, reason). Fail-closed."""
    ents = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    k = str(key).strip()
    if not k:
        return False, "empty permission key"
    if k in FORBIDDEN_PERMISSION_KEYS or k.startswith("owner."):
        return False, f"owner/platform permission not grantable via Studio: {k}"
    defn = get_permission_def(k)
    if defn is None:
        return False, f"unknown or non-grantable permission: {k}"
    if not domain_enabled(ents, defn.domain):
        return False, f"exceeds plan ceiling: {k} requires enabled {defn.domain}"
    if defn.requires_publish:
        row = _domain_row(ents, defn.domain)
        if row is None or not row.publish:
            return (
                False,
                f"exceeds plan ceiling: {k} requires {defn.domain} publish=true",
            )
    return True, ""


def check_permissions_against_ceiling(
    permission_keys: list[str],
    entitlements: PlanEntitlements | dict[str, Any],
) -> CeilingCheckResult:
    ents = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    rejected: list[str] = []
    reasons: dict[str, str] = {}
    grantable: list[str] = []
    for raw in permission_keys:
        ok, reason = permission_within_ceiling(raw, ents)
        if ok:
            grantable.append(str(raw).strip())
        else:
            rejected.append(str(raw).strip())
            reasons[str(raw).strip()] = reason
    return CeilingCheckResult(
        allowed=len(rejected) == 0,
        rejected=rejected,
        reasons=reasons,
        grantable=grantable,
    )


def assert_within_ceiling(
    permission_keys: list[str],
    entitlements: PlanEntitlements | dict[str, Any],
) -> list[str]:
    result = check_permissions_against_ceiling(permission_keys, entitlements)
    if not result.allowed:
        # Prefer first rejection message for HTTP 403 detail.
        first = result.rejected[0] if result.rejected else "permissions"
        detail = result.reasons.get(first, "privilege escalation blocked")
        raise PermissionCeilingError(detail)
    # Dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for k in result.grantable:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def catalog_with_ceiling(
    entitlements: PlanEntitlements | dict[str, Any],
) -> list[dict[str, Any]]:
    ents = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    rows: list[dict[str, Any]] = []
    for defn in list_catalog():
        ok, reason = permission_within_ceiling(defn.key, ents)
        row = defn.as_dict()
        row["within_ceiling"] = ok
        row["ceiling_reason"] = reason or None
        rows.append(row)
    return rows


def summarize_ceiling(entitlements: PlanEntitlements | dict[str, Any]) -> dict[str, Any]:
    ents = (
        entitlements
        if isinstance(entitlements, PlanEntitlements)
        else parse_entitlements(entitlements)
    )
    enabled = sorted(k for k, v in ents.domains.items() if v.enabled)
    publishable = sorted(k for k, v in ents.domains.items() if v.enabled and v.publish)
    grantable = [d.key for d in list_catalog() if permission_within_ceiling(d.key, ents)[0]]
    return {
        "enabled_domains": enabled,
        "publish_domains": publishable,
        "grantable_permissions": grantable,
        "entitlements": ents.model_dump(mode="json"),
    }
