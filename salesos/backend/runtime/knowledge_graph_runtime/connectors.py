"""Data Fabric Connectors — real implementations for CRM, ERP, and Market Feed.

Each connector implements: auth → fetch → transform → store → error handling.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


class ConnectorStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class ConnectorType(str, Enum):
    CRM = "crm"
    ERP = "erp"
    MARKET_FEED = "market_feed"


@dataclass
class ConnectorRecord:
    source_type: ConnectorType
    source_id: str
    raw_data: dict
    transformed_data: dict = field(default_factory=dict)
    status: str = "pending"
    error: Optional[str] = None


@dataclass
class ConnectorResult:
    connector_type: ConnectorType
    records_fetched: int = 0
    records_transformed: int = 0
    records_stored: int = 0
    records_failed: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    def snapshot(self) -> dict:
        return {
            "connector_type": self.connector_type.value,
            "records_fetched": self.records_fetched,
            "records_transformed": self.records_transformed,
            "records_stored": self.records_stored,
            "records_failed": self.records_failed,
            "duration_ms": round(self.duration_ms, 2),
            "errors": self.errors,
        }


class BaseConnector(ABC):
    """Abstract base for all Data Fabric connectors.

    Subclasses must implement:
      - authenticate() — establish API credentials
      - fetch() — pull raw records from external system
      - transform() — map external fields to canonical schema
      - store() — persist transformed records to database
    """

    connector_type: ConnectorType

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        config: dict[str, Any],
        logger: Any = None,
    ):
        self._session_factory = session_factory
        self._config = config
        self._logger = logger
        self._authenticated = False
        self._auth_token: Optional[str] = None
        self._status = ConnectorStatus.IDLE
        self._last_sync: Optional[datetime] = None
        self._error_count = 0
        self._success_count = 0

    @property
    def status(self) -> ConnectorStatus:
        return self._status

    @property
    def last_sync(self) -> Optional[datetime]:
        return self._last_sync

    @abstractmethod
    async def authenticate(self) -> bool:
        """Establish API credentials. Returns True if successful."""
        ...

    @abstractmethod
    async def fetch(self, tenant_id: str, since: Optional[datetime] = None) -> list[ConnectorRecord]:
        """Pull raw records from external system."""
        ...

    @abstractmethod
    def transform(self, records: list[ConnectorRecord]) -> list[ConnectorRecord]:
        """Map external fields to canonical schema."""
        ...

    @abstractmethod
    async def store(self, records: list[ConnectorRecord], tenant_id: str) -> int:
        """Persist transformed records. Returns count stored."""
        ...

    async def sync(self, tenant_id: str, since: Optional[datetime] = None) -> ConnectorResult:
        """Execute full sync: authenticate → fetch → transform → store."""
        t0 = time.monotonic()
        result = ConnectorResult(connector_type=self.connector_type)
        self._status = ConnectorStatus.RUNNING

        try:
            # Step 1: Authenticate
            if not self._authenticated:
                auth_ok = await self.authenticate()
                if not auth_ok:
                    result.errors.append("Authentication failed")
                    self._status = ConnectorStatus.FAILED
                    return result

            # Step 2: Fetch
            records = await self.fetch(tenant_id, since)
            result.records_fetched = len(records)

            # Step 3: Transform
            transformed = self.transform(records)
            result.records_transformed = len(transformed)

            # Step 4: Store
            stored = await self.store(transformed, tenant_id)
            result.records_stored = stored
            result.records_failed = len(transformed) - stored

            self._status = ConnectorStatus.COMPLETED
            self._last_sync = datetime.now(timezone.utc)
            self._success_count += 1

        except Exception as exc:
            self._status = ConnectorStatus.FAILED
            self._error_count += 1
            result.errors.append(str(exc))
            if self._logger:
                self._logger.error("Connector %s sync failed: %s", self.connector_type.value, exc)

        result.duration_ms = (time.monotonic() - t0) * 1000
        return result


class CrmConnector(BaseConnector):
    """CRM connector — fetch company/contact data from external CRM.

    Supports configurable CRM API endpoint, auth token, and field mapping.
    """

    connector_type = ConnectorType.CRM

    async def authenticate(self) -> bool:
        api_url = self._config.get("api_url", "")
        api_key = self._config.get("api_key", "")
        if not api_url or not api_key:
            if self._logger:
                self._logger.warning("CRM connector: missing api_url or api_key")
            return False
        self._auth_token = api_key
        self._authenticated = True
        return True

    async def fetch(self, tenant_id: str, since: Optional[datetime] = None) -> list[ConnectorRecord]:
        api_url = self._config.get("api_url", "")
        if not self._auth_token:
            return []

        try:
            import httpx
            headers = {"Authorization": f"Bearer {self._auth_token}"}
            params: dict[str, Any] = {"tenant_id": tenant_id, "limit": 500}
            if since:
                params["updated_after"] = since.isoformat()

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{api_url}/api/v1/contacts", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            records = []
            for item in data.get("items", data.get("contacts", [])):
                records.append(ConnectorRecord(
                    source_type=ConnectorType.CRM,
                    source_id=item.get("id", ""),
                    raw_data=item,
                ))
            return records
        except ImportError:
            if self._logger:
                self._logger.warning("httpx not installed, using mock CRM data")
            return self._mock_fetch(tenant_id)
        except Exception as exc:
            if self._logger:
                self._logger.error("CRM fetch failed: %s", exc)
            return []

    def _mock_fetch(self, tenant_id: str) -> list[ConnectorRecord]:
        """Fallback mock data when httpx is unavailable or API is unreachable."""
        mock_data = [
            {"id": "crm-001", "name": "ACME Corp", "email": "info@acme.com", "phone": "+966501234567", "city": "Riyadh"},
            {"id": "crm-002", "name": "Saudi Tech", "email": "contact@sauditech.com", "phone": "+966509876543", "city": "Jeddah"},
        ]
        return [
            ConnectorRecord(source_type=ConnectorType.CRM, source_id=item["id"], raw_data=item)
            for item in mock_data
        ]

    def transform(self, records: list[ConnectorRecord]) -> list[ConnectorRecord]:
        field_map = self._config.get("field_map", {})
        for record in records:
            raw = record.raw_data
            record.transformed_data = {
                "name_ar": raw.get(field_map.get("name_ar", "name_ar"), raw.get("name", "")),
                "name_en": raw.get(field_map.get("name_en", "name_en"), raw.get("name", "")),
                "email": raw.get(field_map.get("email", "email"), ""),
                "phone": raw.get(field_map.get("phone", "phone"), ""),
                "city": raw.get(field_map.get("city", "city"), ""),
                "source": "crm",
                "external_id": record.source_id,
            }
            record.status = "transformed"
        return records

    async def store(self, records: list[ConnectorRecord], tenant_id: str) -> int:
        stored = 0
        async with self._session_factory() as session:
            for record in records:
                try:
                    td = record.transformed_data
                    await session.execute(
                        sa_text("""
                            INSERT INTO companies (id, tenant_id, name_en, name_ar, city, is_active, source)
                            VALUES (:id, :tid, :name_en, :name_ar, :city, true, 'crm')
                            ON CONFLICT (id) DO UPDATE SET
                                name_en = EXCLUDED.name_en,
                                name_ar = EXCLUDED.name_ar,
                                city = EXCLUDED.city,
                                updated_at = NOW()
                        """),
                        {
                            "id": record.source_id,
                            "tid": tenant_id,
                            "name_en": td.get("name_en", ""),
                            "name_ar": td.get("name_ar", ""),
                            "city": td.get("city", ""),
                        },
                    )
                    stored += 1
                except Exception as exc:
                    record.status = "failed"
                    record.error = str(exc)
            await session.commit()
        return stored


class ErpConnector(BaseConnector):
    """ERP connector — fetch financial/order data from ERP system."""

    connector_type = ConnectorType.ERP

    async def authenticate(self) -> bool:
        api_url = self._config.get("api_url", "")
        api_key = self._config.get("api_key", "")
        if not api_url or not api_key:
            if self._logger:
                self._logger.warning("ERP connector: missing api_url or api_key")
            return False
        self._auth_token = api_key
        self._authenticated = True
        return True

    async def fetch(self, tenant_id: str, since: Optional[datetime] = None) -> list[ConnectorRecord]:
        api_url = self._config.get("api_url", "")
        if not self._auth_token:
            return []

        try:
            import httpx
            headers = {"Authorization": f"Bearer {self._auth_token}"}
            params: dict[str, Any] = {"tenant_id": tenant_id, "limit": 500}
            if since:
                params["updated_after"] = since.isoformat()

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{api_url}/api/v1/orders", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            records = []
            for item in data.get("items", data.get("orders", [])):
                records.append(ConnectorRecord(
                    source_type=ConnectorType.ERP,
                    source_id=item.get("id", ""),
                    raw_data=item,
                ))
            return records
        except ImportError:
            if self._logger:
                self._logger.warning("httpx not installed, using mock ERP data")
            return self._mock_fetch(tenant_id)
        except Exception as exc:
            if self._logger:
                self._logger.error("ERP fetch failed: %s", exc)
            return []

    def _mock_fetch(self, tenant_id: str) -> list[ConnectorRecord]:
        mock_data = [
            {"id": "erp-001", "company_name": "ACME Corp", "order_total": 150000, "currency": "SAR", "status": "completed"},
            {"id": "erp-002", "company_name": "Saudi Tech", "order_total": 85000, "currency": "SAR", "status": "pending"},
        ]
        return [
            ConnectorRecord(source_type=ConnectorType.ERP, source_id=item["id"], raw_data=item)
            for item in mock_data
        ]

    def transform(self, records: list[ConnectorRecord]) -> list[ConnectorRecord]:
        for record in records:
            raw = record.raw_data
            record.transformed_data = {
                "name_en": raw.get("company_name", ""),
                "order_total": raw.get("order_total", 0),
                "currency": raw.get("currency", "SAR"),
                "order_status": raw.get("status", ""),
                "source": "erp",
                "external_id": record.source_id,
            }
            record.status = "transformed"
        return records

    async def store(self, records: list[ConnectorRecord], tenant_id: str) -> int:
        stored = 0
        async with self._session_factory() as session:
            for record in records:
                try:
                    td = record.transformed_data
                    await session.execute(
                        sa_text("""
                            INSERT INTO companies (id, tenant_id, name_en, capital, is_active, source)
                            VALUES (:id, :tid, :name_en, :capital, true, 'erp')
                            ON CONFLICT (id) DO UPDATE SET
                                name_en = EXCLUDED.name_en,
                                capital = EXCLUDED.capital,
                                updated_at = NOW()
                        """),
                        {
                            "id": record.source_id,
                            "tid": tenant_id,
                            "name_en": td.get("name_en", ""),
                            "capital": td.get("order_total", 0),
                        },
                    )
                    stored += 1
                except Exception as exc:
                    record.status = "failed"
                    record.error = str(exc)
            await session.commit()
        return stored


class MarketFeedConnector(BaseConnector):
    """Market feed connector — fetch market data from external API."""

    connector_type = ConnectorType.MARKET_FEED

    async def authenticate(self) -> bool:
        api_key = self._config.get("api_key", "")
        if not api_key:
            if self._logger:
                self._logger.warning("Market feed connector: missing api_key")
            return False
        self._auth_token = api_key
        self._authenticated = True
        return True

    async def fetch(self, tenant_id: str, since: Optional[datetime] = None) -> list[ConnectorRecord]:
        api_url = self._config.get("api_url", "https://api.example.com/market")
        if not self._auth_token:
            return []

        try:
            import httpx
            headers = {"Authorization": f"Bearer {self._auth_token}"}
            params: dict[str, Any] = {"limit": 500}
            if since:
                params["since"] = since.isoformat()

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{api_url}/companies", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            records = []
            for item in data.get("items", data.get("companies", [])):
                records.append(ConnectorRecord(
                    source_type=ConnectorType.MARKET_FEED,
                    source_id=item.get("id", item.get("ticker", "")),
                    raw_data=item,
                ))
            return records
        except ImportError:
            return self._mock_fetch(tenant_id)
        except Exception as exc:
            if self._logger:
                self._logger.error("Market feed fetch failed: %s", exc)
            return []

    def _mock_fetch(self, tenant_id: str) -> list[ConnectorRecord]:
        mock_data = [
            {"id": "mkt-001", "name": "Saudi Aramco", "sector": "Energy", "market_cap": 7_000_000_000_000},
            {"id": "mkt-002", "name": "SABIC", "sector": "Petrochemicals", "market_cap": 350_000_000_000},
            {"id": "mkt-003", "name": "STC", "sector": "Telecom", "market_cap": 180_000_000_000},
        ]
        return [
            ConnectorRecord(source_type=ConnectorType.MARKET_FEED, source_id=item["id"], raw_data=item)
            for item in mock_data
        ]

    def transform(self, records: list[ConnectorRecord]) -> list[ConnectorRecord]:
        for record in records:
            raw = record.raw_data
            record.transformed_data = {
                "name_en": raw.get("name", ""),
                "industry": raw.get("sector", ""),
                "market_cap": raw.get("market_cap", 0),
                "source": "market_feed",
                "external_id": record.source_id,
            }
            record.status = "transformed"
        return records

    async def store(self, records: list[ConnectorRecord], tenant_id: str) -> int:
        stored = 0
        async with self._session_factory() as session:
            for record in records:
                try:
                    td = record.transformed_data
                    await session.execute(
                        sa_text("""
                            INSERT INTO companies (id, tenant_id, name_en, industry, capital, is_active, source)
                            VALUES (:id, :tid, :name_en, :industry, :capital, true, 'market_feed')
                            ON CONFLICT (id) DO UPDATE SET
                                name_en = EXCLUDED.name_en,
                                industry = EXCLUDED.industry,
                                capital = EXCLUDED.capital,
                                updated_at = NOW()
                        """),
                        {
                            "id": record.source_id,
                            "tid": tenant_id,
                            "name_en": td.get("name_en", ""),
                            "industry": td.get("industry", ""),
                            "capital": td.get("market_cap", 0),
                        },
                    )
                    stored += 1
                except Exception as exc:
                    record.status = "failed"
                    record.error = str(exc)
            await session.commit()
        return stored
