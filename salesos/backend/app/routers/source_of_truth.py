"""Source of Truth — unified view of every product, page, module, and widget.

Aggregates all registries into one discoverable endpoint so the platform
never needs hardcoded knowledge of what exists.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_optional_token
from runtime.capability_framework import Capability as CapabilityDecorator
from runtime.widget_engine import WidgetRegistry
from sdk.capability_registry import CapabilityRegistry as SDKCapabilityRegistry
from sdk.feature_registry import FeatureRegistry

router = APIRouter(
    prefix="/api/v1/source-of-truth",
    tags=["Source of Truth"],
    dependencies=[Depends(get_optional_token)],
)


def _get_all_modules() -> list[dict]:
    seen = set()
    modules = []

    for name, fm in FeatureRegistry.all().items():
        seen.add(name)
        modules.append({
            "name": name,
            "label": fm.label,
            "label_ar": fm.label_ar,
            "description": fm.description,
            "description_ar": fm.description_ar,
            "version": fm.version,
            "status": fm.status.value,
            "entities": fm.entities,
            "permissions": fm.permissions,
            "events": fm.events,
            "api_prefix": fm.api_prefix,
            "owner": fm.owner,
            "tags": fm.tags,
            "source": "FeatureRegistry",
        })

    for name, cap in SDKCapabilityRegistry.all().items():
        label = name
        description = ""
        if hasattr(cap, "label"):
            label = cap.label
        if hasattr(cap, "description"):
            description = cap.description
        entry = {
            "name": name,
            "label": label,
            "label_ar": getattr(cap, "label_ar", ""),
            "description": description,
            "version": getattr(cap, "version", "1.0.0"),
            "status": "registered",
            "type": cap.type.value if hasattr(cap, "type") else "",
            "entities": [],
            "permissions": getattr(cap, "permissions", []),
            "events": {
                "produces": cap.events.produces if hasattr(cap, "events") else [],
                "consumes": cap.events.consumes if hasattr(cap, "events") else [],
            },
            "executors": [
                {"name": e.name, "strategy": e.strategy.value, "supports": e.supports}
                for e in getattr(cap, "executors", [])
            ],
            "source": "SDKCapabilityRegistry",
        }
        if name not in seen:
            seen.add(name)
            modules.append(entry)
        else:
            for i, m in enumerate(modules):
                if m["name"] == name:
                    modules[i] = entry
                    break

    return modules


def _get_all_products() -> list[dict]:
    return [
        {
            "id": c.id,
            "name": c.manifest.name,
            "version": c.manifest.version,
            "description": c.manifest.description,
            "owner": c.manifest.owner,
            "status": c.manifest.status.value,
            "dependencies": c.manifest.dependencies,
            "tags": c.manifest.tags,
            "contract": {
                "consumes": c.manifest.contract.consumes,
                "produces": c.manifest.contract.produces,
                "events": c.manifest.contract.events,
                "apis": c.manifest.contract.apis,
                "permissions": c.manifest.contract.permissions,
                "entities": c.manifest.contract.entities,
            },
            "ui": {
                "tabs": c.manifest.ui.tabs,
                "sidebar": c.manifest.ui.sidebar,
                "icon": c.manifest.ui.icon,
                "routes": c.manifest.ui.routes,
                "components": c.manifest.ui.components,
            },
            "source": "CapabilityFramework",
        }
        for c in sorted(CapabilityDecorator.all(), key=lambda x: x.id)
    ]


def _get_all_pages() -> list[dict]:
    pages = []
    seen_routes = set()

    from runtime.capability_framework import Capability
    for cap in Capability.all():
        ui = cap.manifest.ui
        for route in ui.routes:
            if route not in seen_routes:
                seen_routes.add(route)
                pages.append({
                    "route": route,
                    "label": route.strip("/").split("/")[0].replace("_", " ").title(),
                    "capability_id": cap.id,
                    "capability_name": cap.manifest.name,
                    "tabs": ui.tabs,
                    "icon": ui.icon,
                    "sidebar": ui.sidebar,
                })

    core_pages = [
        {"route": "/login", "label": "Login", "capability_id": "identity", "capability_name": "Identity & Access Management"},
        {"route": "/register", "label": "Register", "capability_id": "identity", "capability_name": "Identity & Access Management"},
        {"route": "/dashboard", "label": "Dashboard", "capability_id": "company", "capability_name": "Company Intelligence"},
        {"route": "/admin", "label": "Admin", "capability_id": "identity", "capability_name": "Identity & Access Management"},
        {"route": "/admin/tenants", "label": "Admin Tenants", "capability_id": "identity"},
        {"route": "/admin/audit", "label": "Admin Audit", "capability_id": "identity"},
        {"route": "/admin/flags", "label": "Admin Flags", "capability_id": "identity"},
        {"route": "/admin/config", "label": "Admin Config", "capability_id": "identity"},
        {"route": "/settings", "label": "Settings", "capability_id": "identity"},
    ]
    for cp in core_pages:
        if cp["route"] not in seen_routes:
            seen_routes.add(cp["route"])
            pages.append(cp)

    v3_pages = [
        {"route": "/v3", "label": "V3 Shell", "capability_id": "capability-framework"},
        {"route": "/v3/activities", "label": "Activities (v3)", "capability_id": "activity-intelligence"},
        {"route": "/v3/admin", "label": "Admin (v3)", "capability_id": "identity"},
        {"route": "/v3/analytics", "label": "Analytics (v3)", "capability_id": "feature-store"},
        {"route": "/v3/companies", "label": "Companies (v3)", "capability_id": "company"},
        {"route": "/v3/contacts", "label": "Contacts (v3)", "capability_id": "company"},
        {"route": "/v3/crm", "label": "CRM (v3)", "capability_id": "company"},
        {"route": "/v3/cs", "label": "Customer Success (v3)", "capability_id": "company"},
        {"route": "/v3/employee", "label": "Employee (v3)", "capability_id": "activity-intelligence"},
        {"route": "/v3/people", "label": "People (v3)", "capability_id": "company"},
        {"route": "/v3/settings", "label": "Settings (v3)", "capability_id": "identity"},
        {"route": "/v3/shell", "label": "Shell (v3)", "capability_id": "capability-framework"},
        {"route": "/v3/tasks", "label": "Tasks (v3)", "capability_id": "workflow"},
    ]
    for vp in v3_pages:
        if vp["route"] not in seen_routes:
            seen_routes.add(vp["route"])
            pages.append(vp)

    return sorted(pages, key=lambda p: p["route"])


def _get_all_widgets() -> list[dict]:
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "capability_id": w.capability_id,
            "renderer": w.renderer,
            "slots": [s.value for s in w.slots],
            "size_hints": {
                "min_width": w.size_hints.min_width,
                "min_height": w.size_hints.min_height,
                "default_width": w.size_hints.default_width,
                "default_height": w.size_hints.default_height,
            },
            "icon": w.icon,
            "tags": w.tags,
        }
        for w in WidgetRegistry.all()
    ]


@router.get("")
async def get_source_of_truth():
    products = _get_all_products()
    modules = _get_all_modules()
    pages = _get_all_pages()
    widgets = _get_all_widgets()

    return {
        "summary": {
            "total_products": len(products),
            "total_modules": len(modules),
            "total_pages": len(pages),
            "total_widgets": len(widgets),
        },
        "products": products,
        "modules": modules,
        "pages": pages,
        "widgets": widgets,
    }


@router.get("/products")
async def list_products():
    return _get_all_products()


@router.get("/modules")
async def list_modules():
    return _get_all_modules()


@router.get("/pages")
async def list_pages():
    return _get_all_pages()


@router.get("/widgets")
async def list_widgets():
    return _get_all_widgets()
