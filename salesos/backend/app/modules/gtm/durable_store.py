"""STORY-11-02..09 — durable per-tenant GTM capability results (Postgres layer).

The eight GTM capabilities that previously lived only in in-memory stores now
persist their result records (the model's as_dict()) as JSONB in a single
tenant-scoped table (migration s9t0u1v2w3x4) discriminated by ``capability``:

  market_sizing, lead_discovery, lookalike, enrichment, verification,
  website_intelligence, outreach, sequence_definition, sequence_enrollment

Isolation is enforced by DB RLS + FORCE RLS (canonical DEC-085 shape) AND by
pinning ``app.tenant_id`` around every statement here — defence in depth,
fail-closed, mirroring PostgresICPRepository (icp_persistence.py).

The compute kernels stay in the pure engine modules. PostgresGtmStore reuses
the exact model constructors and provider banks of the Mem stores so the HTTP
response contract is byte-identical to the in-memory behavior. Mem stores stay
as the synchronous test double.
"""

from __future__ import annotations

import inspect
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.gtm.enrichment import (
    ENRICHABLE_FIELDS,
    EnrichmentError,
    EnrichmentResult,
    normalize_request,
)
from app.modules.gtm.enrichment_engine import (
    EnrichmentProvider,
    build_default_providers,
    run_waterfall,
)
from app.modules.gtm.lead_discovery import (
    LeadDiscoveryError,
    LeadDiscoveryRun,
    normalize_query,
)
from app.modules.gtm.lead_discovery_engine import discover_leads
from app.modules.gtm.lookalike import (
    LookalikeError,
    LookalikeModel,
    normalize_seed,
)
from app.modules.gtm.lookalike_engine import (
    MemOpportunityHistory,
    rank_lookalikes,
)
from app.modules.gtm.market_sizing import (
    GOVERNMENT_DATASET_SCALE_HINT,
    MarketSizingError,
    MarketSizingSnapshot,
    normalize_criteria,
)
from app.modules.gtm.market_sizing_engine import (
    CompanyUniversePort,
    compute_tam_sam_som,
)
from app.modules.gtm.outreach import (
    OUTREACH_PROMPT_ID,
    OutreachDraft,
    OutreachError,
    normalize_request as normalize_outreach_request,
)
from app.modules.gtm.outreach_engine import (
    FixtureOutreachGenerator,
    OutreachGenerator,
    run_outreach_draft,
)
from app.modules.gtm.sequence_channels import (
    CompliantChannelSender,
    build_default_channel_senders,
)
from app.modules.gtm.sequencing import (
    BoundActivityRef,
    BoundTaskRef,
    EnrollmentStepState,
    SequenceDefinition,
    SequenceEnrollment,
    SequenceStep,
    SequencingError,
    normalize_steps,
)
from app.modules.gtm.sequencing_engine import (
    advance_enrollment,
    build_enrollment,
    cancel_enrollment,
    pause_enrollment,
    resume_enrollment,
)
from app.modules.gtm.verification import (
    VerificationError,
    VerificationResult,
    normalize_request as normalize_verification_request,
)
from app.modules.gtm.verification_engine import (
    MemVerificationConnector,
    VerificationConnector,
    run_verification,
)
from app.modules.gtm.website_intelligence import (
    WEBSITE_INTEL_PROMPT_ID,
    WebsiteIntelligenceError,
    WebsiteIntelligenceSnapshot,
    normalize_request as normalize_website_request,
)
from app.modules.gtm.website_intelligence_engine import (
    FixtureWebsiteAnalyzer,
    WebsiteAnalyzer,
    run_website_intelligence,
)
from app.modules.integration_hub.fake_adapter import FakeSourceConnector
from app.modules.integration_hub.source_connector import SourceConnector

ENROLLMENT_CAPABILITY = "sequence_enrollment"
DEFINITION_CAPABILITY = "sequence_definition"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _require_uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{field} must be a valid uuid") from None


@dataclass
class DurableRecord:
    """A persisted result record with the same shape routers already consume."""

    payload: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return self.payload


