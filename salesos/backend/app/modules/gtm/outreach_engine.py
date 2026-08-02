"""STORY-11-08 — AI Outreach engine (CAP-103).

Honesty: FixtureOutreachGenerator + governed prompt-registry key.
No live LLM, SMTP send, LinkedIn, or WhatsApp.
feature_ai_copilot remains False. Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.modules.gtm.outreach import (
    OUTREACH_PROMPT_ID,
    OUTREACH_PROMPT_VERSION,
    OutreachError,
    OutreachRequest,
)

# CAP-023-shaped prompt catalog entry (in-module; not live Studio Prompt Library).
GOVERNED_OUTREACH_PROMPT: dict[str, str] = {
    "id": OUTREACH_PROMPT_ID,
    "version": OUTREACH_PROMPT_VERSION,
    "template": (
        "Draft {channel} outreach ({intent}) to {contact_name} at {company_name}. "
        "Title: {contact_title}. Value: {value_prop}. "
        "Website intel: {website_summary}. ICP: {icp_notes}."
    ),
    "domain": "gtm",
    "category": "ai_outreach",
    "active": "true",
}


@runtime_checkable
class OutreachGenerator(Protocol):
    """Platform LLM-spend adapter for outreach copy — CI uses fixture."""

    @property
    def generator_key(self) -> str:
        """Stable generator id (e.g. ``fixture_outreach``) — not a secret."""
        ...

    async def generate(
        self,
        request: OutreachRequest,
        *,
        prompt: dict[str, str],
    ) -> tuple[str, str, list[str]]:
        """Return subject, body, warnings. Must not invent live delivery."""
        ...


@dataclass
class FixtureOutreachGenerator:
    """Deterministic fixture generator — Prompt Registry spend-path shape only."""

    key: str = "fixture_outreach"

    @property
    def generator_key(self) -> str:
        return self.key

    async def generate(
        self,
        request: OutreachRequest,
        *,
        prompt: dict[str, str],
    ) -> tuple[str, str, list[str]]:
        if not isinstance(request, OutreachRequest):
            raise OutreachError("request required")
        if not prompt or prompt.get("id") != OUTREACH_PROMPT_ID:
            raise OutreachError("governed AI outreach prompt required")

        contact = request.contact_name or "there"
        title_bit = f" ({request.contact_title})" if request.contact_title else ""
        intent_label = {
            "intro": "quick intro",
            "follow_up": "follow-up",
            "breakup": "closing note",
        }.get(request.intent, "note")

        subject = f"{intent_label.title()} for {request.company_name}"
        value = request.value_prop or "how peers shorten cycle time with governed GTM workflows"
        website_bit = ""
        if request.website_summary:
            website_bit = f"\n\nI noticed: {request.website_summary[:240]}"
        icp_bit = ""
        if request.icp_notes:
            icp_bit = f"\nICP fit notes: {request.icp_notes[:160]}"

        body = (
            f"Hi {contact}{title_bit},\n\n"
            f"This is a {intent_label} regarding {request.company_name}. "
            f"We help teams with {value}.{website_bit}{icp_bit}\n\n"
            f"— Draft via {OUTREACH_PROMPT_ID} v{OUTREACH_PROMPT_VERSION} "
            f"(fixture; live LLM/SMTP not claimed)\n"
        )
        warnings = [
            "draft_only — no SMTP send",
            "feature_ai_copilot=False",
            "FE Decision package is STUB — not used for generation",
        ]
        return subject, body, warnings


async def run_outreach_draft(
    request: OutreachRequest,
    generator: OutreachGenerator,
    *,
    prompt: dict[str, str] | None = None,
) -> tuple[str, str, list[str], dict[str, str]]:
    if not isinstance(generator, OutreachGenerator):
        raise OutreachError("generator must implement OutreachGenerator")
    bound: dict[str, str] = {**prompt} if prompt is not None else {**GOVERNED_OUTREACH_PROMPT}
    subject, body, warnings = await generator.generate(request, prompt=bound)
    return subject, body, warnings, bound
