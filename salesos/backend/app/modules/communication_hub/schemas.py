"""Pydantic schemas for Google Workspace integration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GoogleConnectResponse(BaseModel):
    authorization_url: str
    state: str


class GoogleCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)


class GoogleAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    provider: str
    is_active: bool
    scope: str | None = None
    avatar_url: str | None = None
    created_at: datetime
    last_sync_at: datetime | None = None
    token_expiry: datetime | None = None


class GoogleStatusResponse(BaseModel):
    connected: bool
    account: GoogleAccountResponse | None = None
    scopes_granted: list[str] = []
    token_valid: bool = False
    # Honest config gate — false when Client ID/Secret/encryption key missing.
    oauth_configured: bool = False
    config_missing: list[str] = []


class GoogleDisconnectResponse(BaseModel):
    success: bool
    message: str


class GoogleSyncRequest(BaseModel):
    days_lookback: int = Field(default=30, ge=1, le=365)
    max_results: int = Field(default=100, ge=1, le=500)


class GoogleSyncResponse(BaseModel):
    success: bool
    synced_count: int = 0
    new_count: int = 0
    updated_count: int = 0
    errors: list[str] = []
    message: str = ""


class GoogleCalendarSyncRequest(BaseModel):
    days_lookback: int = Field(default=90, ge=1, le=365)
    days_forward: int = Field(default=90, ge=1, le=365)


class GoogleCalendarSyncResponse(BaseModel):
    success: bool
    synced_count: int = 0
    new_count: int = 0
    updated_count: int = 0
    cancelled_count: int = 0
    errors: list[str] = []
    message: str = ""
