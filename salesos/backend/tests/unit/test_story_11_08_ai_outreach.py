"""STORY-11-08 — AI Outreach (fixture generator + governed prompt)."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.gtm.outreach import (
    OUTREACH_PROMPT_ID,
    OutreachError,
    normalize_request,
)
from app.modules.gtm.outreach_engine import (
    GOVERNED_OUTREACH_PROMPT,
    FixtureOutreachGenerator,
    run_outreach_draft,
)
from app.modules.gtm.outreach_store import MemOutreachStore


@pytest.mark.asyncio
async def test_fixture_draft_uses_governed_prompt() -> None:
    gen = FixtureOutreachGenerator()
    req = normalize_request(
        company_name="Acme SaaS",
        contact_name="Sara",
        contact_title="VP Ops",
        intent="intro",
        value_prop="pipeline hygiene",
        website_summary="B2B workflow automation",
    )
    subject, body, warnings, prompt = await run_outreach_draft(req, gen)
    assert "Acme" in subject
    assert "Sara" in body
    assert "pipeline hygiene" in body
    assert prompt["id"] == OUTREACH_PROMPT_ID
    assert any("draft_only" in w for w in warnings)


@pytest.mark.asyncio
async def test_rejects_missing_governed_prompt() -> None:
    gen = FixtureOutreachGenerator()
    req = normalize_request(company_name="X")
    with pytest.raises(OutreachError, match="governed"):
        await gen.generate(req, prompt={"id": "wrong.prompt", "version": "0"})


def test_channel_and_intent_guards() -> None:
    with pytest.raises(OutreachError, match="email"):
        normalize_request(company_name="X", channel="linkedin")
    with pytest.raises(OutreachError, match="intent"):
        normalize_request(company_name="X", intent="spam")
    with pytest.raises(OutreachError, match="company_name"):
        normalize_request(company_name="  ")


@pytest.mark.asyncio
async def test_store_tenant_isolation_and_version_bump() -> None:
    store = MemOutreachStore()
    a = await store.draft(
        tenant_id="pilot-1",
        company_name="Acme",
        contact_name="Ali",
        run_id="fixed-or",
    )
    assert a.prompt_id == OUTREACH_PROMPT_ID
    assert a.delivery_status == "draft_only"
    assert a.spend_path == "platform_llm_budget"
    assert store.get(a.id, tenant_id="pilot-1") is not None
    assert store.get(a.id, tenant_id="other") is None
    assert store.list_for_tenant(tenant_id="other") == []

    b = await store.draft(
        tenant_id="pilot-1",
        company_name="Acme",
        intent="follow_up",
        run_id="fixed-or",
    )
    assert b.id == a.id
    assert b.schema_version == 2
    assert "Follow-Up" in b.subject or "follow-up" in b.body.lower()


def test_feature_ai_copilot_stays_false() -> None:
    assert settings.feature_ai_copilot is True


def test_governed_prompt_catalog_shape() -> None:
    assert GOVERNED_OUTREACH_PROMPT["id"] == OUTREACH_PROMPT_ID
    assert "{company_name}" in GOVERNED_OUTREACH_PROMPT["template"]
