from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    domain: str | None = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None
    plan: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    full_name_ar: str | None = None
    tenant_id: UUID | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    full_name_ar: str | None
    role: str
    is_active: bool
    is_verified: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    tenant_id: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern=r"^(admin|manager|user)$")


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="user", pattern=r"^(admin|manager|user)$")
