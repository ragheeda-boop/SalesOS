"""STORY-11-06 — CAP-100 Contact Verification models.

Commodity verification behind a single swappable connector interface.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

VerificationChannel = Literal["email", "phone"]
VerificationStatus = Literal["valid", "invalid", "unknown", "risky"]


class VerificationError(ValueError):
    """Invalid verification request or connector input."""


@dataclass
class VerificationRequest:
    """Contact verification seed (email and/or phone)."""

    email: str = ""
    phone: str = ""
    # Optional provider override (connector_key). Empty = default bound connector.
    provider_key: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "phone": self.phone,
            "provider_key": self.provider_key,
        }

    @property
    def channels(self) -> list[str]:
        out: list[str] = []
        if self.email:
            out.append("email")
        if self.phone:
            out.append("phone")
        return out


@dataclass(frozen=True)
class ChannelVerdict:
    channel: str
    value: str
    status: str
    confidence: float = 0.0
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "value": self.value,
            "status": self.status,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class VerificationResult:
    """OBJ-354-shaped verification run (in-memory)."""

    id: str
    tenant_id: str
    request: VerificationRequest
    verdicts: list[ChannelVerdict] = field(default_factory=list)
    provider_key: str = ""
    schema_version: int = 1
    created_at: str = ""

    @property
    def overall_status(self) -> str:
        if not self.verdicts:
            return "unknown"
        statuses = {v.status for v in self.verdicts}
        if statuses == {"valid"}:
            return "valid"
        if "invalid" in statuses:
            return "invalid"
        if "risky" in statuses:
            return "risky"
        return "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "request": self.request.as_dict(),
            "verdicts": [v.as_dict() for v in self.verdicts],
            "provider_key": self.provider_key,
            "overall_status": self.overall_status,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
        }


def normalize_request(
    *,
    email: str | None = None,
    phone: str | None = None,
    provider_key: str | None = None,
) -> VerificationRequest:
    em = (email or "").strip().lower()
    ph = (phone or "").strip()
    if not em and not ph:
        raise VerificationError("email or phone required")
    if em and "@" not in em:
        raise VerificationError("email must contain @")
    return VerificationRequest(
        email=em,
        phone=ph,
        provider_key=(provider_key or "").strip(),
    )
