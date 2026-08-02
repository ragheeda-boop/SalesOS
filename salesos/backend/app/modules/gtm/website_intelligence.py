"""STORY-11-07 — CAP-101 Website Intelligence models (OBJ-355).

Reuses platform Prompt Registry / LLM-spend path — no separate per-row vendor.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
feature_ai_copilot remains False.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class WebsiteIntelligenceError(ValueError):
    """Invalid website intelligence request or analysis input."""


# Governed CAP-023-shaped prompt id (fixture registry — not live Studio Prompt Library).
WEBSITE_INTEL_PROMPT_ID = "gtm.website_intelligence.v1"
WEBSITE_INTEL_PROMPT_VERSION = "1.0.0"


@dataclass(frozen=True)
class WebsiteSignal:
    """Single extracted signal from a website analysis pass."""

    key: str
    value: str
    confidence: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
        }


@dataclass
class WebsiteIntelligenceRequest:
    """Input seed for website intelligence (URL + optional context)."""

    url: str
    company_name: str = ""
    page_snippet: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "company_name": self.company_name,
            "page_snippet": self.page_snippet,
        }


@dataclass
class WebsiteIntelligenceSnapshot:
    """OBJ-355-shaped website intelligence snapshot (in-memory)."""

    id: str
    tenant_id: str
    request: WebsiteIntelligenceRequest
    summary: str = ""
    signals: list[WebsiteSignal] = field(default_factory=list)
    prompt_id: str = WEBSITE_INTEL_PROMPT_ID
    prompt_version: str = WEBSITE_INTEL_PROMPT_VERSION
    spend_path: str = "platform_llm_budget"
    analyzer_key: str = "fixture_website"
    schema_version: int = 1
    created_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "request": self.request.as_dict(),
            "summary": self.summary,
            "signals": [s.as_dict() for s in self.signals],
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "spend_path": self.spend_path,
            "analyzer_key": self.analyzer_key,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "signal_count": len(self.signals),
        }


def normalize_request(
    *,
    url: str,
    company_name: str | None = None,
    page_snippet: str | None = None,
) -> WebsiteIntelligenceRequest:
    raw = (url or "").strip()
    if not raw:
        raise WebsiteIntelligenceError("url required")
    lowered = raw.lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        raise WebsiteIntelligenceError("url must start with http:// or https://")
    if "://" not in raw or len(raw.split("://", 1)[1].strip()) < 1:
        raise WebsiteIntelligenceError("url host required")
    return WebsiteIntelligenceRequest(
        url=raw,
        company_name=(company_name or "").strip(),
        page_snippet=(page_snippet or "").strip()[:4000],
    )
