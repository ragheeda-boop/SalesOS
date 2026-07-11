"""Meeting & Email Intelligence REST API."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.dependencies import get_current_tenant_id, get_db_session
from domains.commercial.meeting.intelligence import MeetingIntelligenceService
from domains.commercial.email import EmailIntelligence, Email

router = APIRouter()


class EmailRequest(BaseModel):
    opportunity_id: str
    subject: str
    from_address: str
    to_addresses: list[str]
    body: str
    direction: str = "outbound"
    email_type: str = "general"


# ── Meetings ──

@router.get("/meetings/{opportunity_id}")
async def get_meetings(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from sqlalchemy import text as sa_text
    result = await db.execute(
        sa_text("""
            SELECT id, title, meeting_date, duration_minutes, notes, status
            FROM meetings WHERE opportunity_id = :oid AND tenant_id = :tid
            ORDER BY meeting_date DESC
        """),
        {"oid": opportunity_id, "tid": tenant_id},
    )
    return [dict(r) for r in result.mappings().all()]


@router.post("/meetings/{opportunity_id}/brief")
async def get_meeting_brief(
    opportunity_id: str,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from sqlalchemy import text as sa_text
    opp = await db.execute(
        sa_text("SELECT company_id FROM commercial_opportunities WHERE id = :oid"),
        {"oid": opportunity_id},
    )
    op = opp.mappings().one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    service = MeetingIntelligenceService(db, tenant_id)
    return await service.generate_brief(opportunity_id, str(op["company_id"]))


@router.post("/meetings/{opportunity_id}/summary")
async def get_meeting_summary(
    opportunity_id: str,
    body: dict,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    service = MeetingIntelligenceService(db, tenant_id)
    return await service.generate_summary(body)


# ── Emails ──

@router.get("/emails/{opportunity_id}")
async def get_emails(
    opportunity_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
):
    from sqlalchemy import text as sa_text
    result = await db.execute(
        sa_text("""
            SELECT id, subject, from_address, to_addresses, body, direction, email_type, sent_at
            FROM emails WHERE opportunity_id = :oid AND tenant_id = :tid
            ORDER BY sent_at DESC LIMIT 20
        """),
        {"oid": opportunity_id, "tid": tenant_id},
    )
    return [dict(r) for r in result.mappings().all()]


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
