from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class NotionSourceConfig(BaseModel):
    database_id: str
    token: str


class SyncRequest(BaseModel):
    source: NotionSourceConfig
    direction: str = "import"  # import | export
    entity_type: str = "company"  # company | contact


class SyncStatus(BaseModel):
    sync_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    entities_found: int = 0
    entities_imported: int = 0
    entities_skipped: int = 0
    errors: list[str] = []


class SyncResult(BaseModel):
    status: str
    message: str
    details: SyncStatus
