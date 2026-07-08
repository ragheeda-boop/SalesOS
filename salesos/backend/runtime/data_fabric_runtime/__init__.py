"""Data Fabric Runtime — ingestion pipeline from source to golden record.

Pipeline stages:
   1. Collector — ingest raw records from any source (CSV, API, scraper, webhook)
   2. Normalizer — map source fields to canonical schema per data contract
   3. Validator — validate records against schema rules, reject invalid
   4. Entity Resolution — match by CR number, create/merge golden records
   5. Golden Record — provenance-tracked merged entity
   6. Knowledge Graph — populate Neo4j graph relationships
   7. Search Index — update pgvector embeddings and full-text search
   8. Feature Store — trigger feature recomputation (P0.3)

Each stage emits events, metrics, and audit trail entries.
Failed records go to dead letter queue configurable per-stage.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.company.repositories import CompanyRepository
from app.modules.entity_resolution.models import GoldenRecord
from app.modules.entity_resolution.repositories import DeadLetterRepository, GoldenRecordRepository
from app.modules.entity_resolution.service import EntityResolutionService
from typing import TYPE_CHECKING
from sdk.vector import VectorRecord

if TYPE_CHECKING:
    from domains.search.engine.vector_store import PgVectorStore
from sdk.audit import AuditTrail
from sdk.telemetry import StructuredLogger, get_tracer


class PipelineStage(Enum):
    COLLECTOR = "collector"
    NORMALIZER = "normalizer"
    VALIDATOR = "validator"
    ENTITY_RESOLUTION = "entity_resolution"
    GOLDEN_RECORD = "golden_record"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    SEARCH_INDEX = "search_index"
    FEATURE_STORE = "feature_store"


@dataclass
class PipelineRecord:
    """A record flowing through the data fabric pipeline."""
    source_slug: str
    raw_data: dict
    normalized_data: dict | None = None
    validation_errors: list[str] = field(default_factory=list)
    is_valid: bool = True
    cr_number: str | None = None
    golden_record_id: str | None = None
    company_id: str | None = None
    stage_errors: dict[str, str] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of a pipeline run for one record."""
    record: PipelineRecord
    stages_completed: list[str] = field(default_factory=list)
    stages_failed: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    golden_created: bool = False
    golden_merged: bool = False


class PipelineMetrics:
    """Tracks pipeline execution metrics."""

    def __init__(self):
        self._records_ingested: int = 0
        self._records_valid: int = 0
        self._records_invalid: int = 0
        self._records_golden_created: int = 0
        self._records_golden_merged: int = 0
        self._stage_durations: dict[str, list[float]] = {}
        self._errors_by_stage: dict[str, int] = {}

    def record_ingested(self) -> None:
        self._records_ingested += 1

    def record_valid(self) -> None:
        self._records_valid += 1

    def record_invalid(self) -> None:
        self._records_invalid += 1

    def record_golden_created(self) -> None:
        self._records_golden_created += 1

    def record_golden_merged(self) -> None:
        self._records_golden_merged += 1

    def record_stage_duration(self, stage: str, duration_ms: float) -> None:
        if stage not in self._stage_durations:
            self._stage_durations[stage] = []
        self._stage_durations[stage].append(duration_ms)

    def record_stage_error(self, stage: str) -> None:
        self._errors_by_stage[stage] = self._errors_by_stage.get(stage, 0) + 1

    def snapshot(self) -> dict:
        avg_durations = {
            stage: round(sum(durs) / len(durs), 2) if durs else 0
            for stage, durs in self._stage_durations.items()
        }
        return {
            "records_ingested": self._records_ingested,
            "records_valid": self._records_valid,
            "records_invalid": self._records_invalid,
            "records_golden_created": self._records_golden_created,
            "records_golden_merged": self._records_golden_merged,
            "stage_avg_durations_ms": avg_durations,
            "errors_by_stage": dict(self._errors_by_stage),
            "total_errors": sum(self._errors_by_stage.values()),
            "companies_synced": getattr(self, "_companies_synced", 0),
            "embeddings_stored": getattr(self, "_embeddings_stored", 0),
            "kg_triples_created": getattr(self, "_kg_triples_created", 0),
            "features_computed": getattr(self, "_features_computed", 0),
        }


