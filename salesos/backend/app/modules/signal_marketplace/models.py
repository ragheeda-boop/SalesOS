from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Signal:
    id: str
    name: str
    ar_name: str = ""
    description: str = ""
    domain: str = ""
    category: str = ""
    severity: str = "info"
    source: str = ""
    pack_id: str = ""
    priority: str = "medium"
    weight: float = 0.5
    decay_days: int = 90
    triggers: list[str] = field(default_factory=list)
    relevance_sectors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SignalSubscription:
    id: str
    signal_id: str
    company_id: str
    tenant_id: str
    channel: str = "in-app"
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SignalEvent:
    id: str
    signal_id: str
    company_id: str
    tenant_id: str
    data: dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
