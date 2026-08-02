"""STORY-08-06 — ConflictResolutionPolicy persistence (tenant-scoped)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integration_hub.conflict_policy import (
    ConflictResolutionPolicy,
    policy_from_row,
)
from app.modules.integration_hub.models import ConflictResolutionPolicyModel


class ConflictResolutionPolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_connection(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connection_id: uuid.UUID | str,
    ) -> ConflictResolutionPolicyModel | None:
        tid = uuid.UUID(str(tenant_id))
        cid = uuid.UUID(str(connection_id))
        return (
            await self.session.execute(
                select(ConflictResolutionPolicyModel).where(
                    ConflictResolutionPolicyModel.tenant_id == tid,
                    ConflictResolutionPolicyModel.connection_id == cid,
                )
            )
        ).scalar_one_or_none()

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID | str,
        connection_id: uuid.UUID | str,
        rules: Sequence[Mapping[str, Any]] | None = None,
        salesos_authored_fields: Sequence[str] | None = None,
        operational_fields: Sequence[str] | None = None,
    ) -> ConflictResolutionPolicyModel:
        tid = uuid.UUID(str(tenant_id))
        cid = uuid.UUID(str(connection_id))
        policy = policy_from_row(
            rules=list(rules) if rules is not None else [],
            salesos_authored_fields=list(salesos_authored_fields)
            if salesos_authored_fields is not None
            else None,
            operational_fields=list(operational_fields) if operational_fields is not None else None,
        )
        row = await self.get_for_connection(tenant_id=tid, connection_id=cid)
        rules_json = [
            {
                "internal": r.internal,
                "winner": r.winner,
                "exclude_from_pull": r.exclude_from_pull,
            }
            for r in policy.rules
        ]
        if row is None:
            row = ConflictResolutionPolicyModel(
                id=uuid.uuid4(),
                tenant_id=tid,
                connection_id=cid,
                rules=rules_json,
                salesos_authored_fields=sorted(policy.salesos_authored_fields),
                operational_fields=sorted(policy.operational_fields),
            )
            self.session.add(row)
        else:
            row.rules = rules_json
            row.salesos_authored_fields = sorted(policy.salesos_authored_fields)
            row.operational_fields = sorted(policy.operational_fields)
        await self.session.flush()
        return row

    def as_policy(self, row: ConflictResolutionPolicyModel) -> ConflictResolutionPolicy:
        return policy_from_row(
            rules=row.rules,
            salesos_authored_fields=row.salesos_authored_fields,
            operational_fields=row.operational_fields,
        )