class Normalizer:
    """Normalizes source fields to canonical schema per data contract.

    Each source (balady, taqeem, ncnp, najiz, rega, socpa) has a
    field mapping registered at startup.
    """

    def __init__(self):
        self._mappings: dict[str, dict[str, str]] = {}

    def register_mapping(self, source_slug: str, field_map: dict[str, str]) -> None:
        """Register a source→canonical field mapping.

        Args:
            source_slug: e.g., 'balady', 'taqeem'
            field_map: {source_field: canonical_field}
        """
        self._mappings[source_slug.lower()] = field_map

    def normalize(self, source_slug: str, record: dict) -> dict:
        """Normalize a record's fields to canonical names.

        Unknown fields are passed through unchanged.
        """
        mapping = self._mappings.get(source_slug.lower(), {})
        normalized = {}
        for key, value in record.items():
            canonical = mapping.get(key, key)
            normalized[canonical] = value
        return normalized


class Validator:
    """Validates records against schema rules."""

    def __init__(self):
        self._rules: dict[str, list[Callable[[dict], str | None]]] = {}

    def register_rules(self, source_slug: str, rules: list[Callable[[dict], str | None]]) -> None:
        self._rules[source_slug.lower()] = rules

    def validate(self, source_slug: str, record: dict) -> list[str]:
        errors = []
        rules = self._rules.get(source_slug.lower(), [])

        # Built-in required field check
        cr_number = record.get("cr_number") or record.get("CR_number")
        if not cr_number:
            errors.append("Missing cr_number")

        name_ar = record.get("name_ar") or record.get("company_name") or record.get("company_name_ar")
        if not name_ar:
            errors.append("Missing company name (name_ar)")

        for rule in rules:
            try:
                error = rule(record)
                if error:
                    errors.append(error)
            except Exception as e:
                errors.append(f"Rule error: {e}")

        return errors


