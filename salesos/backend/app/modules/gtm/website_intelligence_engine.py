"""STORY-11-07 — Website Intelligence engine (CAP-101).

Honesty: FixtureWebsiteAnalyzer + governed prompt-registry key.
No live crawl, live LLM, Claygent/Clay vendor, or RAG GO.
feature_ai_copilot remains False. Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from urllib.parse import urlparse

from app.modules.gtm.website_intelligence import (
    WEBSITE_INTEL_PROMPT_ID,
    WEBSITE_INTEL_PROMPT_VERSION,
    WebsiteIntelligenceError,
    WebsiteIntelligenceRequest,
    WebsiteSignal,
)

# CAP-023-shaped prompt catalog entry (in-module; not live Studio Prompt Library).
# All values are str so mypy accepts dict[str, str] spend-path bindings.
GOVERNED_WEBSITE_PROMPT: dict[str, str] = {
    "id": WEBSITE_INTEL_PROMPT_ID,
    "version": WEBSITE_INTEL_PROMPT_VERSION,
    "template": (
        "Analyze company website {url} for {company_name}. "
        "Extract industry, offerings, tech hints, and tone. "
        "Snippet: {page_snippet}"
    ),
    "domain": "gtm",
    "category": "website_intelligence",
    "active": "true",
}


@runtime_checkable
class WebsiteAnalyzer(Protocol):
    """Platform LLM-spend adapter — swappable; CI uses fixture."""

    @property
    def analyzer_key(self) -> str:
        """Stable analyzer id (e.g. ``fixture_website``) — not a secret."""
        ...

    async def analyze(
        self,
        request: WebsiteIntelligenceRequest,
        *,
        prompt: dict[str, str],
    ) -> tuple[str, list[WebsiteSignal]]:
        """Return summary + signals. Must not invent live vendor calls."""
        ...


def _host(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().strip(".")
        return host.removeprefix("www.")
    except Exception as exc:  # noqa: BLE001
        raise WebsiteIntelligenceError("url parse failed") from exc


# Deterministic demo catalog (not live crawl).
_FIXTURE_CATALOG: dict[str, tuple[str, list[WebsiteSignal]]] = {
    "acme-saas.test": (
        "Acme SaaS positions B2B workflow automation for mid-market ops teams.",
        [
            WebsiteSignal("industry", "saas", 0.9),
            WebsiteSignal("offering", "workflow automation", 0.85),
            WebsiteSignal("buyer", "operations / IT", 0.75),
            WebsiteSignal("tone", "product-led, concise", 0.7),
            WebsiteSignal("tech_hint", "api-first", 0.65),
        ],
    ),
    "riyal-retail.test": (
        "Riyal Retail highlights GCC omnichannel retail and Arabic storefronts.",
        [
            WebsiteSignal("industry", "retail", 0.9),
            WebsiteSignal("region", "gcc", 0.85),
            WebsiteSignal("offering", "omnichannel retail", 0.8),
            WebsiteSignal("tone", "brand-forward Arabic/English", 0.7),
            WebsiteSignal("tech_hint", "ecommerce", 0.6),
        ],
    ),
}


@dataclass
class FixtureWebsiteAnalyzer:
    """Deterministic fixture analyzer — reuses prompt-registry spend path shape.

    Does not call live LLM providers. Does not crawl the public web.
    """

    key: str = "fixture_website"
    catalog: dict[str, tuple[str, list[WebsiteSignal]]] = field(
        default_factory=lambda: dict(_FIXTURE_CATALOG)
    )

    @property
    def analyzer_key(self) -> str:
        return self.key

    async def analyze(
        self,
        request: WebsiteIntelligenceRequest,
        *,
        prompt: dict[str, str],
    ) -> tuple[str, list[WebsiteSignal]]:
        if not isinstance(request, WebsiteIntelligenceRequest):
            raise WebsiteIntelligenceError("request required")
        if not prompt or prompt.get("id") != WEBSITE_INTEL_PROMPT_ID:
            raise WebsiteIntelligenceError("governed website intelligence prompt required")

        host = _host(request.url)
        if host in self.catalog:
            summary, signals = self.catalog[host]
            return summary, list(signals)

        return self._derive(request, host)

    def _derive(
        self,
        request: WebsiteIntelligenceRequest,
        host: str,
    ) -> tuple[str, list[WebsiteSignal]]:
        tokens = [
            t
            for t in host.replace("-", ".").split(".")
            if t and t not in {"test", "com", "net", "io", "sa"}
        ]
        name = request.company_name or (tokens[0].title() if tokens else "Unknown")
        snippet_l = (request.page_snippet or "").lower()
        signals: list[WebsiteSignal] = []

        industry = "general"
        for needle, label in (
            ("saas", "saas"),
            ("software", "software"),
            ("retail", "retail"),
            ("health", "healthcare"),
            ("bank", "financial_services"),
            ("construct", "construction"),
        ):
            if needle in host or needle in snippet_l or needle in name.lower():
                industry = label
                break
        signals.append(WebsiteSignal("industry", industry, 0.55 if industry != "general" else 0.35))

        if "api" in snippet_l:
            signals.append(WebsiteSignal("tech_hint", "api", 0.6))
        if "arabic" in snippet_l or "gcc" in snippet_l:
            signals.append(WebsiteSignal("region", "gcc", 0.65))
        if tokens:
            signals.append(WebsiteSignal("host_token", tokens[0], 0.5))
        signals.append(WebsiteSignal("tone", "neutral fixture", 0.4))

        summary = (
            f"Fixture analysis for {name} ({host}) via {WEBSITE_INTEL_PROMPT_ID} "
            f"v{WEBSITE_INTEL_PROMPT_VERSION}; live crawl/LLM not claimed."
        )
        return summary, signals


async def run_website_intelligence(
    request: WebsiteIntelligenceRequest,
    analyzer: WebsiteAnalyzer,
    *,
    prompt: dict[str, str] | None = None,
) -> tuple[str, list[WebsiteSignal], dict[str, str]]:
    """Execute analysis through governed prompt + analyzer adapter."""
    if not isinstance(analyzer, WebsiteAnalyzer):
        raise WebsiteIntelligenceError("analyzer must implement WebsiteAnalyzer")
    bound: dict[str, str] = {**prompt} if prompt is not None else {**GOVERNED_WEBSITE_PROMPT}
    summary, signals = await analyzer.analyze(request, prompt=bound)
    return summary, signals, bound
