"""
Preamble Builder — generates session context for agent execution.

Reads UBOM, FeatureStore, and KnowledgeGraph to build a rich markdown
preamble that tells the agent what it's working on and what tools
are available.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from runtime.agent_runtime.models import AgentTask


async def build_preamble(
    session: AsyncSession,
    task: AgentTask,
    tenant_id: str,
) -> str:
    lines = ["## Session Context", ""]
    lines.append(f"Task: **{task.kind}**")
    if task.input_data.get("reason"):
        lines.append(f"Why: {task.input_data['reason']}")
    lines.append(f"Budget: **{task.budget}** vendor calls.")
    lines.append("")

    if task.entity_type == "company" and task.entity_id:
        company = await _load_company(session, task.entity_id)
        if company:
            lines.append(f"Working on: **{company['name_ar'] or company['name_en'] or 'Unknown'}**")
            if company.get("cr_number"):
                lines.append(f"CR: {company['cr_number']}")
            if company.get("industry"):
                lines.append(f"Industry: {company['industry']}")
            if company.get("city"):
                lines.append(f"Location: {company['city']}, {company.get('region', '')}")
            if company.get("employees_count"):
                lines.append(f"Employees: ~{company['employees_count']}")
            if company.get("activity_description"):
                lines.append(f"Activity: {company['activity_description'][:200]}")
            lines.append("")

    elif task.entity_type == "contact" and task.entity_id:
        contact = await _load_contact(session, task.entity_id)
        if contact:
            lines.append(f"Working on: **{contact['name']}**")
            if contact.get("position"):
                lines.append(f"Position: {contact['position']}")
            if contact.get("email"):
                lines.append(f"Email: {contact['email']}")
            lines.append("")

    lines.append("Start with what the CRM already holds. Use external sources only where needed.")
    if task.attempts > 1:
        lines.append(f"(Attempt {task.attempts} of {task.max_attempts}. Earlier attempt may have partial context.)")

    return "\n".join(lines)


async def _load_company(session: AsyncSession, company_id: str) -> dict | None:
    result = await session.execute(
        text("""
            SELECT name_ar, name_en, cr_number, industry, city, region,
                   employees_count, activity_description, confidence_score
            FROM companies WHERE id = :cid
        """),
        {"cid": company_id},
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None


async def _load_contact(session: AsyncSession, contact_id: str) -> dict | None:
    result = await session.execute(
        text("""
            SELECT name, name_ar, position, email, phone, department, source
            FROM contacts WHERE id = :cid
        """),
        {"cid": contact_id},
    )
    row = result.fetchone()
    return dict(row._mapping) if row else None
