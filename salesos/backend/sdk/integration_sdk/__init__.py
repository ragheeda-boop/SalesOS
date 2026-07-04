"""Integration SDK — connect external systems to SalesOS.

Provides:
  - Webhook builder (incoming/outgoing)
  - API client factory (REST, GraphQL, gRPC)
  - Auth handler (OAuth2, API Key, Basic, JWT)
  - Data mapper (transform external data to UBOM entities)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class AuthType(str, Enum):
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    NONE = "none"


class IntegrationDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class AuthConfig:
    type: AuthType = AuthType.NONE
    credentials: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type.value, "has_credentials": bool(self.credentials)}


@dataclass
class WebhookDefinition:
    id: str
    name: str
    direction: IntegrationDirection = IntegrationDirection.INBOUND
    url: Optional[str] = None  # For outbound: target URL
    events: list[str] = field(default_factory=list)  # Event IDs to subscribe to
    auth: AuthConfig = field(default_factory=AuthConfig)
    mapper: Optional[Callable] = None  # Data transformation function
    schema: Optional[dict] = None  # Expected payload schema

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "direction": self.direction.value,
            "url": self.url,
            "events": self.events,
            "auth": self.auth.to_dict(),
            "schema": self.schema,
        }


@dataclass
class IntegrationConfig:
    id: str
    name: str
    provider: str  # e.g. "hubspot", "salesforce", "zoho", "custom"
    version: str = "1.0.0"
    auth: AuthConfig = field(default_factory=AuthConfig)
    webhooks: list[WebhookDefinition] = field(default_factory=list)
    entity_mappings: dict = field(default_factory=dict)  # external -> UBOM field mapping
    enabled: bool = True
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "version": self.version,
            "auth": self.auth.to_dict(),
            "webhooks": [w.to_dict() for w in self.webhooks],
            "entity_mappings": self.entity_mappings,
            "enabled": self.enabled,
        }
