"""Entity Resolution Service — orchestrates golden record creation, matching, and conflict detection.

The pipeline flow:
1. Receive records from a source (e.g., Balady scraper)
2. Match by CR number against existing companies and golden records
3. For new CR numbers: create golden record with provenance
4. For existing CR numbers: detect field-level conflicts, apply highest-priority source rule
5. Log conflicts when automatic resolution is not possible
6. Publish EntityResolutionMatchFound / GoldenRecordCreated / GoldenRecordUpdated events
7. Update company confidence_score based on gold record state
"""

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from sdk.audit import AuditTrail
from sdk.events import EventBus
from sdk.events.domain_events import (
    EntityResolutionCompleted,
    EntityResolutionMatchFound,
    GoldenRecordCreated,
    GoldenRecordUpdated,
)
from sdk.telemetry import StructuredLogger

from ..company.repositories import CompanyRepository
from .models import EntityResolutionConflict, EntityResolutionLog, GoldenRecord
from .repositories import ConflictRepository, GoldenRecordRepository

# Source priority for automatic conflict resolution
SOURCE_PRIORITY: dict[str, int] = {
    "balady": 100,
    "ncnp": 90,
    "taqeem": 80,
    "rega": 70,
    "najiz": 60,
    "socpa": 50,
    "apollo": 40,
    "hubspot": 30,
}


