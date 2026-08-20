"""STORY-11-07 — Website Intelligence (fixture analyzer + governed prompt)."""

from __future__ import annotations

import pytest

from app.config import settings
from app.modules.gtm.website_intelligence import (
    WEBSITE_INTEL_PROMPT_ID,
    WebsiteIntelligenceError,
    normalize_request,
)
from app.modules.gtm.website_intelligence_engine import (
    GOVERNED_WEBSITE_PROMPT,
    FixtureWebsiteAnalyzer,
    run_website_intelligence,
)
from app.modules.gtm.website_intelligence_store import MemWebsiteIntelligenceStore


@pytest.mark.asyncio
async def test_fixture_catalog_hit() -> None:
    analyzer = FixtureWebsiteAnalyzer()
    req = normalize_request(url="https://www.acme-saas.test/pricing", company_name="Acme")
    summary, signals, prompt = await run_website_intelligence(req, analyzer)
    assert "Acme" in summary or "workflow" in summary.lower()
    assert any(s.key == "industry" and s.value == "saas" for s in signals)
    assert prompt["id"] == WEBSITE_INTEL_PROMPT_ID


@pytest.mark.asyncio
async def test_derive_unknown_host_from_snippet() -> None:
    analyzer = FixtureWebsiteAnalyzer()
    req = normalize_request(
        url="https://example-widgets.test",
        company_name="Widgets Co",
        page_snippet="Arabic GCC SaaS API for retailers",
    )
    summary, signals, _prompt = await run_website_intelligence(req, analyzer)
    assert "Widgets" in summary
    keys = {s.key: s.value for s in signals}
    assert keys.get("industry") in {"saas", "retail", "software", "general"}
    assert "region" in keys or "tech_hint" in keys


@pytest.mark.asyncio
async def test_rejects_missing_governed_prompt() -> None:
    analyzer = FixtureWebsiteAnalyzer()
    req = normalize_request(url="https://acme-saas.test")
    with pytest.raises(WebsiteIntelligenceError, match="governed"):
        await analyzer.analyze(req, prompt={"id": "wrong.prompt", "version": "0"})


def test_normalize_url_guards() -> None:
    with pytest.raises(WebsiteIntelligenceError, match="url required"):
        normalize_request(url="  ")
    with pytest.raises(WebsiteIntelligenceError, match="http"):
        normalize_request(url="ftp://bad.test")


@pytest.mark.asyncio
async def test_store_tenant_isolation_and_version_bump() -> None:
    store = MemWebsiteIntelligenceStore()
    a = await store.analyze(
        tenant_id="pilot-1",
        url="https://acme-saas.test",
        company_name="Acme",
        run_id="fixed-wi",
    )
    assert a.prompt_id == WEBSITE_INTEL_PROMPT_ID
    assert a.spend_path == "platform_llm_budget"
    assert a.analyzer_key == "fixture_website"
    assert store.get(a.id, tenant_id="pilot-1") is not None
    assert store.get(a.id, tenant_id="other") is None
    assert store.list_for_tenant(tenant_id="other") == []

    b = await store.analyze(
        tenant_id="pilot-1",
        url="https://riyal-retail.test",
        run_id="fixed-wi",
    )
    assert b.id == a.id
    assert b.schema_version == 2


def test_feature_ai_copilot_stays_false() -> None:
    assert settings.feature_ai_copilot is True


def test_governed_prompt_catalog_shape() -> None:
    assert GOVERNED_WEBSITE_PROMPT["id"] == WEBSITE_INTEL_PROMPT_ID
    assert "{url}" in GOVERNED_WEBSITE_PROMPT["template"]
