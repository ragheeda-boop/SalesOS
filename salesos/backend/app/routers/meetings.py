"""Meeting & Email Intelligence REST API."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session, require_permission_dep
from app.common.rate_limit import rate_limit_dep
from sdk.permissions import PermissionAction
from domains.commercial.meeting.intelligence import MeetingIntelligenceService
from domains.commercial.email import EmailIntelligence, Email
from domains.commercial.infrastructure.postgres_repositories import (
    PostgresMeetingRepository, PostgresEmailRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class EmailRequest(BaseModel):
    opportunity_id: str = Field(max_length=100)
    subject: str = Field(max_length=500)
    from_address: str = Field(max_length=254)
    to_addresses: list[str] = Field(default_factory=list, max_length=20)
    body: str = Field(max_length=50000)
    direction: str = Field(default="outbound", pattern="^(inbound|outbound)$")
    email_type: str = Field(default="general", max_length=50)


class MeetingSummaryRequest(BaseModel):
    notes: str = Field(max_length=50000)
    meeting_id: str | None = Field(None, max_length=100)


# ── Repository factories ──

def _get_meeting_repo(db: AsyncSession) -> PostgresMeetingRepository:
    return PostgresMeetingRepository(db)


def _get_email_repo(db: AsyncSession) -> PostgresEmailRepository:
    return PostgresEmailRepository(db)


# ── Meetings ──

@router.get("/meetings/{opportunity_id}")
async def get_meetings(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep(PermissionAction.READ, "meeting")),
):
    try:
        repo = _get_meeting_repo(db)
        meetings = await repo.list_by_opportunity(opportunity_id, tenant_id)
        return [
            {
                "id": m.id, "title": m.title,
                "meeting_date": m.meeting_date.isoformat() if m.meeting_date else None,
                "duration_minutes": m.duration_minutes,
                "notes": m.notes, "status": m.status,
            }
            for m in meetings
        ]
    except Exception as exc:
        logger.error("get_meetings failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/meetings/{opportunity_id}/brief",
             dependencies=[Depends(rate_limit_dep("meeting_brief", 10, 60))])
async def get_meeting_brief(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep(PermissionAction.READ, "meeting")),
):
    try:
        from domains.commercial.infrastructure.postgres_repositories import PostgresOpportunityRepository
        opp_repo = PostgresOpportunityRepository(db)
        opp = await opp_repo.get(opportunity_id)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        service = MeetingIntelligenceService(db, tenant_id)
        return await service.generate_brief(opportunity_id, opp.company_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_meeting_brief failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/meetings/{opportunity_id}/summary",
             dependencies=[Depends(rate_limit_dep("meeting_summary", 10, 60))])
async def get_meeting_summary(
    opportunity_id: str,
    body: MeetingSummaryRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep(PermissionAction.CREATE, "meeting")),
):
    try:
        service = MeetingIntelligenceService(db, tenant_id)
        return await service.generate_summary(body.model_dump())
    except Exception as exc:
        logger.error("get_meeting_summary failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Emails ──

@router.get("/emails/{opportunity_id}")
async def get_emails(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    _rbac: None = Depends(require_permission_dep(PermissionAction.READ, "email")),
):
    try:
        repo = _get_email_repo(db)
        emails = await repo.list_by_opportunity(opportunity_id, tenant_id)
        return [
            {
                "id": e.id, "subject": e.subject,
                "from_address": e.from_address,
                "to_addresses": e.to_addresses,
                "direction": e.direction,
                "email_type": e.email_type,
                "sent_at": e.sent_at.isoformat() if e.sent_at else None,
                "body_preview": (e.body or "")[:200],
            }
            for e in emails
        ]
    except Exception as exc:
        logger.error("get_emails failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/emails/analyze",
             dependencies=[Depends(rate_limit_dep("email_analyze", 20, 60))])
async def analyze_email(
    email_req: EmailRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _rbac: None = Depends(require_permission_dep(PermissionAction.CREATE, "email")),
):
    email = Email(
        id="preview",
        tenant_id=tenant_id,
        opportunity_id=email_req.opportunity_id,
        subject=email_req.subject,
        from_address=email_req.from_address,
        to_addresses=email_req.to_addresses,
        body=email_req.body,
        direction=email_req.direction,
        email_type=email_req.email_type,
    )
    intelligence = EmailIntelligence()
    return intelligence.analyze(email)
