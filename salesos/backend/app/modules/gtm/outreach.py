"""STORY-11-08 — CAP-103 AI Outreach models (OBJ-353-adjacent draft).

Routed through governed CAP-023 Prompt Registry — not a disconnected copy tool.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
feature_ai_copilot remains False. No live SMTP / LinkedIn / WhatsApp.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class OutreachError(ValueError):
    """Invalid AI outreach draft request or prompt binding."""


# Governed CAP-023-shaped prompt id (fixture registry — not live Studio Prompt Library).
OUTREACH_PROMPT_ID = "gtm.ai_outreach.v1"
OUTREACH_PROMPT_VERSION = "1.0.0"


@dataclass
class OutreachRequest:
    """Seed for governed outreach draft generation."""

    company_name: str
    contact_name: str = ""
    contact_title: str = ""
    channel: str = "email"
    intent: str = "intro"
    value_prop: str = ""
    website_summary: str = ""
    icp_notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "contact_title": self.contact_title,
            "channel": self.channel,
            "intent": self.intent,
            "value_prop": self.value_prop,
            "website_summary": self.website_summary,
            "icp_notes": self.icp_notes,
        }


@dataclass
class OutreachDraft:
    """Governed outreach draft (in-memory) — not a sent message."""

    id: str
    tenant_id: str
    request: OutreachRequest
    subject: str = ""
    body: str = ""
    channel: str = "email"
    prompt_id: str = OUTREACH_PROMPT_ID
    prompt_version: str = OUTREACH_PROMPT_VERSION
    spend_path: str = "platform_llm_budget"
    generator_key: str = "fixture_outreach"
    delivery_status: str = "draft_only"
    schema_version: int = 1
    created_at: str = ""
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "request": self.request.as_dict(),
            "subject": self.subject,
            "body": self.body,
            "channel": self.channel,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "spend_path": self.spend_path,
            "generator_key": self.generator_key,
            "delivery_status": self.delivery_status,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "warnings": list(self.warnings),
        }


def normalize_request(
    *,
    company_name: str,
    contact_name: str | None = None,
    contact_title: str | None = None,
    channel: str | None = None,
    intent: str | None = None,
    value_prop: str | None = None,
    website_summary: str | None = None,
    icp_notes: str | None = None,
) -> OutreachRequest:
    name = (company_name or "").strip()
    if not name:
        raise OutreachError("company_name required")
    ch = (channel or "email").strip().lower() or "email"
    if ch != "email":
        raise OutreachError("only email channel supported (LinkedIn/WhatsApp deferred)")
    intent_n = (intent or "intro").strip().lower() or "intro"
    if intent_n not in {"intro", "follow_up", "breakup"}:
        raise OutreachError("intent must be intro|follow_up|breakup")
    return OutreachRequest(
        company_name=name,
        contact_name=(contact_name or "").strip(),
        contact_title=(contact_title or "").strip(),
        channel=ch,
        intent=intent_n,
        value_prop=(value_prop or "").strip()[:2000],
        website_summary=(website_summary or "").strip()[:4000],
        icp_notes=(icp_notes or "").strip()[:2000],
    )