async def aresolve(value: Any) -> Any:
    """Resolve a possibly-awaitable result.

    Mem stores remain synchronous (compute/run/get/list); PostgresGtmStore is
    async. Handlers can await either via ``await aresolve(_STORE.xxx(...))``.
    """
    if inspect.isawaitable(value):
        return await value
    return value


def _demand_tenant(tenant_id: str | None) -> str:
    tid = (tenant_id or "").strip()
    if not tid:
        raise ValueError("tenant_id required")
    return tid


def _definition_from_payload(payload: dict[str, Any]) -> SequenceDefinition:
    return SequenceDefinition(
        id=str(payload["id"]),
        tenant_id=str(payload["tenant_id"]),
        name=str(payload["name"]),
        steps=[SequenceStep(**s) for s in payload.get("steps") or []],
        channel=str(payload.get("channel") or "email"),
        schema_version=int(payload.get("schema_version") or 1),
        created_at=str(payload.get("created_at") or ""),
        updated_at=str(payload.get("updated_at") or ""),
    )


def _enrollment_from_payload(payload: dict[str, Any]) -> SequenceEnrollment:
    return SequenceEnrollment(
        id=str(payload["id"]),
        tenant_id=str(payload["tenant_id"]),
        sequence_id=str(payload["sequence_id"]),
        contact_email=str(payload["contact_email"]),
        status=str(payload.get("status") or "active"),
        current_step_index=int(payload.get("current_step_index") or 0),
        step_states=[
            EnrollmentStepState(**s) for s in payload.get("step_states") or []
        ],
        task_bindings=[BoundTaskRef(**t) for t in payload.get("task_bindings") or []],
        activity_bindings=[
            BoundActivityRef(**a) for a in payload.get("activity_bindings") or []
        ],
        contact_handles=dict(payload.get("contact_handles") or {}),
        last_send=dict(payload.get("last_send") or {}),
        schema_version=int(payload.get("schema_version") or 1),
        created_at=str(payload.get("created_at") or ""),
        updated_at=str(payload.get("updated_at") or ""),
    )