class DataFabricPipeline:
    """Orchestrates the full data ingestion pipeline.

    Usage:
        pipeline = DataFabricPipeline(session_factory, logger)
        result = await pipeline.run("balady", records)
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_runtime=None,
        feature_store=None,
        vector_store: PgVectorStore | None = None,
        embedding_service=None,
        kg_engine=None,
        logger: StructuredLogger | None = None,
    ):
        self._session_factory = session_factory
        self._event_runtime = event_runtime
        self._feature_store = feature_store
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._kg_engine = kg_engine
        self._logger = logger
        self._tracer = get_tracer("data_fabric_runtime")

        # Pipeline components
        self.normalizer = Normalizer()
        self._register_default_mappings()
        self.validator = Validator()
        self._register_default_validators()

        # Metrics
        self.metrics = PipelineMetrics()

    def _register_default_mappings(self) -> None:
        """Register canonical field mappings for all known sources."""
        self.normalizer.register_mapping("balady", {
            "company_name_ar": "name_ar",
            "company_name_en": "name_en",
            "cr_number": "cr_number",
            "city_ar": "city",
            "city_en": "city",
            "postal_code": "postal_code",
            "activity": "activity_description",
            "license_status": "status",
            "issue_date": "incorporation_date",
            "expiry_date": "expiry_date",
            "owner_name": "__owner_name",
            "owner_nationality": "__owner_nationality",
        })
        self.normalizer.register_mapping("taqeem", {
            "company_name": "name_ar",
            "company_name_ar": "name_ar",
            "company_name_en": "name_en",
            "cr_number": "cr_number",
            "city_ar": "city",
            "city_en": "city",
            "employee_count": "employees_count",
            "employees_count": "employees_count",
            "capital": "capital",
            "status": "status",
            "establishment_date": "incorporation_date",
            "incorporation_date": "incorporation_date",
        })
        self.normalizer.register_mapping("ncnp", {
            "establishment_name": "name_ar",
            "cr": "cr_number",
            "cr_number": "cr_number",
            "city_ar": "city",
            "city_en": "city",
            "employees_total": "employees_count",
        })
        self.normalizer.register_mapping("rega", {
            "company_name": "name_ar",
            "company_name_ar": "name_ar",
            "cr_number": "cr_number",
            "license_type": "cr_type",
            "license_status": "status",
            "city_ar": "city",
            "city_en": "city",
        })
        self.normalizer.register_mapping("najiz", {
            "case_number": "__case_number",
            "case_type": "__case_type",
            "court": "__court",
            "status": "__case_status",
        })

    def _register_default_validators(self) -> None:
        """Register validation rules for all known sources."""

        def cr_number_format(record: dict) -> str | None:
            cr = record.get("cr_number") or record.get("CR_number") or ""
            if cr and (not isinstance(cr, str) or len(cr) < 5):
                return f"Invalid cr_number format: {cr}"
            return None

        def name_not_empty(record: dict) -> str | None:
            name = record.get("name_ar") or record.get("company_name") or ""
            if not name or not isinstance(name, str) or len(name.strip()) < 1:
                return "Company name must be non-empty string"
            return None

        for src in ("balady", "taqeem", "ncnp", "rega"):
            self.validator.register_rules(src, [cr_number_format, name_not_empty])

    async def run_batch(
        self,
        source_slug: str,
        records: list[dict],
        tenant_id: str,
    ) -> dict:
        """Run the full data fabric pipeline on a batch of records.

        Pipeline: Collector → Normalizer → Validator → Entity Resolution
                 → Golden Record → Knowledge Graph → Search Index → Feature Store

        Returns:
            dict with summary: processed, valid, invalid, golden_created, golden_merged, errors
        """
        start_time = time.time()
        results: list[PipelineResult] = []
        total_valid = 0
        total_invalid = 0
        total_golden_created = 0
        total_golden_merged = 0
        errors: list[dict] = []

        for i, record in enumerate(records):
            pipeline_record = PipelineRecord(source_slug=source_slug, raw_data=record)
            result = PipelineResult(record=pipeline_record)

            with self._tracer.start_as_current_span("data_fabric.record") as span:
                span.set_attribute("record.index", i)
                span.set_attribute("source", source_slug)

                try:
                    # Stage 1: Normalizer
                    stage_start = time.monotonic()
                    try:
                        normalized = self.normalizer.normalize(source_slug, record)
                    except Exception as ne:
                        await self._dlq(tenant_id, source_slug, "normalizer", record, ne)
                        raise
                    pipeline_record.normalized_data = normalized
                    result.stages_completed.append("normalizer")
                    dur = (time.monotonic() - stage_start) * 1000
                    self.metrics.record_stage_duration("normalizer", dur)

                    # Stage 2: Validator
                    stage_start = time.monotonic()
                    try:
                        validation_errors = self.validator.validate(source_slug, normalized)
                    except Exception as ve:
                        await self._dlq(tenant_id, source_slug, "validator", normalized, ve)
                        raise
                    pipeline_record.validation_errors = validation_errors
                    pipeline_record.is_valid = len(validation_errors) == 0
                    result.stages_completed.append("validator")
                    dur = (time.monotonic() - stage_start) * 1000
                    self.metrics.record_stage_duration("validator", dur)

                    if not pipeline_record.is_valid:
                        total_invalid += 1
                        self.metrics.record_invalid()
                        result.stages_failed.append("validator")
                        errors.append({
                            "index": i,
                            "stage": "validator",
                            "cr_number": normalized.get("cr_number"),
                            "errors": validation_errors,
                        })
                        results.append(result)
                        continue
                    else:
                        total_valid += 1
                        self.metrics.record_valid()

                    # Stage 3: Entity Resolution
                    cr_number = normalized.get("cr_number") or normalized.get("CR_number")
                    pipeline_record.cr_number = cr_number
                    result.stages_completed.append("entity_resolution")

                except Exception as e:
                    error_msg = str(e)
                    pipeline_record.stage_errors["pipeline"] = error_msg
                    result.stages_failed.append("pipeline")
                    errors.append({"index": i, "stage": error_msg, "error": error_msg})
                    if self._logger:
                        self._logger.error("data_fabric.record_error", index=i, error=error_msg)

                results.append(result)

        total_processed = len(records)
        duration = time.time() - start_time

        # Now run entity resolution for all valid records in one batch
        valid_records = [
            r.record.normalized_data
            for r in results
            if r.record.is_valid and r.record.normalized_data
        ]

        if valid_records:
            try:
                async with self._session_factory() as session:
                    resolution = EntityResolutionService(
                        db=session,
                        event_bus=self._event_runtime,
                        logger=self._logger,
                    )
                    resolution_result = await resolution.resolve_records(
                        tenant_id=tenant_id,
                        source_slug=source_slug,
                        records=valid_records,
                    )
                    total_golden_created = resolution_result["records_created"]
                    total_golden_merged = resolution_result["records_merged"]
                    for _ in range(total_golden_created):
                        self.metrics.record_golden_created()
                    for _ in range(total_golden_merged):
                        self.metrics.record_golden_merged()

                    # Stage 5: Sync golden records → companies table
                    company_repo = CompanyRepository(session)
                    golden_repo = GoldenRecordRepository(session)
                    companies_created = 0
                    companies_updated = 0
                    for rec in valid_records:
                        cr_number = rec.get("cr_number") or rec.get("CR_number")
                        if not cr_number:
                            continue
                        golden = await golden_repo.get_by_cr_number(uuid.UUID(tenant_id), cr_number)
                        if not golden:
                            continue

                        # Stage 5a: Company sync
                        try:
                            company_id = await self._sync_golden_to_company(
                                session, company_repo, golden, tenant_id,
                            )
                        except Exception as ce:
                            await self._send_to_dlq(session, tenant_id, source_slug, "company_sync", rec, ce, cr_number)
                            continue

                        if golden.company_id is None:
                            golden.company_id = company_id
                            companies_created += 1
                        else:
                            companies_updated += 1
                        self.metrics._companies_synced = getattr(self.metrics, "_companies_synced", 0) + 1

                        # Stage 6: Compute embedding + store in companies.embedding + vectors table
                        try:
                            await self._compute_and_store_embedding(
                                session, company_id, golden, tenant_id,
                            )
                            self.metrics._embeddings_stored = getattr(self.metrics, "_embeddings_stored", 0) + 1
                        except Exception as ee:
                            await self._send_to_dlq(session, tenant_id, source_slug, "embedding", rec, ee, cr_number)

                        # Stage 7: Knowledge Graph — populate Neo4j
                        if self._kg_engine:
                            try:
                                golden_dict = {
                                    "id": str(golden.id),
                                    "company_id": str(company_id),
                                    "cr_number": golden.cr_number,
                                    "data": golden.data,
                                    "tenant_id": tenant_id,
                                }
                                await self._kg_engine.populate_from_golden_record(
                                    golden_dict, tenant_id,
                                )
                                self.metrics._kg_triples_created = getattr(self.metrics, "_kg_triples_created", 0) + 1
                            except Exception as ke:
                                await self._send_to_dlq(session, tenant_id, source_slug, "knowledge_graph", rec, ke, cr_number)

                    await session.commit()

                    # Stage 8: Feature store recompute (separate session to avoid long tx)
                    if self._feature_store and companies_created > 0:
                        try:
                            cr_list = [r.get("cr_number") or r.get("CR_number") for r in valid_records if r.get("cr_number") or r.get("CR_number")]
                            async with self._session_factory():
                                for cr in cr_list:
                                    gr = await golden_repo.get_by_cr_number(uuid.UUID(tenant_id), cr)
                                    if gr and gr.company_id:
                                        await self._feature_store.recompute(
                                            company_id=str(gr.company_id),
                                            tenant_id=tenant_id,
                                        )
                                        self.metrics._features_computed = getattr(self.metrics, "_features_computed", 0) + 1
                        except Exception as fe:
                            if self._logger:
                                self._logger.error("data_fabric.feature_store_error", error=str(fe))
                            errors.append({"stage": "feature_store", "error": str(fe)})

            except Exception as e:
                if self._logger:
                    self._logger.error("data_fabric.entity_resolution_error", error=str(e))
                errors.append({"stage": "entity_resolution", "error": str(e)})

        self.metrics._records_ingested = total_processed

        # Audit trail
        try:
            async with self._session_factory() as session:
                audit = AuditTrail(session)
                await audit.record(
                    tenant_id=tenant_id,
                    entity_type="data_fabric",
                    entity_id="",
                    action="pipeline_run",
                    changes={
                        "source": source_slug,
                        "records_processed": total_processed,
                        "records_valid": total_valid,
                        "records_invalid": total_invalid,
                        "golden_created": total_golden_created,
                        "golden_merged": total_golden_merged,
                        "errors": len(errors),
                        "duration_seconds": round(duration, 3),
                    },
                )
                await session.commit()
        except Exception:
            pass

        return {
            "source": source_slug,
            "records_processed": total_processed,
            "records_valid": total_valid,
            "records_invalid": total_invalid,
            "golden_records_created": total_golden_created,
            "golden_records_merged": total_golden_merged,
            "errors": errors,
            "duration_seconds": round(duration, 3),
        }

    async def _sync_golden_to_company(
        self,
        session: AsyncSession,
        company_repo: CompanyRepository,
        golden: GoldenRecord,
        tenant_id: str,
    ) -> uuid.UUID:
        """Create or update a Company record from a golden record.

        Returns the company UUID.
        """
        from app.modules.company.models import Company
        from sqlalchemy import select

        data = golden.data or {}
        company_id = golden.company_id

        if company_id:
            stmt = select(Company).where(Company.id == company_id)
            result = await session.execute(stmt)
            company = result.scalar_one_or_none()
            if company:
                self._apply_golden_data(company, data, golden)
                return company.id

        stmt = select(Company).where(
            Company.tenant_id == uuid.UUID(tenant_id),
            Company.cr_number == golden.cr_number,
        )
        result = await session.execute(stmt)
        company = result.scalar_one_or_none()

        if company:
            self._apply_golden_data(company, data, golden)
            golden.company_id = company.id
            return company.id

        company = Company(
            tenant_id=uuid.UUID(tenant_id),
            cr_number=golden.cr_number,
            name_ar=data.get("name_ar", {}).get("value", ""),
            name_en=data.get("name_en", {}).get("value", None),
            city=data.get("city", {}).get("value", None),
            region=data.get("region", {}).get("value", None),
            status=data.get("status", {}).get("value", "active"),
            activity_description=data.get("activity_description", {}).get("value", None),
            phone=data.get("phone", {}).get("value", None),
            email=data.get("email", {}).get("value", None),
            website=data.get("website", {}).get("value", None),
            capital=data.get("capital", {}).get("value", None),
            employees_count=data.get("employees_count", {}).get("value", None),
            is_golden_record=True,
            confidence_score=golden.confidence_score or 0.0,
            source_ids=golden.source_ids or [],
        )
        session.add(company)
        await session.flush()
        golden.company_id = company.id
        return company.id

    def _apply_golden_data(self, company, data: dict, golden: GoldenRecord) -> None:
        """Apply golden record data to an existing Company record."""
        field_map = {
            "name_ar": "name_ar",
            "name_en": "name_en",
            "city": "city",
            "region": "region",
            "status": "status",
            "activity_description": "activity_description",
            "phone": "phone",
            "email": "email",
            "website": "website",
            "capital": "capital",
            "employees_count": "employees_count",
            "industry": "industry",
        }
        for gr_field, company_field in field_map.items():
            entry = data.get(gr_field)
            if entry and entry.get("value") is not None:
                setattr(company, company_field, entry["value"])
        company.is_golden_record = True
        company.confidence_score = golden.confidence_score or 0.0
        company.source_ids = golden.source_ids or []

    async def _compute_and_store_embedding(
        self,
        session: AsyncSession,
        company_id: uuid.UUID,
        golden: GoldenRecord,
        tenant_id: str,
    ) -> None:
        """Compute embedding for a company and store in companies.embedding + vectors table."""
        from sqlalchemy import text

        text_to_embed = " ".join(filter(None, [
            golden.data.get("name_ar", {}).get("value", ""),
            golden.data.get("name_en", {}).get("value", ""),
            golden.data.get("activity_description", {}).get("value", ""),
            golden.data.get("city", {}).get("value", ""),
            golden.data.get("industry", {}).get("value", ""),
        ]))
        if not text_to_embed.strip():
            return

        if self._embedding_service:
            try:
                embedding = await self._embedding_service.embed(text_to_embed)
                await session.execute(
                    text("UPDATE companies SET embedding = :emb WHERE id = :cid"),
                    {"emb": embedding, "cid": company_id},
                )
                if self._vector_store:
                    await self._vector_store.upsert(VectorRecord(
                        id=str(company_id),
                        vector=embedding,
                        metadata={
                            "name_ar": golden.data.get("name_ar", {}).get("value"),
                            "name_en": golden.data.get("name_en", {}).get("value"),
                            "cr_number": golden.cr_number,
                            "tenant_id": tenant_id,
                        },
                    ))
            except Exception as e:
                if self._logger:
                    self._logger.warning("data_fabric.embedding_error", company_id=str(company_id), error=str(e))

    async def _send_to_dlq(
        self,
        session: AsyncSession,
        tenant_id: str,
        source_slug: str,
        stage: str,
        record_data: dict,
        error: Exception,
        cr_number: str | None = None,
    ) -> None:
        """Send a failed record to the dead letter queue."""
        try:
            repo = DeadLetterRepository(session)
            await repo.add(
                tenant_id=tenant_id,
                source_slug=source_slug,
                stage=stage,
                record_data=record_data,
                error_message=str(error),
                error_type=type(error).__name__,
                cr_number=cr_number,
            )
            self.metrics.record_stage_error(stage)
        except Exception as dlq_err:
            if self._logger:
                self._logger.error("data_fabric.dlq_error", stage=stage, error=str(dlq_err))

    async def _dlq(
        self,
        tenant_id: str,
        source_slug: str,
        stage: str,
        record_data: dict,
        error: Exception,
    ) -> None:
        """Standalone DLQ writer — opens its own session."""
        try:
            async with self._session_factory() as s:
                repo = DeadLetterRepository(s)
                await repo.add(
                    tenant_id=tenant_id,
                    source_slug=source_slug,
                    stage=stage,
                    record_data=record_data,
                    error_message=str(error),
                    error_type=type(error).__name__,
                    cr_number=record_data.get("cr_number"),
                )
                await s.commit()
                self.metrics.record_stage_error(stage)
        except Exception as dlq_err:
            if self._logger:
                self._logger.error("data_fabric.dlq_error", stage=stage, error=str(dlq_err))

    async def retry_dlq(self, tenant_id: str, limit: int = 50) -> dict:
        """Retry failed records from the dead letter queue."""
        async with self._session_factory() as session:
            repo = DeadLetterRepository(session)
            pending = await repo.get_pending_retries(tenant_id, limit=limit)

            retried = 0
            resolved = 0
            still_failed = 0

            for entry in pending:
                try:
                    normalized = self.normalizer.normalize(entry.source_slug, entry.record_data)
                    validation_errors = self.validator.validate(entry.source_slug, normalized)
                    if validation_errors:
                        await repo.mark_failed(entry.id, f"Validation: {', '.join(validation_errors)}")
                        still_failed += 1
                        continue

                    async with self._session_factory() as inner_session:
                        resolution = EntityResolutionService(
                            db=inner_session,
                            event_bus=self._event_runtime,
                            logger=self._logger,
                        )
                        result = await resolution.resolve_records(
                            tenant_id=tenant_id,
                            source_slug=entry.source_slug,
                            records=[normalized],
                        )
                        if result.get("errors"):
                            await repo.mark_failed(entry.id, str(result["errors"][0]))
                            still_failed += 1
                        else:
                            await repo.mark_resolved(entry.id)
                            resolved += 1

                    await repo.mark_retried(entry.id)
                    retried += 1

                except Exception as e:
                    await repo.mark_failed(entry.id, str(e))
                    still_failed += 1

            await session.commit()

        return {
            "processed": len(pending),
            "retried": retried,
            "resolved": resolved,
            "still_failed": still_failed,
        }

    async def run_single(
        self,
        source_slug: str,
        record: dict,
        tenant_id: str,
    ) -> PipelineResult:
        """Run the pipeline on a single record."""
        result_dict = await self.run_batch(source_slug, [record], tenant_id)
        return result_dict
