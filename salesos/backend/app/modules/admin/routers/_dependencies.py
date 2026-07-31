from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session

from ..pg_repositories import (
    PostgresAICostRepository,
    PostgresFeatureFlagRepository,
    PostgresHealthRepository,
    PostgresInvoiceRepository,
    PostgresJobRepository,
    PostgresLicenseRepository,
    PostgresPermissionRepository,
    PostgresPlanRepository,
    PostgresRoleRepository,
    PostgresTenantConfigRepository,
)


class AdminRepositories:
    def __init__(self, db: AsyncSession):
        self.plans = PostgresPlanRepository(db)
        self.licenses = PostgresLicenseRepository(db)
        self.invoices = PostgresInvoiceRepository(db)
        self.flags = PostgresFeatureFlagRepository(db)
        self.jobs = PostgresJobRepository(db)
        self.ai = PostgresAICostRepository(db)
        self.health = PostgresHealthRepository(db)
        self.roles = PostgresRoleRepository(db)
        self.permissions = PostgresPermissionRepository(db)
        self.tenant_configs = PostgresTenantConfigRepository(db)


async def get_admin_repos(db: AsyncSession = Depends(get_db_session)) -> AdminRepositories:
    return AdminRepositories(db)
