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


class GoogleDisconnectResponse(BaseModel):
    success: bool
    message: str
