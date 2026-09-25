"""Master Data Service — CRUD for global master entities.

Phase 1 scope:
- Global Company (md_global_companies) — create, read, update, list
- Global Person (md_global_people) — create, read, update, list
- Legacy ID Mapping (md_legacy_id_mappings) — register, query
- Source File (md_source_files) — register, query
- Source Row (md_source_rows) — insert, query

ID generation uses the ID Registry (G-C-XXXXXXXX / G-P-XXXXXXXX).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entity_resolution.id_registry import IDRegistry


class MasterDataService:
    """CRUD operations for global master entities."""

    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self.session = session
        self.tenant_id = uuid.UUID(tenant_id) if tenant_id else None
        self.id_registry = IDRegistry(session)

    # ═══════════════════════════════════════════════════════════════════════════════
    # Global Company
    # ═══════════════════════════════════════════════════════════════════════════════

    async def create_global_company(
        self,
        canonical_name: str,
        canonical_name_ar: str | None = None,
        cr_number: str | None = None,
        vat_number: str | None = None,
        unified_national_number: str | None = None,
        status: str = "active",
    ) -> dict[str, Any]:
        """Create a global company with generated G-C-XXXXXXXX ID."""
        global_id = await self.id_registry.generate_company_id()
        slug = global_id.lower().replace("g-c-", "gc-")
        now = datetime.now(UTC)

        result = await self.session.execute(
            text(
                "INSERT INTO md_global_companies "
                "(id, slug, canonical_name, canonical_name_ar, cr_number, vat_number, "
                "unified_national_number, status, created_at, updated_at) "
                "VALUES (:id, :slug, :name, :name_ar, :cr, :vat, :unified, :status, :now, :now) "
                "RETURNING id, slug, canonical_name, canonical_name_ar, cr_number, vat_number, "
                "unified_national_number, status, created_at, updated_at"
            ),
            {
                "id": global_id,
                "slug": slug,
                "name": canonical_name,
                "name_ar": canonical_name_ar,
                "cr": cr_number,
                "vat": vat_number,
                "unified": unified_national_number,
                "status": status,
                "now": now,
            },
        )
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else {"id": global_id}

    async def get_global_company(self, company_id: str) -> dict[str, Any] | None:
        """Get a global company by ID."""
        result = await self.session.execute(
            text("SELECT * FROM md_global_companies WHERE id = :id"),
            {"id": company_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_global_company(
        self, company_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a global company. Returns updated row or None."""
        set_clauses = []
        params: dict[str, Any] = {"id": company_id, "now": datetime.now(UTC)}
        field_map = {
            "canonical_name": "canonical_name",
            "canonical_name_ar": "canonical_name_ar",
            "cr_number": "cr_number",
            "vat_number": "vat_number",
            "unified_national_number": "unified_national_number",
            "status": "status",
        }
        for key, value in updates.items():
            db_col = field_map.get(key)
            if value is not None and db_col:
                set_clauses.append(f"{db_col} = :{key}")
                params[key] = value
        if not set_clauses:
            return await self.get_global_company(company_id)
        set_clauses.append("updated_at = :now")
        sql = f"UPDATE md_global_companies SET {', '.join(set_clauses)} WHERE id = :id RETURNING *"
        result = await self.session.execute(text(sql), params)
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else None

    async def list_global_companies(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """List global companies with pagination."""
        offset = (page - 1) * page_size
        count_result = await self.session.execute(
            text("SELECT COUNT(*) FROM md_global_companies")
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            text(
                "SELECT * FROM md_global_companies ORDER BY created_at DESC "
                "LIMIT :limit OFFSET :offset"
            ),
            {"limit": page_size, "offset": offset},
        )
        rows = [dict(r) for r in result.mappings().all()]
        return rows, total

    # ═══════════════════════════════════════════════════════════════════════════════
    # Global Person
    # ═══════════════════════════════════════════════════════════════════════════════

    async def create_global_person(
        self,
        canonical_name: str,
        email: str | None = None,
        phone: str | None = None,
        company_global_id: str | None = None,
        job_title: str | None = None,
        status: str = "active",
    ) -> dict[str, Any]:
        """Create a global person with generated G-P-XXXXXXXX ID."""
        global_id = await self.id_registry.generate_person_id()
        slug = global_id.lower().replace("g-p-", "gp-")
        now = datetime.now(UTC)

        result = await self.session.execute(
            text(
                "INSERT INTO md_global_people "
                "(id, slug, canonical_name, email, phone, company_global_id, job_title, status, created_at, updated_at) "
                "VALUES (:id, :slug, :name, :email, :phone, :company_id, :job_title, :status, :now, :now) "
                "RETURNING id, slug, canonical_name, email, phone, company_global_id, job_title, status, created_at, updated_at"
            ),
            {
                "id": global_id,
                "slug": slug,
                "name": canonical_name,
                "email": email,
                "phone": phone,
                "company_id": company_global_id,
                "job_title": job_title,
                "status": status,
                "now": now,
            },
        )
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else {"id": global_id}

    async def get_global_person(self, person_id: str) -> dict[str, Any] | None:
        """Get a global person by ID."""
        result = await self.session.execute(
            text("SELECT * FROM md_global_people WHERE id = :id"),
            {"id": person_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_global_person(
        self, person_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a global person."""
        set_clauses = []
        params: dict[str, Any] = {"id": person_id, "now": datetime.now(UTC)}
        field_map = {
            "canonical_name": "canonical_name",
            "email": "email",
            "phone": "phone",
            "company_global_id": "company_global_id",
            "job_title": "job_title",
            "status": "status",
        }
        for key, value in updates.items():
            db_col = field_map.get(key)
            if value is not None and db_col:
                set_clauses.append(f"{db_col} = :{key}")
                params[key] = value
        if not set_clauses:
            return await self.get_global_person(person_id)
        set_clauses.append("updated_at = :now")
        sql = f"UPDATE md_global_people SET {', '.join(set_clauses)} WHERE id = :id RETURNING *"
        result = await self.session.execute(text(sql), params)
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else None

    async def list_global_people(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """List global people with pagination."""
        offset = (page - 1) * page_size
        count_result = await self.session.execute(
            text("SELECT COUNT(*) FROM md_global_people")
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            text(
                "SELECT * FROM md_global_people ORDER BY created_at DESC "
                "LIMIT :limit OFFSET :offset"
            ),
            {"limit": page_size, "offset": offset},
        )
        rows = [dict(r) for r in result.mappings().all()]
        return rows, total

    # ═══════════════════════════════════════════════════════════════════════════════
    # Legacy ID Mapping
    # ═══════════════════════════════════════════════════════════════════════════════

    async def register_legacy_id(
        self,
        legacy_id_type: str,
        legacy_id: str,
        global_entity_type: str,
        global_entity_id: str,
        confidence: float = 1.0,
    ) -> dict[str, Any] | None:
        """Register a legacy→global ID mapping. Idempotent (ON CONFLICT DO NOTHING)."""
        now = datetime.now(UTC)
        result = await self.session.execute(
            text(
                "INSERT INTO md_legacy_id_mappings "
                "(legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at) "
                "VALUES (:type, :legacy_id, :entity_type, :entity_id, :confidence, :now) "
                "ON CONFLICT (legacy_id_type, legacy_id) DO NOTHING "
                "RETURNING id, legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at"
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
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else None

    async def get_legacy_mapping(
        self, legacy_id_type: str, legacy_id: str
    ) -> dict[str, Any] | None:
        """Look up a legacy ID mapping."""
        result = await self.session.execute(
            text(
                "SELECT * FROM md_legacy_id_mappings "
                "WHERE legacy_id_type = :type AND legacy_id = :legacy_id"
            ),
            {"type": legacy_id_type, "legacy_id": legacy_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def list_legacy_mappings_for_entity(
        self, global_entity_id: str
    ) -> list[dict]:
        """List all legacy mappings for a global entity."""
        result = await self.session.execute(
            text(
                "SELECT * FROM md_legacy_id_mappings "
                "WHERE global_entity_id = :entity_id ORDER BY created_at"
            ),
            {"entity_id": global_entity_id},
        )
        return [dict(r) for r in result.mappings().all()]

    # ═══════════════════════════════════════════════════════════════════════════════
    # Source File
    # ═══════════════════════════════════════════════════════════════════════════════

    async def register_source_file(
        self,
        filename: str,
        file_hash_sha256: str,
        file_size_bytes: int,
        source_system: str,
        mime_type: str,
        storage_path: str,
        uploaded_by: str,
        sheet_count: int = 0,
        total_rows: int = 0,
        schema_mapping: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register an uploaded source file. Returns file record."""
        if not self.tenant_id:
            raise ValueError("tenant_id required for source file registration")
        file_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        result = await self.session.execute(
            text(
                "INSERT INTO md_source_files "
                "(id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes, "
                "mime_type, sheet_count, total_rows, source_system, schema_mapping, "
                "uploaded_by, uploaded_at, status) "
                "VALUES (:id, :tenant_id, :filename, :storage_path, :hash, :size, "
                ":mime_type, :sheet_count, :total_rows, :source, :schema_mapping, "
                ":uploaded_by, :now, 'uploaded') "
                "RETURNING id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes, "
                "mime_type, sheet_count, total_rows, source_system, schema_mapping, "
                "uploaded_by, uploaded_at, status"
            ),
            {
                "id": file_id,
                "tenant_id": self.tenant_id,
                "filename": filename,
                "storage_path": storage_path,
                "hash": file_hash_sha256,
                "size": file_size_bytes,
                "mime_type": mime_type,
                "sheet_count": sheet_count,
                "total_rows": total_rows,
                "source": source_system,
                "schema_mapping": schema_mapping,
                "uploaded_by": uploaded_by,
                "now": now,
            },
        )
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else {"id": file_id}

    async def get_source_file(self, file_id: str) -> dict[str, Any] | None:
        """Get a source file by ID."""
        result = await self.session.execute(
            text("SELECT * FROM md_source_files WHERE id = :id"),
            {"id": file_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def list_source_files(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        """List source files for the current tenant."""
        if not self.tenant_id:
            return [], 0
        offset = (page - 1) * page_size
        count_result = await self.session.execute(
            text("SELECT COUNT(*) FROM md_source_files WHERE tenant_id = :tenant_id"),
            {"tenant_id": self.tenant_id},
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            text(
                "SELECT * FROM md_source_files WHERE tenant_id = :tenant_id "
                "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
            ),
            {"tenant_id": self.tenant_id, "limit": page_size, "offset": offset},
        )
        rows = [dict(r) for r in result.mappings().all()]
        return rows, total

    # ═══════════════════════════════════════════════════════════════════════════════
    # Source Row
    # ═══════════════════════════════════════════════════════════════════════════════

    async def insert_source_row(
        self,
        source_file_id: str,
        source_id: str,
        source_record_id: str,
        row_number: int,
        raw_payload: dict[str, Any],
        sheet_name: str | None = None,
        entity_type: str = "company",
    ) -> dict[str, Any]:
        """Insert a source row (immutable after insert)."""
        if not self.tenant_id:
            raise ValueError("tenant_id required for source row insertion")
        row_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        result = await self.session.execute(
            text(
                "INSERT INTO md_source_rows "
                "(id, tenant_id, source_file_id, source_id, source_record_id, row_number, "
                "sheet_name, raw_payload, entity_type, resolution_status, created_at) "
                "VALUES (:id, :tenant_id, :file_id, :source_id, :source_record_id, :row_number, "
                ":sheet_name, :payload, :entity_type, 'pending', :now) "
                "RETURNING id, tenant_id, source_file_id, source_id, source_record_id, row_number, "
                "sheet_name, raw_payload, entity_type, resolution_status, created_at"
            ),
            {
                "id": row_id,
                "tenant_id": self.tenant_id,
                "file_id": source_file_id,
                "source_id": source_id,
                "source_record_id": source_record_id,
                "row_number": row_number,
                "sheet_name": sheet_name,
                "payload": raw_payload,
                "entity_type": entity_type,
                "now": now,
            },
        )
        row = result.mappings().first()
        await self.session.flush()
        return dict(row) if row else {"id": row_id}

    async def get_source_row(self, row_id: str) -> dict[str, Any] | None:
        """Get a source row by ID."""
        result = await self.session.execute(
            text("SELECT * FROM md_source_rows WHERE id = :id"),
            {"id": row_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def list_source_rows(
        self, source_file_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[dict], int]:
        """List source rows for a file."""
        if not self.tenant_id:
            return [], 0
        offset = (page - 1) * page_size
        count_result = await self.session.execute(
            text(
                "SELECT COUNT(*) FROM md_source_rows "
                "WHERE source_file_id = :file_id AND tenant_id = :tenant_id"
            ),
            {"file_id": source_file_id, "tenant_id": self.tenant_id},
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            text(
                "SELECT * FROM md_source_rows "
                "WHERE source_file_id = :file_id AND tenant_id = :tenant_id "
                "ORDER BY row_number ASC LIMIT :limit OFFSET :offset"
            ),
            {
                "file_id": source_file_id,
                "tenant_id": self.tenant_id,
                "limit": page_size,
                "offset": offset,
            },
        )
        rows = [dict(r) for r in result.mappings().all()]
        return rows, total