class PostgresGtmStore:
    """Async Postgres-backed store speaking the same vocabulary as the Mem stores.

    ``capability`` selects the result-record class inside the single
    gtm_capability_results table. Provider banks default to the exact fixtures
    the Mem stores use, so the durable default behaves identically out of the
    box (honesty disclaimers in each /meta remain authoritative).
    """

    def __init__(self, *, capability: str, session_factory=None):
        self.capability = capability
        self._sessions = session_factory
        self._universe: CompanyUniversePort | None = None
        self._provider: SourceConnector | None = None
        self._history: MemOpportunityHistory | None = None
        self._providers: list[EnrichmentProvider] = list(build_default_providers())
        self._connectors: dict[str, VerificationConnector] = {}
        self._analyzers: dict[str, WebsiteAnalyzer] = {}
        self._generators: dict[str, OutreachGenerator] = {}
        self._senders: dict[str, CompliantChannelSender] = dict(
            build_default_channel_senders()
        )

    # ── session / GUC (canonical DEC-085 defence in depth) ───────────────
    def _session_ctx(self):
        if self._sessions is not None:
            return self._sessions()
        from app.database import async_session

        return async_session()

    @staticmethod
    async def _pin(db, tenant_id: str) -> None:
        await db.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)}
        )

    # ── provider / binding banks (same vocabulary as Mem stores) ──────────
    def bind_universe(self, universe: CompanyUniversePort) -> None:
        self._universe = universe

    def bind_provider(self, provider: SourceConnector | None) -> None:
        self._provider = provider

    def bind_history(self, history: MemOpportunityHistory) -> None:
        self._history = history

    def bind_providers(self, providers: list[EnrichmentProvider]) -> None:
        if len(providers) < 2:
            raise EnrichmentError("at least 2 enrichment providers required")
        self._providers = list(providers)

    def bind_connector(
        self, connector: VerificationConnector, *, default: bool = False
    ) -> None:
        self._connectors[connector.connector_key] = connector
        if default or len(self._connectors) == 1:
            self._default_connector_key = connector.connector_key

    def bind_analyzer(self, analyzer: WebsiteAnalyzer, *, default: bool = False) -> None:
        self._analyzers[analyzer.analyzer_key] = analyzer
        if default or len(self._analyzers) == 1:
            self._default_analyzer_key = analyzer.analyzer_key

    def bind_generator(
        self, generator: OutreachGenerator, *, default: bool = False
    ) -> None:
        self._generators[generator.generator_key] = generator
        if default or len(self._generators) == 1:
            self._default_generator_key = generator.generator_key

    def bind_senders(self, senders: dict[str, CompliantChannelSender]) -> None:
        self._senders = dict(senders)

    def provider_keys(self) -> list[str]:
        return [p.provider_key for p in self._providers]

    def connector_keys(self) -> list[str]:
        return sorted(self._connectors.keys())

    def analyzer_keys(self) -> list[str]:
        return sorted(self._analyzers.keys())

    def generator_keys(self) -> list[str]:
        return sorted(self._generators.keys())

    def _resolve_universe(self) -> CompanyUniversePort:
        if self._universe is not None:
            return self._universe
        from app.modules.gtm.market_sizing_store import build_demo_government_universe

        self._universe = build_demo_government_universe()
        return self._universe

    def _resolve_history(self) -> MemOpportunityHistory:
        if self._history is None:
            self._history = MemOpportunityHistory()
        return self._history

    async def ensure_default_provider(self) -> SourceConnector:
        if self._provider is None:
            from app.modules.gtm.lead_discovery_store import (
                seed_fake_provider_companies,
            )

            fake = FakeSourceConnector()
            await seed_fake_provider_companies(fake)
            self._provider = fake
        return self._provider

    # ── persistence core ──────────────────────────────────────────────────
    async def _existing(
        self, *, tenant_id: str, row_id: str, capability: str | None = None
    ) -> dict[str, Any] | None:
        cap = capability or self.capability
        tid = _require_uuid(tenant_id, "tenant_id")
        async with self._session_ctx() as db:
            await self._pin(db, tid)
            res = await db.execute(
                text(
                    "SELECT schema_version AS v, "
                    "COALESCE(payload->>'created_at', '') AS created_at "
                    "FROM gtm_capability_results "
                    "WHERE capability = :c AND id = :i"
                ),
                {"c": cap, "i": str(row_id)},
            )
            row = res.first()
        if row is None:
            return None
        return {"schema_version": int(row.v), "created_at": str(row.created_at)}

    async def _save(
        self,
        *,
        tenant_id: str,
        row_id: str,
        name: str,
        payload: dict[str, Any],
        existing: dict[str, Any] | None,
        bump_on_existing: bool = True,
        capability: str | None = None,
    ) -> None:
        cap = capability or self.capability
        tid = _require_uuid(tenant_id, "tenant_id")
        now = datetime.now(UTC)
        version = (
            int(existing["schema_version"]) + 1
            if existing is not None and bump_on_existing
            else int(payload.get("schema_version") or 1)
        )
        payload["schema_version"] = version
        if existing is not None:
            # Recompute produces a brand-new in-memory record with a fresh
            # created_at; the durable row is authoritative for creation time
            # (and the tests assert the original created_at survives a
            # recompute, with only schema_version/updated_at moving).
            original_created = str(existing.get("created_at") or "")
            if original_created:
                payload["created_at"] = original_created
            payload["updated_at"] = now.isoformat()
        async with self._session_ctx() as db:
            await self._pin(db, tid)
            if existing is not None:
                await db.execute(
                    text(
                        "UPDATE gtm_capability_results SET name = :n, "
                        "payload = CAST(:p AS jsonb), schema_version = :v, "
                        "updated_at = :u "
                        "WHERE capability = :c AND id = :i"
                    ),
                    {
                        "n": name,
                        "p": json.dumps(payload),
                        "v": version,
                        "u": now,
                        "c": cap,
                        "i": str(row_id),
                    },
                )
            else:
                try:
                    await db.execute(
                        text(
                            "INSERT INTO gtm_capability_results "
                            "(capability, id, tenant_id, name, payload, "
                            "schema_version, created_at, updated_at) "
                            "VALUES (:c, :i, CAST(:t AS uuid), :n, "
                            "CAST(:p AS jsonb), :v, :ca, :ua)"
                        ),
                        {
                            "c": cap,
                            "i": str(row_id),
                            "t": tid,
                            "n": name,
                            "p": json.dumps(payload),
                            "v": version,
                            "ca": now,
                            "ua": now,
                        },
                    )
                except IntegrityError:
                    # A row with this (capability, id) exists under another
                    # tenant — RLS hides it, so we surface the same
                    # cross-tenant write-block the in-memory stores raise.
                    await db.rollback()
                    raise PermissionError(
                        f"cross-tenant {cap} write blocked"
                    ) from None
            await db.commit()

    async def _load(
        self, *, tenant_id: str, row_id: str, capability: str | None = None
    ) -> dict[str, Any] | None:
        cap = capability or self.capability
        tid = _require_uuid(tenant_id, "tenant_id")
        async with self._session_ctx() as db:
            await self._pin(db, tid)
            res = await db.execute(
                text(
                    "SELECT payload FROM gtm_capability_results "
                    "WHERE capability = :c AND id = :i"
                ),
                {"c": cap, "i": str(row_id)},
            )
            row = res.first()
        if row is None:
            return None
        return dict(row.payload)

    async def _list(
        self, *, tenant_id: str, capability: str | None = None
    ) -> list[dict[str, Any]]:
        cap = capability or self.capability
        tid = _require_uuid(tenant_id, "tenant_id")
        async with self._session_ctx() as db:
            await self._pin(db, tid)
            res = await db.execute(
                text(
                    "SELECT payload FROM gtm_capability_results "
                    "WHERE capability = :c ORDER BY updated_at DESC"
                ),
                {"c": cap},
            )
            rows = res.all()
        return [dict(r.payload) for r in rows]

    # ── generic reads (all capabilities) ──────────────────────────────────
    async def get(self, row_id: str, *, tenant_id: str) -> DurableRecord | None:
        payload = await self._load(tenant_id=tenant_id, row_id=row_id)
        return DurableRecord(payload) if payload is not None else None

    async def list_for_tenant(self, *, tenant_id: str) -> list[DurableRecord]:
        return [DurableRecord(p) for p in await self._list(tenant_id=tenant_id)]

    # ── CAP-096 market sizing ─────────────────────────────────────────────
    async def compute(
        self,
        *,
        tenant_id: str,
        name: str,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
        snapshot_id: str | None = None,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        nm = (name or "").strip()
        if not nm:
            raise MarketSizingError("name required")

        criteria = normalize_criteria(
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
        )
        result = compute_tam_sam_som(criteria, self._resolve_universe(), tenant_id=tid)
        rid = (snapshot_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
        snap = MarketSizingSnapshot(
            id=rid,
            tenant_id=tid,
            name=nm,
            criteria=criteria,
            tam=result.tam,
            sam=result.sam,
            som=result.som,
            universe_size=result.universe_size,
            dataset_scale_hint=GOVERNMENT_DATASET_SCALE_HINT,
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=_now_iso(),
        )
        payload = snap.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=nm, payload=payload,
            existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-097 lead discovery ────────────────────────────────────────────
    async def discover(
        self,
        *,
        tenant_id: str,
        name: str,
        industries: list[str] | None = None,
        cities: list[str] | None = None,
        employees_min: int | None = None,
        employees_max: int | None = None,
        limit: int | None = None,
        run_id: str | None = None,
        use_provider_fallback: bool = True,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        nm = (name or "").strip()
        if not nm:
            raise LeadDiscoveryError("name required")

        query = normalize_query(
            industries=industries,
            cities=cities,
            employees_min=employees_min,
            employees_max=employees_max,
            limit=limit,
        )
        provider: SourceConnector | None = None
        if use_provider_fallback:
            provider = await self.ensure_default_provider()

        leads, gov_n, prov_n, prov_key = await discover_leads(
            query=query,
            universe=self._resolve_universe(),
            provider=provider,
            tenant_id=tid,
        )
        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
        run = LeadDiscoveryRun(
            id=rid,
            tenant_id=tid,
            name=nm,
            query=query,
            leads=leads,
            government_hit_count=gov_n,
            provider_hit_count=prov_n,
            provider_key=prov_key,
            dataset_scale_hint=GOVERNMENT_DATASET_SCALE_HINT,
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=_now_iso(),
        )
        if not run.government_first_ok:
            raise LeadDiscoveryError("government-first ordering invariant broken")
        payload = run.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=nm, payload=payload,
            existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-098 lookalike accounts ────────────────────────────────────────
    async def run(
        self,
        *,
        tenant_id: str,
        name: str,
        company_name: str,
        industry: str | None = None,
        city: str | None = None,
        employees_count: int | None = None,
        limit: int = 10,
        model_id: str | None = None,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        nm = (name or "").strip()
        if not nm:
            raise LookalikeError("name required")

        seed = normalize_seed(
            company_name=company_name,
            industry=industry,
            city=city,
            employees_count=employees_count,
        )
        hits, won_n, lost_n = rank_lookalikes(
            seed,
            self._resolve_history(),
            tenant_id=tid,
            limit=limit,
        )
        rid = (model_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
        now = _now_iso()
        row = LookalikeModel(
            id=rid,
            tenant_id=tid,
            name=nm,
            seed=seed,
            hits=hits,
            trained_on_won=won_n,
            trained_on_lost=lost_n,
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=existing["created_at"] if existing else now,
            updated_at=now,
        )
        payload = row.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=nm, payload=payload,
            existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-099 enrichment waterfall ──────────────────────────────────────
    async def enrich(
        self,
        *,
        tenant_id: str,
        company_name: str,
        domain: str | None = None,
        external_id: str | None = None,
        known: dict | None = None,
        provider_order: list[str] | None = None,
        run_id: str | None = None,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)

        request = normalize_request(
            company_name=company_name,
            domain=domain,
            external_id=external_id,
            known=known,
            provider_order=provider_order,
        )
        filled, hits, attempted, configured = await run_waterfall(
            request, self._providers
        )
        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
        missing_fields = [f for f in ENRICHABLE_FIELDS if f not in filled]
        result = EnrichmentResult(
            id=rid,
            tenant_id=tid,
            request=request,
            filled=filled,
            hits=hits,
            providers_attempted=attempted,
            providers_configured=configured,
            missing_fields=missing_fields,
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=_now_iso(),
        )
        payload = result.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=str(company_name or "").strip()[:200],
            payload=payload, existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-100 contact verification ──────────────────────────────────────
    def _resolve_connector(self, provider_key: str) -> VerificationConnector:
        if not self._connectors:
            default = MemVerificationConnector(key="fake_verify")
            self._connectors = {default.connector_key: default}
            self._default_connector_key = default.connector_key
        key = (provider_key or "").strip() or getattr(
            self, "_default_connector_key", "fake_verify"
        )
        conn = self._connectors.get(key)
        if conn is None:
            raise VerificationError(f"unknown verification connector: {key}")
        return conn

    async def verify(
        self,
        *,
        tenant_id: str,
        email: str | None = None,
        phone: str | None = None,
        provider_key: str | None = None,
        run_id: str | None = None,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)

        request = normalize_verification_request(
            email=email,
            phone=phone,
            provider_key=provider_key,
        )
        connector = self._resolve_connector(request.provider_key)
        verdicts = await run_verification(request, connector)

        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
        result = VerificationResult(
            id=rid,
            tenant_id=tid,
            request=request,
            verdicts=list(verdicts),
            provider_key=connector.connector_key,
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=_now_iso(),
        )
        name = str(connector.connector_key or "")[:200]
        payload = result.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=name, payload=payload,
            existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-101 website intelligence ──────────────────────────────────────
    def _resolve_analyzer(self, analyzer_key: str) -> WebsiteAnalyzer:
        if not self._analyzers:
            default = FixtureWebsiteAnalyzer(key="fixture_website")
            self._analyzers = {default.analyzer_key: default}
            self._default_analyzer_key = default.analyzer_key
        key = (analyzer_key or "").strip() or getattr(
            self, "_default_analyzer_key", "fixture_website"
        )
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
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)

        request = normalize_website_request(
            url=url,
            company_name=company_name,
            page_snippet=page_snippet,
        )
        analyzer = self._resolve_analyzer(analyzer_key or "")
        summary, signals, prompt = await run_website_intelligence(request, analyzer)

        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
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
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=_now_iso(),
        )
        payload = row.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=str(company_name or url or "")[:200],
            payload=payload, existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-103 AI outreach ───────────────────────────────────────────────
    def _resolve_generator(self, generator_key: str) -> OutreachGenerator:
        if not self._generators:
            default = FixtureOutreachGenerator(key="fixture_outreach")
            self._generators = {default.generator_key: default}
            self._default_generator_key = default.generator_key
        key = (generator_key or "").strip() or getattr(
            self, "_default_generator_key", "fixture_outreach"
        )
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
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)

        request = normalize_outreach_request(
            company_name=company_name,
            contact_name=contact_name,
            contact_title=contact_title,
            channel=channel,
            intent=intent,
            value_prop=value_prop,
            website_summary=website_summary,
            icp_notes=icp_notes,
        )
        generator = self._resolve_generator(generator_key or "")
        subject, body, warnings, prompt = await run_outreach_draft(
            request, generator
        )

        rid = (run_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(tenant_id=tid, row_id=rid)
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
            schema_version=(existing["schema_version"] + 1) if existing else 1,
            created_at=_now_iso(),
            warnings=list(warnings),
        )
        payload = row.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=str(company_name or "")[:200],
            payload=payload, existing=existing,
        )
        return DurableRecord(payload)

    # ── CAP-104 sequencing (definitions + enrollments) ────────────────────
    async def create_definition(
        self,
        *,
        tenant_id: str,
        name: str,
        steps: list[dict] | None,
        definition_id: str | None = None,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        nm = (name or "").strip()
        if not nm:
            raise SequencingError("name required")
        parsed = normalize_steps(steps)
        channels = {s.channel for s in parsed}
        channel_label = next(iter(channels)) if len(channels) == 1 else "multi"
        rid = (definition_id or "").strip() or uuid.uuid4().hex[:12]
        existing = await self._existing(
            tenant_id=tid, row_id=rid, capability=DEFINITION_CAPABILITY
        )
        if existing is not None:
            raise SequencingError("sequence id already exists; use a new id")
        now = _now_iso()
        row = SequenceDefinition(
            id=rid,
            tenant_id=tid,
            name=nm,
            steps=parsed,
            channel=channel_label,
            schema_version=1,
            created_at=now,
            updated_at=now,
        )
        payload = row.as_dict()
        await self._save(
            tenant_id=tid, row_id=rid, name=nm, payload=payload,
            existing=None, capability=DEFINITION_CAPABILITY,
        )
        return DurableRecord(payload)

    async def get_definition(
        self, definition_id: str, *, tenant_id: str
    ) -> DurableRecord | None:
        payload = await self._load(
            tenant_id=tenant_id, row_id=definition_id, capability=DEFINITION_CAPABILITY
        )
        return DurableRecord(payload) if payload is not None else None

    async def list_definitions(self, *, tenant_id: str) -> list[DurableRecord]:
        return [
            DurableRecord(p)
            for p in await self._list(
                tenant_id=tenant_id, capability=DEFINITION_CAPABILITY
            )
        ]

    async def enroll(
        self,
        *,
        tenant_id: str,
        sequence_id: str,
        contact_email: str,
        enrollment_id: str | None = None,
        contact_handles: dict[str, str] | None = None,
    ) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        definition = await self._load(
            tenant_id=tid, row_id=sequence_id, capability=DEFINITION_CAPABILITY
        )
        if definition is None:
            raise KeyError("sequence definition not found")
        now = _now_iso()
        row = build_enrollment(
            _definition_from_payload(definition),
            tenant_id=tid,
            contact_email=contact_email,
            enrollment_id=enrollment_id,
            created_at=now,
            contact_handles=contact_handles,
        )
        existing = await self._existing(
            tenant_id=tid, row_id=row.id, capability=ENROLLMENT_CAPABILITY
        )
        payload = row.as_dict()
        await self._save(
            tenant_id=tid, row_id=row.id, name=f"{row.status} {row.sequence_id}",
            payload=payload, existing=existing, bump_on_existing=False,
            capability=ENROLLMENT_CAPABILITY,
        )
        return DurableRecord(payload)

    async def _load_enrollment(
        self, *, tenant_id: str, enrollment_id: str
    ) -> tuple[SequenceEnrollment, SequenceDefinition]:
        payload = await self._load(
            tenant_id=tenant_id, row_id=enrollment_id, capability=ENROLLMENT_CAPABILITY
        )
        if payload is None:
            raise KeyError("enrollment not found")
        enrollment = _enrollment_from_payload(payload)
        definition = await self._load(
            tenant_id=tenant_id,
            row_id=str(enrollment.sequence_id),
            capability=DEFINITION_CAPABILITY,
        )
        if definition is None:
            raise KeyError("sequence definition not found")
        return enrollment, _definition_from_payload(definition)

    async def _save_enrollment(
        self, *, tenant_id: str, enrollment: SequenceEnrollment
    ) -> dict[str, Any]:
        existing = await self._existing(
            tenant_id=tenant_id, row_id=str(enrollment.id),
            capability=ENROLLMENT_CAPABILITY,
        )
        payload = enrollment.as_dict()
        await self._save(
            tenant_id=tenant_id, row_id=str(enrollment.id),
            name=f"{enrollment.status} {enrollment.sequence_id}",
            payload=payload, existing=existing,
            bump_on_existing=False, capability=ENROLLMENT_CAPABILITY,
        )
        return payload

    async def advance(self, enrollment_id: str, *, tenant_id: str) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        enrollment, definition = await self._load_enrollment(
            tenant_id=tid, enrollment_id=enrollment_id
        )
        updated = await advance_enrollment(
            enrollment,
            definition,
            now_iso=_now_iso(),
            senders=self._senders,
        )
        payload = await self._save_enrollment(tenant_id=tid, enrollment=updated)
        return DurableRecord(payload)

    async def pause(self, enrollment_id: str, *, tenant_id: str) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        enrollment, _ = await self._load_enrollment(
            tenant_id=tid, enrollment_id=enrollment_id
        )
        updated = pause_enrollment(enrollment, now_iso=_now_iso())
        payload = await self._save_enrollment(tenant_id=tid, enrollment=updated)
        return DurableRecord(payload)

    async def resume(self, enrollment_id: str, *, tenant_id: str) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        enrollment, _ = await self._load_enrollment(
            tenant_id=tid, enrollment_id=enrollment_id
        )
        updated = resume_enrollment(enrollment, now_iso=_now_iso())
        payload = await self._save_enrollment(tenant_id=tid, enrollment=updated)
        return DurableRecord(payload)

    async def cancel(self, enrollment_id: str, *, tenant_id: str) -> DurableRecord:
        tid = _demand_tenant(tenant_id)
        enrollment, _ = await self._load_enrollment(
            tenant_id=tid, enrollment_id=enrollment_id
        )
        updated = cancel_enrollment(enrollment, now_iso=_now_iso())
        payload = await self._save_enrollment(tenant_id=tid, enrollment=updated)
        return DurableRecord(payload)

    async def get_enrollment(
        self, enrollment_id: str, *, tenant_id: str
    ) -> DurableRecord | None:
        payload = await self._load(
            tenant_id=tenant_id, row_id=enrollment_id, capability=ENROLLMENT_CAPABILITY
        )
        return DurableRecord(payload) if payload is not None else None

    async def list_enrollments(self, *, tenant_id: str) -> list[DurableRecord]:
        return [
            DurableRecord(p)
            for p in await self._list(
                tenant_id=tenant_id, capability=ENROLLMENT_CAPABILITY
            )
        ]