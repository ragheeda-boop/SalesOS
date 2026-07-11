"""Meeting & Email Intelligence REST API."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_tenant_id, get_db_session
from domains.commercial.meeting.intelligence import MeetingIntelligenceService
from domains.commercial.email import EmailIntelligence, Email

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


# ── Meetings ──

@router.get("/meetings/{opportunity_id}")
async def get_meetings(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        result = await db.execute(
            sa_text("""
                SELECT id, title, meeting_date, duration_minutes, notes, status
                FROM meetings WHERE opportunity_id = :oid AND tenant_id = :tid
                ORDER BY meeting_date DESC LIMIT 50
            """),
            {"oid": opportunity_id, "tid": tenant_id},
        )
        return [dict(r) for r in result.mappings().all()]
    except Exception as exc:
        logger.error("get_meetings failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/meetings/{opportunity_id}/brief")
async def get_meeting_brief(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        opp = await db.execute(
            sa_text("SELECT company_id FROM commercial_opportunities WHERE id = :oid AND tenant_id = :tid"),
            {"oid": opportunity_id, "tid": tenant_id},
        )
        op = opp.mappings().one_or_none()
        if not op:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        service = MeetingIntelligenceService(db, tenant_id)
        return await service.generate_brief(opportunity_id, str(op["company_id"]))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_meeting_brief failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/meetings/{opportunity_id}/summary")
async def get_meeting_summary(
    opportunity_id: str,
    body: MeetingSummaryRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
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
):
    try:
        result = await db.execute(
            sa_text("""
                SELECT id, subject, from_address, to_addresses, direction, email_type, sent_at,
                       LEFT(body, 200) as body_preview
                FROM emails WHERE opportunity_id = :oid AND tenant_id = :tid
                ORDER BY sent_at DESC LIMIT 20
            """),
            {"oid": opportunity_id, "tid": tenant_id},
        )
        return [dict(r) for r in result.mappings().all()]
    except Exception as exc:
        logger.error("get_emails failed: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/emails/analyze")
async def analyze_email(
    email_req: EmailRequest,
    tenant_id: str = Depends(get_current_tenant_id),
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
