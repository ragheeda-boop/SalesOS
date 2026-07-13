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
from .city_mapping import CityRegionNormalizer
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
        """Create a new golden record from a source record.

        City and region fields are normalized through CityRegionNormalizer to
        canonical Arabic forms before storage.
        """
        tenant_uuid = uuid.UUID(tenant_id)
        now = datetime.now(timezone.utc)
        city_normalizer = CityRegionNormalizer.default()

        data: dict = {}
        for field, value in record.items():
            if value is not None and not field.startswith("_"):
                # Normalize city and region fields
                normalized_value = value
                if field in ("city", "city_ar", "city_en", "region", "region_ar", "region_en"):
                    if isinstance(value, str):
                        normalized_value = city_normalizer.normalize_city(str(value))

                data[field] = {
                    "value": normalized_value,
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
        Batches DB writes and event publishing for efficiency.
        """
        merged = False
        conflict_count = 0
        now = datetime.now(timezone.utc)
        incoming_priority = SOURCE_PRIORITY.get(source_slug, 0)
        pending_conflicts: list[EntityResolutionConflict] = []

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
                    conflict_count += 1
                    conflict = EntityResolutionConflict(
                        tenant_id=golden.tenant_id,
                        golden_record_id=golden.id,
                        field_name=field,
                        source_a_value=str(existing.get("value", "")),
                        source_a_source=existing.get("source", "unknown"),
                        source_b_value=str(value),
                        source_b_source=source_slug.upper(),
                        status="open",
                    )
                    pending_conflicts.append(conflict)

                    if incoming_priority > existing_priority:
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

        if merged:
            golden.confidence_score = self._compute_overall_confidence(golden.data)
            if source_slug not in (golden.source_ids or []):
                if golden.source_ids:
                    golden.source_ids.append(source_slug)
                else:
                    golden.source_ids = [source_slug]
            golden.updated_at = now

        if pending_conflicts:
            for pc in pending_conflicts:
                self.db.add(pc)

        await self.db.flush()

        if merged and self.event_bus:
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

    async def find_duplicates(
        self,
        tenant_id: str,
        domain: str | None = None,
        cr_number: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        """Find potential duplicate companies by domain, CR, or name."""
        from sqlalchemy import or_, select
        from app.modules.company.models import Company

        tenant_uuid = uuid.UUID(tenant_id)
        stmt = select(Company).where(Company.tenant_id == tenant_uuid)

        if domain:
            domain_like = f"%@{domain}"
            stmt = stmt.where(Company.email.ilike(domain_like))
        elif cr_number:
            stmt = stmt.where(Company.cr_number == cr_number)
        elif name:
            from sqlalchemy import func
            stmt = stmt.where(
                or_(
                    Company.name_ar.ilike(f"%{name}%"),
                    Company.name_en.ilike(f"%{name}%"),
                )
            )
        else:
            return []

        result = await self.db.execute(stmt)
        companies = result.scalars().all()

        candidates = []
        for company in companies:
            match_fields = []
            score = 0.5
            if domain and company.email and domain in company.email:
                match_fields.append("domain_match")
                score = max(score, 0.8)
            if cr_number and company.cr_number == cr_number:
                match_fields.append("cr_match")
                score = max(score, 1.0)
            if name:
                match_fields.append("name_match")
                score = max(score, 0.6)
            candidates.append({
                "company_id": str(company.id),
                "cr_number": company.cr_number,
                "company_name": company.name_ar or company.name_en,
                "name_ar": company.name_ar,
                "name_en": company.name_en,
                "email": company.email,
                "match_fields": match_fields,
                "match_score": score,
            })

        return candidates

    async def find_duplicates_for_company(
        self, company_id: str, tenant_id: str
    ) -> list[dict]:
        """Find potential duplicates for a specific company, excluding itself."""
        from sqlalchemy import select
        from app.modules.company.models import Company

        company = await self.db.get(Company, uuid.UUID(company_id))
        if not company:
            raise NotFoundError("Company", company_id)

        candidates = await self.find_duplicates(
            tenant_id=tenant_id,
            name=company.name_ar or company.name_en,
        )
        return [c for c in candidates if c["company_id"] != company_id]

    async def merge_companies(
        self,
        source_id: str,
        target_id: str,
        tenant_id: str,
        reason: str | None = None,
    ) -> dict:
        """Merge source company into target company, archiving the source."""
        from sqlalchemy import select, update
        from app.modules.company.models import Company

        source = await self.db.get(Company, uuid.UUID(source_id))
        target = await self.db.get(Company, uuid.UUID(target_id))

        if not source:
            raise NotFoundError("Company", source_id)
        if not target:
            raise NotFoundError("Company", target_id)

        # Move relations from source to target
        from app.modules.company.models import Contact, Branch, License
        for model_cls, _ in [(Contact, "contacts"), (Branch, "branches"), (License, "licenses")]:
            stmt = select(model_cls).where(model_cls.company_id == source.id)
            rels = (await self.db.execute(stmt)).scalars().all()
            for rel in rels:
                rel.company_id = target.id

        # Move opportunities
        opps_moved = False
        try:
            from app.modules.revenue_execution.models import Opportunity
            async with self.db.begin_nested():
                stmt = select(Opportunity).where(Opportunity.company_id == source.id)
                opps = (await self.db.execute(stmt)).scalars().all()
                for opp in opps:
                    opp.company_id = target.id
                opps_moved = len(opps) > 0
        except Exception:
            opps_moved = False

        # Merge source IDs
        if source.source_ids:
            for sid in source.source_ids:
                if sid not in (target.source_ids or []):
                    if target.source_ids:
                        target.source_ids = target.source_ids + [sid]
                    else:
                        target.source_ids = [sid]

        # Archive source
        source.is_active = False
        source.status = "merged"
        source.merged_into_id = target.id
        await self.db.flush()

        audit = AuditTrail(self.db)
        await audit.record(
            tenant_id=tenant_id,
            entity_type="company",
            entity_id=source_id,
            action="merged",
            changes={"target_id": target_id, "reason": reason},
        )

        if self.event_bus:
            await self.event_bus.publish(
                EntityResolutionCompleted(
                    tenant_id=tenant_id,
                    aggregate_id=source_id,
                    aggregate_type="company_merge",
                    data={"source_id": source_id, "target_id": target_id},
                )
            )

        return {
            "merged_id": str(target.id),
            "archived_id": str(source.id),
            "merged_fields": {
                "contacts": True,
                "branches": True,
                "licenses": True,
                "opportunities": opps_moved,
                "source_ids": True,
            },
        }
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
