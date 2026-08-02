"""STORY-11-08 — In-memory AI outreach drafts (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.gtm.outreach import (
    OUTREACH_PROMPT_ID,
    OutreachDraft,
    OutreachError,
    normalize_request,
)
from app.modules.gtm.outreach_engine import (
    FixtureOutreachGenerator,
    OutreachGenerator,
    run_outreach_draft,
)


@dataclass
class MemOutreachStore:
    """Tenant-scoped outreach drafts for CAP-103."""

    _by_id: dict[str, OutreachDraft] = field(default_factory=dict)
    _generators: dict[str, OutreachGenerator] = field(default_factory=dict)
    _default_key: str = "fixture_outreach"

    def __post_init__(self) -> None:
        if not self._generators:
            default = FixtureOutreachGenerator(key=self._default_key)
            self._generators = {default.generator_key: default}

    def bind_generator(self, generator: OutreachGenerator, *, default: bool = False) -> None:
        self._generators[generator.generator_key] = generator
        if default or len(self._generators) == 1:
            self._default_key = generator.generator_key

    def generator_keys(self) -> list[str]:
        return sorted(self._generators.keys())

    def _resolve(self, generator_key: str) -> OutreachGenerator:
        key = (generator_key or "").strip() or self._default_key
        gen = self._generators.get(key)
        if gen is None:
            raise OutreachError(f"unknown outreach generator: {key}")
        return gen

    async def draft(
        self,
        *,
        tenant_id: str,
        company_name: str,
        contact_name: str | None = None,
        contact_title: str | None = None,
        channel: str | None = None,
        intent: str | None = None,
        value_prop: str | None = None,
        website_summary: str | None = None,
        icp_notes: str | None = None,
        generator_key: str | None = None,
        run_id: str | None = None,
    ) -> OutreachDraft:
        tid = (tenant_id or "").strip()
        if not tid:
            raise OutreachError("tenant_id required")

        request = normalize_request(
            company_name=company_name,
            contact_name=contact_name,
            contact_title=contact_title,
            channel=channel,
            intent=intent,
            value_prop=value_prop,
            website_summary=website_summary,
            icp_notes=icp_notes,
        )
        generator = self._resolve(generator_key or "")
        subject, body, warnings, prompt = await run_outreach_draft(request, generator)

        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = self._by_id.get(rid)
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant outreach write blocked")

        row = OutreachDraft(
            id=rid,
            tenant_id=tid,
            request=request,
            subject=subject,
            body=body,
            channel=request.channel,
            prompt_id=str(prompt.get("id") or OUTREACH_PROMPT_ID),
            prompt_version=str(prompt.get("version") or "1.0.0"),
            spend_path="platform_llm_budget",
            generator_key=generator.generator_key,
            delivery_status="draft_only",
            schema_version=(existing.schema_version + 1) if existing else 1,
            created_at=datetime.now(UTC).isoformat(),
            warnings=list(warnings),
        )
        self._by_id[row.id] = row
        return row

    def get(self, run_id: str, *, tenant_id: str) -> OutreachDraft | None:
        row = self._by_id.get(str(run_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[OutreachDraft]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: r.created_at or "",
            reverse=True,
        )


DEFAULT_OUTREACH_STORE = MemOutreachStore()
