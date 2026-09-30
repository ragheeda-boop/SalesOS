"""Platform-owner gate for organization and manager registration.

The public request creates no tenant and no user. A designated platform
owner approves or rejects it. Only an approved row lets /register create
the organization, and only in the approved manager's name.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

OPEN_STATUSES = ("pending", "approved")


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def submit_org_registration_request(
    db: AsyncSession,
    *,
    organization_name: str,
    manager_email: str,
    manager_full_name: str,
) -> UUID:
    request_id = uuid4()
    email = normalize_email(manager_email)
    try:
        await db.execute(
            text(
                "INSERT INTO org_registration_approvals ("
                "id, organization_name, manager_email, manager_full_name, status, "
                "created_at, updated_at"
                ") VALUES ("
                "CAST(:id AS uuid), :organization_name, :email, :full_name, 'pending', "
                "NOW(), NOW()"
                ")"
            ),
            {
                "id": str(request_id),
                "organization_name": organization_name.strip(),
                "email": email,
                "full_name": manager_full_name.strip(),
            },
        )
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "org_registration.already_open — this manager email already has "
                "a pending or approved organization request"
            ),
        ) from exc
    return request_id


async def list_open_org_registration_requests(db: AsyncSession) -> list[dict]:
    rows = (
        await db.execute(
            text(
                "SELECT id, organization_name, manager_email, manager_full_name, "
                "status, created_at, decided_at "
                "FROM org_registration_approvals "
                "WHERE status IN ('pending', 'approved') "
                "ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, created_at"
            )
        )
    ).mappings().all()
    return [dict(row) for row in rows]


async def decide_org_registration(
    db: AsyncSession,
    *,
    request_id: UUID,
    decision: str,
    reason: str | None,
    decided_by: str,
) -> dict:
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=422, detail="org_registration.decision_invalid")
    if decision == "reject" and not (reason and reason.strip()):
        raise HTTPException(status_code=422, detail="org_registration.rejection_reason_required")
    status = "approved" if decision == "approve" else "rejected"
    row = (
        await db.execute(
            text(
                "UPDATE org_registration_approvals SET "
                "status = :status, decided_by = CAST(:decided_by AS uuid), "
                "decided_at = NOW(), rejection_reason = :reason, updated_at = NOW() "
                "WHERE id = CAST(:id AS uuid) AND status = 'pending' "
                "RETURNING id, organization_name, manager_email, status"
            ),
            {
                "status": status,
                "decided_by": decided_by,
                "reason": (reason or "").strip() or None,
                "id": str(request_id),
            },
        )
    ).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="org_registration.not_pending — request is missing or already decided",
        )
    return dict(row)


async def lock_approved_organization(
    db: AsyncSession,
    *,
    email: str,
    organization_name: str | None,
) -> tuple[str, str]:
    """Lock the approved row for this manager. Does not consume it."""
    row = (
        await db.execute(
            text(
                "SELECT id, organization_name FROM org_registration_approvals "
                "WHERE manager_email = :email AND status = 'approved' "
                "ORDER BY decided_at ASC LIMIT 1 FOR UPDATE"
            ),
            {"email": normalize_email(email)},
        )
    ).mappings().first()
    if row is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "register.owner_approval_required — the platform owner must approve "
                "this organization and its manager before registration"
            ),
        )
    approved_name = str(row["organization_name"])
    submitted = (organization_name or "").strip()
    if submitted and submitted.casefold() != approved_name.casefold():
        raise HTTPException(
            status_code=403,
            detail="register.organization_name_mismatch — register the approved organization name",
        )
    return str(row["id"]), approved_name


async def consume_approved_organization(
    db: AsyncSession,
    *,
    approval_id: str,
    tenant_id: str,
) -> None:
    row = (
        await db.execute(
            text(
                "UPDATE org_registration_approvals SET "
                "status = 'consumed', consumed_tenant_id = CAST(:tenant_id AS uuid), "
                "updated_at = NOW() "
                "WHERE id = CAST(:id AS uuid) AND status = 'approved' "
                "RETURNING id"
            ),
            {"tenant_id": tenant_id, "id": approval_id},
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=409,
            detail="register.approval_already_consumed",
        )
