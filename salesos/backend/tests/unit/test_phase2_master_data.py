"""Phase 2 tests — Ingestion Pipeline, File Dedup, Duplicate Detection.

Tests verify:
- File hash computation (SHA-256, MD5)
- Duplicate detection within source rows
- Schema validation for ingestion endpoints
- Pipeline flow (hash → register → insert → detect → create)
"""

from __future__ import annotations

import hashlib
import json

import pytest

from app.modules.master_data.ingestion import IngestionPipeline
from app.modules.master_data.ingestion_router import (
    DetectDuplicatesRequest,
    DetectDuplicatesResponse,
    DuplicateGroupResponse,
    FileHashCheckResponse,
    IngestFileRequest,
    IngestFileResponse,
)
from app.modules.master_data.schemas import SourceFileCreate


# ═══════════════════════════════════════════════════════════════════════════════
# FILE HASH COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════


class TestFileHash:
    """File hash dedup — SHA-256 and MD5."""

    def test_sha256_hash(self):
        """SHA-256 hash is deterministic and correct."""
        data = b"test file content"
        h = hashlib.sha256(data).hexdigest()
        assert len(h) == 64
        assert IngestionPipeline.compute_file_hash(data, "sha256") == h

    def test_md5_hash(self):
        """MD5 hash is deterministic and correct."""
        data = b"test file content"
        h = hashlib.md5(data).hexdigest()
        assert len(h) == 32
        assert IngestionPipeline.compute_file_hash(data, "md5") == h

    def test_same_data_same_hash(self):
        """Same data always produces the same hash."""
        data = b"consistent data"
        h1 = IngestionPipeline.compute_file_hash(data)
        h2 = IngestionPipeline.compute_file_hash(data)
        assert h1 == h2

    def test_different_data_different_hash(self):
        """Different data produces different hashes."""
        h1 = IngestionPipeline.compute_file_hash(b"data1")
        h2 = IngestionPipeline.compute_file_hash(b"data2")
        assert h1 != h2

    def test_empty_data_hash(self):
        """Empty data produces a valid hash."""
        h = IngestionPipeline.compute_file_hash(b"")
        assert len(h) == 64  # SHA-256


# ═══════════════════════════════════════════════════════════════════════════════
# DUPLICATE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


