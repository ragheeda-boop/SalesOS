from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SignalSubscription:
    id: str
    signal_id: str
    company_id: str
    tenant_id: str
    channel: str = "in-app"
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SignalEvent:
    id: str
    signal_id: str
    company_id: str
    tenant_id: str
    data: dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