class EntityResolutionService:
    """Orchestrates identity resolution across data sources."""

    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
    ):
        self.db = db
        self.event_bus = event_bus
        self.logger = logger
        self.golden_repo = GoldenRecordRepository(db)
        self.conflict_repo = ConflictRepository(db)
        self.company_repo = CompanyRepository(db)

    async def resolve_records(
        self,
        tenant_id: str,
        source_slug: str,
        records: list[dict],
        confidence_threshold: float = 0.7,
    ) -> dict:
        """Process a batch of records from a source through entity resolution.

        Args:
            tenant_id: Tenant UUID
            source_slug: Source identifier (e.g., 'balady', 'taqeem')
            records: List of record dicts (must contain 'cr_number')
            confidence_threshold: Minimum confidence for auto-merge

        Returns:
            Summary dict with counts of processed/matched/created/merged records
        """
        start_time = time.time()
        tenant_uuid = uuid.UUID(tenant_id)

        processed = 0
        matched = 0
        created = 0
        merged = 0
        conflicts = 0
        errors = []

        for record in records:
            cr_number = record.get("cr_number") or record.get("CR_number")
            if not cr_number:
                errors.append({"record": record, "error": "Missing cr_number"})
                continue

            processed += 1

            try:
                existing_golden = await self.golden_repo.get_by_cr_number(
                    tenant_uuid, cr_number
                )

                if existing_golden:
                    matched += 1
                    result = await self._merge_into_golden(
                        existing_golden, source_slug, record, tenant_id
                    )
                    if result.get("merged"):
                        merged += 1
                    if result.get("conflicts"):
                        conflicts += result["conflicts"]
                else:
                    await self._create_golden_record(
                        tenant_id, cr_number, source_slug, record
                    )
                    created += 1

            except Exception as e:
                errors.append({"cr_number": cr_number, "error": str(e)})
                if self.logger:
                    self.logger.error("entity_resolution.record_error",
                                      cr_number=cr_number, error=str(e))

        duration = time.time() - start_time

        log_entry = EntityResolutionLog(
            tenant_id=tenant_uuid,
            operation="resolve_batch",
            source_slug=source_slug,
            records_processed=processed,
            records_matched=matched,
            records_created=created,
            records_merged=merged,
            confidence_threshold=confidence_threshold,
            details={
                "conflicts_detected": conflicts,
                "errors": len(errors),
                "duration_seconds": round(duration, 3),
            },
        )
        self.db.add(log_entry)
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=tenant_id,
            entity_type="entity_resolution",
            entity_id="",
            action="batch_resolved",
            changes={
                "source": source_slug,
                "processed": processed,
                "matched": matched,
                "created": created,
                "merged": merged,
                "conflicts": conflicts,
                "errors": len(errors),
            },
        )

        if self.event_bus:
            await self.event_bus.publish(
                EntityResolutionCompleted(
                    tenant_id=tenant_id,
                    aggregate_id="",
                    aggregate_type="entity_resolution",
                    data={
                        "source": source_slug,
                        "processed": processed,
                        "matched": matched,
                        "created": created,
                        "merged": merged,
                        "conflicts": conflicts,
                        "duration_seconds": round(duration, 3),
                    },
                )
            )

        return {
            "source": source_slug,
            "records_processed": processed,
            "records_matched": matched,
            "records_created": created,
            "records_merged": merged,
            "conflicts_detected": conflicts,
            "errors": errors,
            "duration_seconds": round(duration, 3),
        }

    async def _create_golden_record(
        self,
        tenant_id: str,
        cr_number: str,
        source_slug: str,
        record: dict,
    ) -> GoldenRecord:
        """Create a new golden record from a source record."""
        tenant_uuid = uuid.UUID(tenant_id)
        now = datetime.now(timezone.utc)

        data: dict = {}
        for field, value in record.items():
            if value is not None and not field.startswith("_"):
                data[field] = {
                    "value": value,
                    "source": source_slug.upper(),
                    "confidence": self._compute_field_confidence(field, source_slug),
                    "timestamp": now.isoformat(),
                    "verified_by": None,
                }

        golden = GoldenRecord(
            tenant_id=tenant_uuid,
            cr_number=cr_number,
            data=data,
            confidence_score=self._compute_overall_confidence(data),
            source_ids=[source_slug],
            is_active=True,
        )
        self.db.add(golden)
        await self.db.flush()

        if self.event_bus:
            await self.event_bus.publish(
                GoldenRecordCreated(
                    tenant_id=tenant_id,
                    aggregate_id=str(golden.id),
                    aggregate_type="golden_record",
                    data={
                        "cr_number": cr_number,
                        "source": source_slug,
                        "confidence": golden.confidence_score,
                    },
                )
            )

        return golden

    async def _merge_into_golden(
        self,
        golden: GoldenRecord,
        source_slug: str,
        record: dict,
        tenant_id: str,
    ) -> dict:
        """Merge a source record into an existing golden record.

        Returns dict with 'merged' (bool) and 'conflicts' (int).
        """
        merged = False
        conflict_count = 0
        now = datetime.now(timezone.utc)
        incoming_priority = SOURCE_PRIORITY.get(source_slug, 0)

        for field, value in record.items():
            if value is None or field.startswith("_"):
                continue

            existing = golden.data.get(field)

            if existing is None:
                golden.data = {
                    **golden.data,
                    field: {
                        "value": value,
                        "source": source_slug.upper(),
                        "confidence": self._compute_field_confidence(field, source_slug),
                        "timestamp": now.isoformat(),
                        "verified_by": None,
                    },
                }
                merged = True
            else:
                existing_priority = SOURCE_PRIORITY.get(existing.get("source", "").lower(), 0)

                if existing["value"] != value:
                    if incoming_priority > existing_priority:
                        conflict_count += 1
                        await self._record_conflict(
                            golden, field, existing, source_slug, value, tenant_id
                        )
                        golden.data = {
                            **golden.data,
                            field: {
                                "value": value,
                                "source": source_slug.upper(),
                                "confidence": self._compute_field_confidence(field, source_slug),
                                "timestamp": now.isoformat(),
                                "verified_by": None,
                            },
                        }
                        merged = True
                    elif incoming_priority < existing_priority:
                        conflict_count += 1
                        await self._record_conflict(
                            golden, field, existing, source_slug, value, tenant_id
                        )
                    else:
                        conflict_count += 1
                        await self._record_conflict(
                            golden, field, existing, source_slug, value, tenant_id
                        )

        if merged:
            golden.confidence_score = self._compute_overall_confidence(golden.data)
            if source_slug not in (golden.source_ids or []):
                if golden.source_ids:
                    golden.source_ids.append(source_slug)
                else:
                    golden.source_ids = [source_slug]
            golden.updated_at = now
            await self.db.flush()

            if self.event_bus:
                await self.event_bus.publish(
                    GoldenRecordUpdated(
                        tenant_id=tenant_id,
                        aggregate_id=str(golden.id),
                        aggregate_type="golden_record",
                        data={
                            "cr_number": golden.cr_number,
                            "source": source_slug,
                            "confidence": golden.confidence_score,
                            "conflicts": conflict_count,
                        },
                    )
                )

        return {"merged": merged, "conflicts": conflict_count}

    async def _record_conflict(
        self,
        golden: GoldenRecord,
        field: str,
        existing: dict,
        incoming_source: str,
        incoming_value: str,
        tenant_id: str,
    ) -> None:
        """Record a field-level conflict for human review."""
        conflict = EntityResolutionConflict(
            tenant_id=golden.tenant_id,
            golden_record_id=golden.id,
            field_name=field,
            source_a_value=str(existing.get("value", "")),
            source_a_source=existing.get("source", "unknown"),
            source_b_value=str(incoming_value),
            source_b_source=incoming_source.upper(),
            status="open",
        )
        self.db.add(conflict)

        if self.event_bus:
            await self.event_bus.publish(
                EntityResolutionMatchFound(
                    tenant_id=tenant_id,
                    aggregate_id=str(golden.id),
                    aggregate_type="entity_resolution",
                    data={
                        "field": field,
                        "cr_number": golden.cr_number,
                        "source_a": existing.get("source"),
                        "source_b": incoming_source.upper(),
                        "value_a": str(existing.get("value", "")),
                        "value_b": str(incoming_value),
                    },
                )
            )

    async def resolve_conflict(
        self,
        conflict_id: str,
        strategy: str,
        custom_value: str | None = None,
        resolved_by: str | None = None,
    ) -> EntityResolutionConflict:
        """Manually resolve a field-level conflict."""
        conflict = await self.conflict_repo.get(uuid.UUID(conflict_id))

        if strategy == "use_source_a":
            pass
        elif strategy == "use_source_b":
            golden = await self.golden_repo.get(conflict.golden_record_id)
            if conflict.field_name in golden.data:
                golden.data = {
                    **golden.data,
                    conflict.field_name: {
                        **golden.data[conflict.field_name],
                        "value": conflict.source_b_value,
                        "source": conflict.source_b_source,
                        "verified_by": resolved_by,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
                golden.confidence_score = self._compute_overall_confidence(golden.data)
        elif strategy == "merge" and custom_value:
            golden = await self.golden_repo.get(conflict.golden_record_id)
            if conflict.field_name in golden.data:
                golden.data = {
                    **golden.data,
                    conflict.field_name: {
                        **golden.data[conflict.field_name],
                        "value": custom_value,
                        "source": "manual_merge",
                        "verified_by": resolved_by,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
                golden.confidence_score = self._compute_overall_confidence(golden.data)
        elif strategy == "custom" and custom_value:
            golden = await self.golden_repo.get(conflict.golden_record_id)
            if conflict.field_name in golden.data:
                golden.data = {
                    **golden.data,
                    conflict.field_name: {
                        **golden.data[conflict.field_name],
                        "value": custom_value,
                        "source": "manual_custom",
                        "verified_by": resolved_by,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
                golden.confidence_score = self._compute_overall_confidence(golden.data)

        conflict.resolution_strategy = strategy
        conflict.resolved_by = uuid.UUID(resolved_by) if resolved_by else None
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.status = "resolved"
        await self.db.flush()

        return conflict

    async def get_golden_record(self, golden_record_id: str) -> GoldenRecord:
        return await self.golden_repo.get(uuid.UUID(golden_record_id))

    async def get_golden_by_cr(self, tenant_id: str, cr_number: str) -> GoldenRecord | None:
        return await self.golden_repo.get_by_cr_number(uuid.UUID(tenant_id), cr_number)

    async def list_golden_records(
        self, tenant_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[GoldenRecord], int]:
        return await self.golden_repo.find_by_tenant(
            uuid.UUID(tenant_id), page=page, page_size=page_size
        )

    async def list_conflicts(
        self, tenant_id: str, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[list[EntityResolutionConflict], int]:
        return await self.conflict_repo.find_by_tenant(
            uuid.UUID(tenant_id), status=status, page=page, page_size=page_size
        )

    async def get_stats(self, tenant_id: str) -> dict:
        tenant_uuid = uuid.UUID(tenant_id)
        total_golden = await self.golden_repo.count_by_tenant(tenant_uuid)
        open_conflicts = await self.conflict_repo.count_open(tenant_uuid)
        return {
            "total_golden_records": total_golden,
            "open_conflicts": open_conflicts,
        }

    def _compute_field_confidence(self, field: str, source_slug: str) -> float:
        base = SOURCE_PRIORITY.get(source_slug, 50) / 100.0
        if field in ("cr_number", "license_number"):
            return min(base + 0.15, 1.0)
        if field in ("name_ar", "company_name"):
            return min(base + 0.05, 1.0)
        return base

    def _compute_overall_confidence(self, data: dict) -> float:
        if not data:
            return 0.0
        scores = [
            entry.get("confidence", 0.0)
            for entry in data.values()
            if isinstance(entry, dict)
        ]
        return round(sum(scores) / len(scores), 4) if scores else 0.0