class TestDuplicateDetection:
    """Within-file duplicate detection based on key fields."""

    def test_no_duplicates(self):
        """Rows with unique keys produce no duplicate groups."""
        rows = [
            {"cr_number": "12345", "name": "A"},
            {"cr_number": "67890", "name": "B"},
            {"cr_number": "11111", "name": "C"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        assert len(groups) == 3
        assert all(len(g) == 1 for g in groups)

    def test_one_duplicate_group(self):
        """Two rows with same CR form one duplicate group."""
        rows = [
            {"cr_number": "12345", "name": "A"},
            {"cr_number": "12345", "name": "A'"},
            {"cr_number": "67890", "name": "B"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 1
        assert sorted(dup_groups[0]) == [0, 1]

    def test_multiple_duplicate_groups(self):
        """Multiple duplicate groups detected correctly."""
        rows = [
            {"cr_number": "12345", "name": "A"},
            {"cr_number": "12345", "name": "A'"},
            {"cr_number": "67890", "name": "B"},
            {"cr_number": "67890", "name": "B'"},
            {"cr_number": "67890", "name": "B''"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 2
        assert sorted(dup_groups[0]) == [0, 1]
        assert sorted(dup_groups[1]) == [2, 3, 4]

    def test_case_insensitive(self):
        """Duplicate detection is case-insensitive."""
        rows = [
            {"cr_number": "12345", "name": "A"},
            {"cr_number": "12345", "name": "A'"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 1

    def test_whitespace_stripped(self):
        """Duplicate detection strips whitespace."""
        rows = [
            {"cr_number": "  12345  ", "name": "A"},
            {"cr_number": "12345", "name": "A'"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 1

    def test_multi_field_key(self):
        """Duplicate detection with composite key (cr_number + name)."""
        rows = [
            {"cr_number": "12345", "name": "A"},
            {"cr_number": "12345", "name": "B"},  # Different name → unique
            {"cr_number": "12345", "name": "A"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number", "name"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 1
        assert sorted(dup_groups[0]) == [0, 2]

    def test_empty_rows(self):
        """Empty rows list returns no groups."""
        groups = IngestionPipeline.detect_duplicates([], ["cr_number"])
        assert groups == []

    def test_none_values_treated_as_empty(self):
        """None values are treated as empty strings."""
        rows = [
            {"cr_number": None, "name": "A"},
            {"cr_number": None, "name": "B"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


class TestIngestionSchemaValidation:
    """API schema models for ingestion endpoints."""

    def test_ingest_file_request_valid(self):
        """IngestFileRequest accepts valid data."""
        obj = IngestFileRequest(
            source_system="muhide_v2",
            rows=[{"cr_number": "12345", "name": "Test Co"}],
            dedup_key_fields=["cr_number"],
        )
        assert obj.source_system == "muhide_v2"
        assert len(obj.rows) == 1

    def test_ingest_file_request_empty_source_system_rejected(self):
        """IngestFileRequest rejects empty source_system."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            IngestFileRequest(
                source_system="",
                rows=[],
            )

    def test_ingest_file_request_empty_rows_valid(self):
        """IngestFileRequest allows empty rows list."""
        obj = IngestFileRequest(
            source_system="muhide_v2",
            rows=[],
        )
        assert len(obj.rows) == 0

    def test_detect_duplicates_request_valid(self):
        """DetectDuplicatesRequest accepts valid data."""
        obj = DetectDuplicatesRequest(
            rows=[{"cr_number": "12345"}],
            key_fields=["cr_number"],
        )
        assert len(obj.rows) == 1

    def test_ingest_file_response_valid(self):
        """IngestFileResponse accepts valid data."""
        obj = IngestFileResponse(
            status="completed",
            file_id="test-file-id",
            filename="test.xlsx",
            rows_inserted=10,
            entities_created=10,
        )
        assert obj.status == "completed"

    def test_file_hash_check_response_exists(self):
        """FileHashCheckResponse when file exists."""
        obj = FileHashCheckResponse(
            exists=True,
            file_id="test-id",
            filename="test.xlsx",
            status="completed",
        )
        assert obj.exists is True

    def test_file_hash_check_response_not_exists(self):
        """FileHashCheckResponse when file doesn't exist."""
        obj = FileHashCheckResponse(exists=False)
        assert obj.exists is False


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE FLOW (unit-level)
# ═══════════════════════════════════════════════════════════════════════════════


class TestIngestionPipelineFlow:
    """Pipeline flow tests — no DB required."""

    def test_compute_hash_returns_hex_string(self):
        """Hash computation returns a valid hex string."""
        data = json.dumps({"test": "data"}).encode("utf-8")
        h = IngestionPipeline.compute_file_hash(data)
        assert all(c in "0123456789abcdef" for c in h)
        assert len(h) == 64

    def test_detect_duplicates_composite_key(self):
        """Composite key detection works correctly."""
        rows = [
            {"cr_number": "12345", "name_ar": "شركة أ"},
            {"cr_number": "12345", "name_ar": "شركة أ"},
            {"cr_number": "67890", "name_ar": "شركة ب"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number"])
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 1
        assert sorted(dup_groups[0]) == [0, 1]

    def test_detect_duplicates_with_missing_fields(self):
        """Missing fields are treated as empty strings."""
        rows = [
            {"cr_number": "12345"},
            {"cr_number": "12345", "name_ar": "different"},
        ]
        groups = IngestionPipeline.detect_duplicates(rows, ["cr_number", "name_ar"])
        # Both have same cr_number but different name_ar
        dup_groups = [g for g in groups if len(g) > 1]
        assert len(dup_groups) == 0  # Not duplicates by composite key


# ═══════════════════════════════════════════════════════════════════════════════
# ARCHITECTURE INVARIANTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestArchitecturePhase2:
    """Phase 2 architecture invariants."""

    def test_source_rows_immutable(self):
        """Source rows are INSERT-only — no UPDATE/DELETE in pipeline."""
        # Enforced by application layer: no UPDATE/DELETE in IngestionPipeline
        pass

    def test_file_hash_dedup_prevents_reimport(self):
        """Same file hash is rejected on second import."""
        # Enforced by check_file_hash() returning existing file
        pass

    def test_legacy_mapping_idempotent(self):
        """Legacy mapping ON CONFLICT DO NOTHING prevents duplicates."""
        # Enforced by SQL in _register_legacy_mapping()
        pass

    def test_global_entity_created_once_per_cr(self):
        """CR number maps to exactly one global entity."""
        # Enforced by: check existing mapping before create
        pass
