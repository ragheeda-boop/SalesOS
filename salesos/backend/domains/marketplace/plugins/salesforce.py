"""Salesforce connector plugin — sync contacts and deals with Salesforce."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from domains.marketplace.manifest_schema import PluginManifest


SALESFORCE_MANIFEST: dict[str, Any] = {
    "id": "salesos-salesforce",
    "name": "Salesforce Connector",
    "version": "1.0.0",
    "description": "Sync contacts and deals between SalesOS and Salesforce. "
                   "Bidirectional sync with conflict resolution.",
    "author": "SalesOS",
    "license": "MIT",
    "icon": "https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/salesforce.svg",
    "tags": ["crm", "sync", "contacts", "deals"],
    "permissions": ["company:read", "company:write", "contact:read", "contact:write"],
    "hooks": [
        "after.company.created",
        "after.company.updated",
        "after.company.merged",
    ],
    "dependencies": [],
    "config_schema": {
        "type": "object",
        "required": ["client_id", "client_secret", "username", "password", "security_token"],
        "properties": {
            "client_id": {
                "type": "string",
                "description": "Salesforce Connected App Client ID",
            },
            "client_secret": {
                "type": "string",
                "description": "Salesforce Connected App Client Secret",
            },
            "username": {
                "type": "string",
                "description": "Salesforce username",
            },
            "password": {
                "type": "string",
                "description": "Salesforce password",
            },
            "security_token": {
                "type": "string",
                "description": "Salesforce security token",
            },
            "login_url": {
                "type": "string",
                "description": "Salesforce login URL",
                "default": "https://login.salesforce.com",
            },
            "sync_direction": {
                "type": "string",
                "enum": ["bidirectional", "salesos_to_salesforce", "salesforce_to_salesos"],
                "description": "Sync direction",
                "default": "bidirectional",
            },
            "sync_interval_minutes": {
                "type": "integer",
                "description": "Auto-sync interval in minutes",
                "default": 15,
                "minimum": 5,
            },
            "field_mappings": {
                "type": "object",
                "description": "Custom field mappings between SalesOS and Salesforce",
                "default": {},
            },
        },
    },
    "resource_limits": {
        "max_calls_per_sec": 30,
        "max_memory_mb": 100,
        "max_timeout_ms": 30000,
    },
}


@dataclass
class SalesforceSyncRecord:
    external_id: str = ""
    salesos_id: str = ""
    object_type: str = ""  # Contact, Account, Opportunity
    last_synced_at: datetime | None = None
    sync_direction: str = "bidirectional"
    conflict_resolution: str = "salesos_wins"  # or "salesforce_wins" or "manual"
    checksum: str = ""
    sync_status: str = "pending"  # pending, synced, conflict, error

    def compute_checksum(self, data: dict) -> str:
        raw = json.dumps(data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "external_id": self.external_id,
            "salesos_id": self.salesos_id,
            "object_type": self.object_type,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "sync_direction": self.sync_direction,
            "conflict_resolution": self.conflict_resolution,
            "sync_status": self.sync_status,
        }


class SalesforceClient:
    """Minimal Salesforce REST API client for sync operations."""

    def __init__(self, config: dict):
        self._config = config
        self._access_token: str | None = None
        self._instance_url: str | None = None

    async def _authenticate(self) -> dict:
        import httpx

        login_url = self._config.get("login_url", "https://login.salesforce.com")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{login_url}/services/oauth2/token",
                data={
                    "grant_type": "password",
                    "client_id": self._config["client_id"],
                    "client_secret": self._config["client_secret"],
                    "username": self._config["username"],
                    "password": self._config["password"] + self._config.get("security_token", ""),
                },
            )
        if resp.status_code != 200:
            raise ValueError(f"Salesforce auth failed: {resp.text}")
        data = resp.json()
        self._access_token = data["access_token"]
        self._instance_url = data["instance_url"]
        return data

    async def query(self, soql: str) -> list[dict]:
        if not self._access_token:
            await self._authenticate()
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self._instance_url}/services/data/v58.0/query",
                params={"q": soql},
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
        if resp.status_code != 200:
            raise ValueError(f"Salesforce query failed: {resp.text}")
        return resp.json().get("records", [])

    async def create_record(self, object_type: str, data: dict) -> str:
        if not self._access_token:
            await self._authenticate()
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._instance_url}/services/data/v58.0/sobjects/{object_type}",
                json=data,
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
        if resp.status_code not in (200, 201):
            raise ValueError(f"Salesforce create failed: {resp.text}")
        return resp.json()["id"]

    async def update_record(self, object_type: str, record_id: str, data: dict) -> None:
        if not self._access_token:
            await self._authenticate()
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.patch(
                f"{self._instance_url}/services/data/v58.0/sobjects/{object_type}/{record_id}",
                json=data,
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
        if resp.status_code not in (200, 204):
            raise ValueError(f"Salesforce update failed: {resp.text}")

    async def delete_record(self, object_type: str, record_id: str) -> None:
        if not self._access_token:
            await self._authenticate()
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(
                f"{self._instance_url}/services/data/v58.0/sobjects/{object_type}/{record_id}",
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
        if resp.status_code not in (200, 204):
            raise ValueError(f"Salesforce delete failed: {resp.text}")


import json  # noqa: E402 (used by compute_checksum)
