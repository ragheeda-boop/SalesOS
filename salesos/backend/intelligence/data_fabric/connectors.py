from enum import Enum
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


class ConnectorType(str, Enum):
    EMAIL = "email"
    CRM = "crm"
    ERP = "erp"
    CALENDAR = "calendar"
    MESSAGING = "messaging"
    STORAGE = "storage"
    SPREADSHEET = "spreadsheet"
    API = "api"
    DATABASE = "database"


class ConnectorStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"


@dataclass
class Connector:
    id: str
    name: str
    type: ConnectorType
    status: ConnectorStatus = ConnectorStatus.DISCONNECTED
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    records_synced: int = 0
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    connector_id: str
    success: bool
    records_found: int = 0
    records_imported: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    data: list[dict[str, Any]] = field(default_factory=list)


class ConnectorEngine:
    """
    Manages all data connectors.
    Each connector connects to an external system and imports data.
    """

    BUILTIN_CONNECTORS: dict[str, dict[str, Any]] = {
        "gmail": {"name": "Gmail", "type": ConnectorType.EMAIL, "icon": "mail"},
        "outlook": {"name": "Outlook", "type": ConnectorType.EMAIL, "icon": "mail"},
        "hubspot": {"name": "HubSpot", "type": ConnectorType.CRM, "icon": "globe"},
        "odoo": {"name": "Odoo", "type": ConnectorType.ERP, "icon": "database"},
        "sap": {"name": "SAP", "type": ConnectorType.ERP, "icon": "database"},
        "dynamics": {"name": "Dynamics 365", "type": ConnectorType.CRM, "icon": "globe"},
        "slack": {"name": "Slack", "type": ConnectorType.MESSAGING, "icon": "message"},
        "whatsapp": {"name": "WhatsApp", "type": ConnectorType.MESSAGING, "icon": "message"},
        "excel": {"name": "Excel Upload", "type": ConnectorType.SPREADSHEET, "icon": "file"},
        "google_drive": {"name": "Google Drive", "type": ConnectorType.STORAGE, "icon": "folder"},
    }

    def __init__(self):
        self._connectors: dict[str, Connector] = {}
        self._initialize_builtins()

    def _initialize_builtins(self):
        for cid, config in self.BUILTIN_CONNECTORS.items():
            self._connectors[cid] = Connector(
                id=cid, name=config["name"], type=config["type"]
            )

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        return self._connectors.get(connector_id)

    def get_all_connectors(self) -> list[Connector]:
        return list(self._connectors.values())

    def get_by_type(self, connector_type: ConnectorType) -> list[Connector]:
        return [c for c in self._connectors.values() if c.type == connector_type]

    def register_connector(self, connector_id: str, name: str,
                           connector_type: ConnectorType,
                           config: Optional[dict[str, Any]] = None) -> Connector:
        connector = Connector(
            id=connector_id, name=name, type=connector_type,
            config=config or {},
        )
        self._connectors[connector_id] = connector
        return connector

    async def connect(self, connector_id: str, auth: dict[str, Any]) -> bool:
        connector = self._connectors.get(connector_id)
        if not connector:
            return False
        try:
            connector.status = ConnectorStatus.CONNECTED
            connector.config.update(auth)
            return True
        except Exception as e:
            connector.status = ConnectorStatus.ERROR
            connector.last_error = str(e)
            return False

    async def sync(self, connector_id: str, since: Optional[datetime] = None) -> SyncResult:
        connector = self._connectors.get(connector_id)
        if not connector or connector.status != ConnectorStatus.CONNECTED:
            return SyncResult(
                connector_id=connector_id, success=False,
                errors=["Connector not found or not connected"]
            )

        result = SyncResult(connector_id=connector_id, success=True)

        try:
            data = await self._fetch_data(connector_id, since)
            result.records_found = len(data)
            result.data = data
            result.records_imported = len(data)
            result.completed_at = datetime.utcnow()
            connector.last_sync = result.completed_at
            connector.records_synced += len(data)
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            connector.status = ConnectorStatus.ERROR
            connector.last_error = str(e)

        return result

    async def sync_all(self) -> dict[str, SyncResult]:
        results = {}
        for cid in self._connectors:
            if self._connectors[cid].status == ConnectorStatus.CONNECTED:
                results[cid] = await self.sync(cid)
        return results

    async def _fetch_data(self, connector_id: str,
                          since: Optional[datetime] = None) -> list[dict[str, Any]]:
        """Simulated data fetch. Production uses real APIs."""
        now = datetime.utcnow()
        mock_data = {
            "gmail": [
                {"subject": f"Email {i}", "from": f"sender{i}@company.com",
                 "date": now.isoformat(), "body": f"Email body {i}"}
                for i in range(5)
            ],
            "hubspot": [
                {"company": f"Company {i}", "domain": f"company{i}.com",
                 "revenue": i * 100000, "industry": "Technology"}
                for i in range(3)
            ],
            "excel": [
                {"name": f"Entry {i}", "value": i * 100} for i in range(10)
            ],
        }
        return mock_data.get(connector_id, [])

    def disconnect(self, connector_id: str) -> bool:
        connector = self._connectors.get(connector_id)
        if not connector:
            return False
        connector.status = ConnectorStatus.DISCONNECTED
        return True

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total": len(self._connectors),
            "connected": sum(1 for c in self._connectors.values() if c.status == ConnectorStatus.CONNECTED),
            "error": sum(1 for c in self._connectors.values() if c.status == ConnectorStatus.ERROR),
            "total_records": sum(c.records_synced for c in self._connectors.values()),
            "by_type": {
                t.value: sum(1 for c in self._connectors.values() if c.type == t)
                for t in ConnectorType
            },
        }
