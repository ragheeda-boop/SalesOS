"""Ingestion Pipeline — MUHIDE Re-Housing (Phase 2).

Handles:
1. File hash dedup (MD5/SHA-256) — reject duplicate files
2. Source row insertion with duplicate detection within file
3. Legacy ID mapping creation (idempotent ON CONFLICT)
4. Global entity creation (companies from MUHIDE v2)

Pipeline flow:
  upload file → hash check → register source file →
  insert source rows (with duplicate groups) →
  create legacy ID mappings → create global entities
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entity_resolution.id_registry import IDRegistry
from app.modules.entity_resolution.resolution_policy import (
    normalize_cr,
    normalize_vat,
)


class IngestionPipeline:
    """MUHIDE v2 file ingestion with dedup, duplicate detection, and entity creation."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = uuid.UUID(tenant_id)
        self.id_registry = IDRegistry(session)

    # ═══════════════════════════════════════════════════════════════════════════════
    # FILE HASH DEDUP
    # ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def compute_file_hash(data: bytes, algorithm: str = "sha256") -> str:
        """Compute file hash (SHA-256 or MD5)."""
        h = hashlib.new(algorithm)
        h.update(data)
        return h.hexdigest()

    async def check_file_hash(self, file_hash: str) -> dict[str, Any] | None:
        """Check if file hash already exists. Returns existing file record or None."""
        result = await self.session.execute(
            text(
                "SELECT id, filename, file_hash_sha256, status, uploaded_at "
                "FROM md_source_files "
                "WHERE file_hash_sha256 = :hash AND tenant_id = :tenant_id"
            ),
            {"hash": file_hash, "tenant_id": self.tenant_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    # ═══════════════════════════════════════════════════════════════════════════════
    # DUPLICATE DETECTION WITHIN FILE
    # ═══════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def detect_duplicates(
        rows: list[dict], key_fields: list[str]
    ) -> list[list[int]]:
        """Detect duplicate groups within rows based on key fields.

        Args:
            rows: List of row dicts (raw_payload)
            key_fields: Fields to use for dedup (e.g., ['cr_number'])

        Returns:
            List of groups, each group is a list of row indices.
            Single-row groups are unique rows.
        """
        groups: dict[str, list[int]] = {}
        for idx, row in enumerate(rows):
            key_parts = []
            for field in key_fields:
                val = row.get(field)
                if val is not None:
                    normalized = str(val).strip().lower()
                    key_parts.append(normalized)
                else:
                    key_parts.append("")
            composite_key = "|".join(key_parts)
            if composite_key not in groups:
                groups[composite_key] = []
            groups[composite_key].append(idx)
        return list(groups.values())

    # ═══════════════════════════════════════════════════════════════════════════════
    # FULL INGESTION PIPELINE
    # ═══════════════════════════════════════════════════════════════════════════════

    async def ingest_file(
        self,
        original_filename: str,
        file_data: bytes,
        source_system: str,
        source_entity_type: str,
        rows: list[dict],
        dedup_key_fields: list[str] | None = None,
        import_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Full ingestion pipeline: hash check → register file → insert rows →
        detect duplicates → create legacy mappings → create global entities.

        Args:
            original_filename: Original file name
            file_data: Raw file bytes
            source_system: Source system identifier (e.g., 'muhide_v2')
            source_entity_type: Entity type (e.g., 'company')
            rows: List of row dicts (raw_payload)
            dedup_key_fields: Fields for within-file duplicate detection
            import_config: Optional import configuration

        Returns:
            Ingestion summary with counts
        """
        start_time = datetime.now(UTC)

        # 1. Compute file hash
        file_hash = self.compute_file_hash(file_data)

        # 2. Check for duplicate file
        existing_file = await self.check_file_hash(file_hash)
        if existing_file:
            return {
                "status": "duplicate",
                "existing_file_id": existing_file["id"],
                "existing_filename": existing_file["original_filename"],
                "message": f"File already ingested as {existing_file['original_filename']}",
            }

        # 3. Register source file
        file_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        await self.session.execute(
            text(
                "INSERT INTO md_source_files "
                "(id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes, "
                "mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status) "
                "VALUES (:id, :tenant_id, :filename, :storage_path, :hash, :size, "
                ":mime_type, 1, :total_rows, :source, :uploaded_by, :now, 'ingesting')"
            ),
            {
                "id": file_id,
                "tenant_id": self.tenant_id,
                "filename": original_filename,
                "storage_path": f"/uploads/{original_filename}",
                "hash": file_hash,
                "size": len(file_data),
                "mime_type": "application/octet-stream",
                "total_rows": len(rows),
                "source": source_system,
                "uploaded_by": str(self.tenant_id),
                "now": now,
            },
        )

        # 4. Insert source rows with duplicate groups
        duplicate_groups = []
        if dedup_key_fields:
            duplicate_groups = self.detect_duplicates(rows, dedup_key_fields)

        group_index_map: dict[int, int] = {}
        for group_idx, group in enumerate(duplicate_groups):
            for row_idx in group:
                group_index_map[row_idx] = group_idx

        inserted_rows = 0
        for idx, row in enumerate(rows):
            row_id = str(uuid.uuid4())
            dup_group = group_index_map.get(idx)
            source_record_id = str(row.get("id", idx))
            await self.session.execute(
                text(
                    "INSERT INTO md_source_rows "
                    "(id, tenant_id, source_file_id, source_id, source_record_id, row_number, "
                    "raw_payload, entity_type, resolution_status, created_at) "
                    "VALUES (:id, :tenant_id, :file_id, :source_id, :source_record_id, :row_number, "
                    ":payload, 'company', 'pending', :now)"
                ),
                {
                    "id": row_id,
                    "tenant_id": self.tenant_id,
                    "file_id": file_id,
                    "source_id": source_system,
                    "source_record_id": source_record_id,
                    "row_number": idx,
                    "payload": row,
                    "now": now,
                },
            )
            inserted_rows += 1

        # 5. Create global entities and legacy mappings
        created_entities = 0
        legacy_mappings_created = 0
        errors = []

        for idx, row in enumerate(rows):
            try:
                cr_raw = row.get("cr_number") or row.get("CR_number")
                cr_normalized = normalize_cr(cr_raw) if cr_raw else None
                name = row.get("company_name") or row.get("name_ar") or row.get("name_en")
                name_ar = row.get("name_ar")
                vat_raw = row.get("vat_number")
                vat_normalized = normalize_vat(vat_raw) if vat_raw else None

                if not name:
                    errors.append({"row": idx, "error": "No company name found"})
                    continue

                # Check if CR already mapped
                existing_mapping = None
                if cr_normalized:
                    existing_result = await self.session.execute(
                        text(
                            "SELECT global_entity_id FROM md_legacy_id_mappings "
                            "WHERE legacy_id_type = 'cr_number' AND legacy_id = :cr"
                        ),
                        {"cr": cr_normalized},
                    )
                    existing_mapping = existing_result.mappings().first()

                if existing_mapping:
                    # Entity already exists — register additional legacy ID
                    global_id = existing_mapping["global_entity_id"]
                    await self._register_legacy_mapping(
                        legacy_id_type="muhide_row_id",
                        legacy_id=str(row.get("id", idx)),
                        global_entity_type="C",
                        global_entity_id=global_id,
                    )
                    legacy_mappings_created += 1
                else:
                    # Create new global company
                    global_id = await self.id_registry.generate_company_id()
                    slug = global_id.lower().replace("g-c-", "gc-")
                    await self.session.execute(
                        text(
                            "INSERT INTO md_global_companies "
                            "(id, slug, canonical_name, cr_number, vat_number, status, created_at, updated_at) "
                            "VALUES (:id, :slug, :name, :cr, :vat, 'active', :now, :now) "
                            "ON CONFLICT (id) DO NOTHING"
                        ),
                        {
                            "id": global_id,
                            "slug": slug,
                            "name": name,
                            "cr": cr_normalized,
                            "vat": vat_normalized,
                            "now": now,
                        },
                    )

                    # Register CR mapping if available
                    if cr_normalized:
                        await self._register_legacy_mapping(
                            legacy_id_type="cr_number",
                            legacy_id=cr_normalized,
                            global_entity_type="C",
                            global_entity_id=global_id,
                        )
                        legacy_mappings_created += 1

                    # Register row ID mapping
                    await self._register_legacy_mapping(
                        legacy_id_type="muhide_row_id",
                        legacy_id=str(row.get("id", idx)),
                        global_entity_type="C",
                        global_entity_id=global_id,
                    )
                    legacy_mappings_created += 1
                    created_entities += 1

            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        # 6. Update source file status
        await self.session.execute(
            text(
                "UPDATE md_source_files "
                "SET status = :status "
                "WHERE id = :id"
            ),
            {"id": file_id, "status": "completed"},
        )

        await self.session.flush()

        duration = (datetime.now(UTC) - start_time).total_seconds()

        return {
            "status": "completed",
            "file_id": file_id,
            "filename": original_filename,
            "file_hash": file_hash,
            "rows_inserted": inserted_rows,
            "duplicate_groups": len(duplicate_groups),
            "entities_created": created_entities,
            "legacy_mappings_created": legacy_mappings_created,
            "errors": errors,
            "duration_seconds": round(duration, 3),
        }

    async def _register_legacy_mapping(
        self,
        legacy_id_type: str,
        legacy_id: str,
        global_entity_type: str,
        global_entity_id: str,
        confidence: float = 1.0,
    ) -> None:
        """Register a legacy ID mapping (idempotent)."""
        now = datetime.now(UTC)
        await self.session.execute(
            text(
                "INSERT INTO md_legacy_id_mappings "
                "(legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at) "
                "VALUES (:type, :legacy_id, :entity_type, :entity_id, :confidence, :now) "
                "ON CONFLICT (legacy_id_type, legacy_id) DO NOTHING"
            ),
            {
                "type": legacy_id_type,
                "legacy_id": legacy_id,
                "entity_type": global_entity_type,
                "entity_id": global_entity_id,
                "confidence": confidence,
                "now": now,
            },
        )
