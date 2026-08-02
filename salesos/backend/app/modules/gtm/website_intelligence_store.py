"""STORY-11-07 — In-memory website intelligence snapshots (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.website_intelligence import (
    WEBSITE_INTEL_PROMPT_ID,
    WebsiteIntelligenceError,
    WebsiteIntelligenceSnapshot,
    normalize_request,
)
from app.modules.gtm.website_intelligence_engine import (
    FixtureWebsiteAnalyzer,
    WebsiteAnalyzer,
    run_website_intelligence,
)


@dataclass
class MemWebsiteIntelligenceStore:
    """Tenant-scoped website intelligence snapshots for CAP-101."""

    _by_id: dict[str, WebsiteIntelligenceSnapshot] = field(default_factory=dict)
    _analyzers: dict[str, WebsiteAnalyzer] = field(default_factory=dict)
    _default_key: str = "fixture_website"

    def __post_init__(self) -> None:
        if not self._analyzers:
            default = FixtureWebsiteAnalyzer(key=self._default_key)
            self._analyzers = {default.analyzer_key: default}

    def bind_analyzer(self, analyzer: WebsiteAnalyzer, *, default: bool = False) -> None:
        self._analyzers[analyzer.analyzer_key] = analyzer
        if default or len(self._analyzers) == 1:
            self._default_key = analyzer.analyzer_key

    def analyzer_keys(self) -> list[str]:
        return sorted(self._analyzers.keys())

    def _resolve(self, analyzer_key: str) -> WebsiteAnalyzer:
        key = (analyzer_key or "").strip() or self._default_key
        analyzer = self._analyzers.get(key)
        if analyzer is None:
            raise WebsiteIntelligenceError(f"unknown website analyzer: {key}")
        return analyzer

    async def analyze(
        self,
        *,
        tenant_id: str,
        url: str,
        company_name: str | None = None,
        page_snippet: str | None = None,
        analyzer_key: str | None = None,
        run_id: str | None = None,
    ) -> WebsiteIntelligenceSnapshot:
        tid = (tenant_id or "").strip()
        if not tid:
            raise WebsiteIntelligenceError("tenant_id required")

        request = normalize_request(
            url=url,
            company_name=company_name,
            page_snippet=page_snippet,
        )
        analyzer = self._resolve(analyzer_key or "")
        summary, signals, prompt = await run_website_intelligence(request, analyzer)

        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant website intelligence write blocked")

        row = WebsiteIntelligenceSnapshot(
            id=rid,
            tenant_id=tid,
            request=request,
            summary=summary,
            signals=list(signals),
            prompt_id=str(prompt.get("id") or WEBSITE_INTEL_PROMPT_ID),
            prompt_version=str(prompt.get("version") or "1.0.0"),
            spend_path="platform_llm_budget",
            analyzer_key=analyzer.analyzer_key,
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._by_id[row.id] = row
        return row

    def get(self, run_id: str, *, tenant_id: str) -> WebsiteIntelligenceSnapshot | None:
        row = self._by_id.get(str(run_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[WebsiteIntelligenceSnapshot]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.created_at or "",
            reverse=True,
        )


DEFAULT_WEBSITE_INTEL_STORE = MemWebsiteIntelligenceStore()
