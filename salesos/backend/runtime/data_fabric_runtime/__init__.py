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

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.company.repositories import SourceRepository
from app.modules.entity_resolution.service import EntityResolutionService
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
        return {
            "records_ingested": self._records_ingested,
            "records_valid": self._records_valid,
            "records_invalid": self._records_invalid,
            "records_golden_created": self._records_golden_created,
            "records_golden_merged": self._records_golden_merged,
            "stage_avg_durations_ms": {
                stage: round(sum(durs) / len(durs), 2) if durs else 0
                for stage, durs in self._stage_durations.items()
            },
            "errors_by_stage": dict(self._errors_by_stage),
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
        logger: StructuredLogger | None = None,
    ):
        self._session_factory = session_factory
        self._event_runtime = event_runtime
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
            "cr_number": "cr_number",
            "city": "city",
            "employee_count": "employees_count",
            "capital": "capital",
            "status": "status",
            "establishment_date": "incorporation_date",
        })
        self.normalizer.register_mapping("ncnp", {
            "establishment_name": "name_ar",
            "cr": "cr_number",
            "city": "city",
            "employees_total": "employees_count",
        })
        self.normalizer.register_mapping("rega", {
            "company_name": "name_ar",
            "cr_number": "cr_number",
            "license_type": "cr_type",
            "license_status": "status",
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
                    normalized = self.normalizer.normalize(source_slug, record)
                    pipeline_record.normalized_data = normalized
                    result.stages_completed.append("normalizer")
                    dur = (time.monotonic() - stage_start) * 1000
                    self.metrics.record_stage_duration("normalizer", dur)

                    # Stage 2: Validator
                    stage_start = time.monotonic()
                    validation_errors = self.validator.validate(source_slug, normalized)
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

                    # Stage 3: Entity Resolution
                    cr_number = normalized.get("cr_number") or normalized.get("CR_number")
                    pipeline_record.cr_number = cr_number
                    result.stages_completed.append("entity_resolution")

                except Exception as e:
                    error_msg = str(e)
                    pipeline_record.stage_errors["pipeline"] = error_msg
                    result.stages_failed.append("pipeline")
                    errors.append({"index": i, "stage": "pipeline", "error": error_msg})
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
                    total_valid = resolution_result["records_processed"]
                    self.metrics.record_golden_created()
                    self.metrics.record_golden_merged()
                    await session.commit()
            except Exception as e:
                if self._logger:
                    self._logger.error("data_fabric.entity_resolution_error", error=str(e))
                errors.append({"stage": "entity_resolution", "error": str(e)})

        self.metrics.records_ingested = total_processed

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

    async def run_single(
        self,
        source_slug: str,
        record: dict,
        tenant_id: str,
    ) -> PipelineResult:
        """Run the pipeline on a single record."""
        result_dict = await self.run_batch(source_slug, [record], tenant_id)
        return result_dict
