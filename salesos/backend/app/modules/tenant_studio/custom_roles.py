"""STORY-10-06 — Tenant-custom role models (Permissions Studio)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class CustomRoleError(ValueError):
    """Invalid custom role definition."""


@dataclass
class CustomRole:
    id: str
    tenant_id: str
    name: str
    description: str = ""
    permissions: list[str] = field(default_factory=list)
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def build_custom_role(
    *,
    tenant_id: str,
    name: str,
    permissions: list[str],
    description: str = "",
    role_id: str = "",
    schema_version: int = 1,
) -> CustomRole:
    tid = (tenant_id or "").strip()
    if not tid:
        raise CustomRoleError("tenant_id required")
    nm = (name or "").strip()
    if not nm:
        raise CustomRoleError("name required")
    if not permissions:
        raise CustomRoleError("permissions required (non-empty)")
    return CustomRole(
        id=role_id,
        tenant_id=tid,
        name=nm,
        description=(description or "").strip(),
        permissions=list(permissions),
        schema_version=max(int(schema_version), 1),
    )
