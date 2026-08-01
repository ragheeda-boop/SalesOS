from __future__ import annotations

from fastapi import APIRouter, Depends

from app.owner_auth import require_owner_role_dep

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(require_owner_role_dep("admin"))],
)

from .routers.ai_audit import router as ai_audit_router
from .routers.ai_costs import router as ai_costs_router
from .routers.audit_log import router as audit_log_router
from .routers.billing import router as billing_router
from .routers.config_editor import router as config_editor_router
from .routers.decision_adoption import router as decision_adoption_router
from .routers.feature_flags import router as feature_flags_router
from .routers.health import router as health_router
from .routers.jobs import router as jobs_router
from .routers.plans import router as plans_router
from .routers.roles_permissions import router as roles_permissions_router
from .routers.tenants import router as tenants_router
from .routers.users import router as users_router

router.include_router(tenants_router)
router.include_router(plans_router)
router.include_router(users_router)
router.include_router(billing_router)
router.include_router(feature_flags_router)
router.include_router(roles_permissions_router)
router.include_router(jobs_router)
router.include_router(ai_costs_router)
router.include_router(health_router)
router.include_router(decision_adoption_router)
router.include_router(config_editor_router)
router.include_router(audit_log_router)
router.include_router(ai_audit_router)
