from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ImportColumnMapping(BaseModel):
    source_column: str
    target_field: str


class ImportPreviewRow(BaseModel):
    row_number: int
    data: dict[str, Any]
    validation_errors: list[str] = []


class ImportPreview(BaseModel):
    filename: str
    total_rows: int
    sample_rows: list[ImportPreviewRow]
    detected_columns: list[str]
    suggested_mapping: dict[str, str]


class ImportResult(BaseModel):
    import_id: str
    filename: str
    total_rows: int
    imported: int
    skipped: int
    errors: list[str]
    started_at: datetime
    completed_at: datetime
    status: str
