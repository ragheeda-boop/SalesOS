"""STORY-10-06 — CAP-003 Permissions Studio catalog (tenant-grantable).

Each grantable permission maps to a Plan.entitlements DOM ceiling (EPIC-06).
Owner/platform keys are intentionally absent — privilege escalation blocked.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StudioPermissionDef:
    key: str
    name: str
    description: str
    domain: str
    group: str = "general"
    requires_publish: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "group": self.group,
            "requires_publish": self.requires_publish,
        }


# Tenant-grantable only. Maps to Plan.entitlements.domains (STORY-06-01).
_STUDIO_PERMISSIONS: tuple[StudioPermissionDef, ...] = (
    StudioPermissionDef(
        key="crm.companies.read",
        name="Read Companies",
        description="View company records",
        domain="DOM-001",
        group="crm",
    ),
    StudioPermissionDef(
        key="crm.contacts.read",
        name="Read Contacts",
        description="View contact records",
        domain="DOM-002",
        group="crm",
    ),
    StudioPermissionDef(
        key="crm.opportunities.manage",
        name="Manage Opportunities",
        description="Create and update opportunities",
        domain="DOM-003",
        group="sales",
    ),
    StudioPermissionDef(
        key="crm.tasks.manage",
        name="Manage Tasks",
        description="Create and update tasks",
        domain="DOM-004",
        group="sales",
    ),
    StudioPermissionDef(
        key="ai.rag.use",
        name="Use RAG / AI retrieval",
        description="Access DOM-011 AI/RAG surfaces",
        domain="DOM-011",
        group="ai",
    ),
    StudioPermissionDef(
        key="ai.copilot.use",
        name="Use Copilot",
        description="Access DOM-012 AI Studio / copilot",
        domain="DOM-012",
        group="ai",
    ),
    StudioPermissionDef(
        key="integrations.manage",
        name="Manage Integrations",
        description="Configure Integration Hub connectors",
        domain="DOM-021",
        group="integrations",
    ),
    StudioPermissionDef(
        key="studio.configure",
        name="Configure Tenant Studio",
        description="Manage Tenant Studio settings",
        domain="DOM-022",
        group="studio",
    ),
    StudioPermissionDef(
        key="gtm.signals.read",
        name="Read GTM Signals",
        description="Access GTM Intelligence signals",
        domain="DOM-023",
        group="gtm",
    ),
    StudioPermissionDef(
        key="marketplace.publish",
        name="Publish to Marketplace",
        description="Publish marketplace listings (requires DOM-024 publish)",
        domain="DOM-024",
        group="marketplace",
        requires_publish=True,
    ),
)

STUDIO_PERMISSION_CATALOG: dict[str, StudioPermissionDef] = {p.key: p for p in _STUDIO_PERMISSIONS}

# Explicitly non-grantable via tenant Studio (Owner / platform plane).
FORBIDDEN_PERMISSION_KEYS: frozenset[str] = frozenset(
    {
        "admin",
        "manage_users",
        "manage_billing",
        "manage_plans",
        "manage_roles",
        "owner.admin",
        "owner.impersonate",
        "*",
        "all",
    }
)


def list_catalog() -> list[StudioPermissionDef]:
    return list(_STUDIO_PERMISSIONS)


def get_permission_def(key: str) -> StudioPermissionDef | None:
    return STUDIO_PERMISSION_CATALOG.get(str(key).strip())
