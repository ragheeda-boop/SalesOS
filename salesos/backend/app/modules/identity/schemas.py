import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


_COMMON_PASSWORDS: frozenset[str] = frozenset({
    "password", "12345678", "123456789", "1234567890",
    "12345678901", "123456789012", "qwerty123", "qwerty12",
    "admin123", "admin12345", "password123", "letmein123",
    "welcome123", "changeme123", "salesos123", "muhide123",
    "باسورد", "123456789", "١٢٣٤٥٦٧٨٩", "admin",
    "administrator", "root12345", "test12345",
})


def validate_password_strength(password: str) -> str:
    """Validate password meets complexity requirements.

    Returns the password if valid, raises ValueError with bilingual message otherwise.
    """
    if len(password) < 12:
        raise ValueError(
            "Password must be at least 12 characters long | "
            "يجب أن تتكون كلمة المرور من 12 حرفًا على الأقل"
        )
    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must contain at least one uppercase letter | "
            "يجب أن تحتوي كلمة المرور على حرف كبير واحد على الأقل"
        )
    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must contain at least one lowercase letter | "
            "يجب أن تحتوي كلمة المرور على حرف صغير واحد على الأقل"
        )
    if not re.search(r"\d", password):
        raise ValueError(
            "Password must contain at least one digit | "
            "يجب أن تحتوي كلمة المرور على رقم واحد على الأقل"
        )
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", password):
        raise ValueError(
            "Password must contain at least one special character (!@#$%^&*) | "
            "يجب أن تحتوي كلمة المرور على رمز خاص واحد على الأقل"
        )
    if password.lower() in _COMMON_PASSWORDS:
        raise ValueError(
            "This password is too common. Please choose a stronger password | "
            "كلمة المرور هذه شائعة جدًا. يرجى اختيار كلمة مرور أقوى"
        )
    return password


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
    password: str = Field(..., min_length=12, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    full_name_ar: str | None = None
    tenant_id: UUID | None = None

    @model_validator(mode="after")
    def validate_password(self) -> "UserCreate":
        validate_password_strength(self.password)
        return self


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


class TokenCookies(BaseModel):
    refresh_token: str
    csrf_token: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    session_id: str | None = None
    all_sessions: bool = False


class SessionResponse(BaseModel):
    id: str
    device_name: str
    device_type: str
    ip_address: str
    last_used_at: datetime
    created_at: datetime
    expires_at: datetime
    is_active: bool


class LogoutResponse(BaseModel):
    message: str
    sessions_revoked: int = 0


class CsrfTokenResponse(BaseModel):
    csrf_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @model_validator(mode="after")
    def validate_password(self) -> "PasswordChangeRequest":
        validate_password_strength(self.new_password)
        return self


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern=r"^(admin|manager|user)$")


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="user", pattern=r"^(admin|manager|user)$")
