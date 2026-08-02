"""STORY-11-06 — Contact Verification connector + engine (CAP-100).

Single VerificationConnector interface — commodity swap-in.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.modules.gtm.verification import (
    ChannelVerdict,
    VerificationError,
    VerificationRequest,
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s]{6,20}$")


@runtime_checkable
class VerificationConnector(Protocol):
    """Commodity verification adapter — single interface, swappable impl."""

    @property
    def connector_key(self) -> str:
        """Stable connector id (e.g. ``fake_verify``) — not a secret."""
        ...

    async def verify(self, request: VerificationRequest) -> list[ChannelVerdict]:
        """Return per-channel verdicts for the request."""
        ...


@dataclass
class MemVerificationConnector:
    """In-memory fake verifier for CI / pilot scaffolding.

    Rules (deterministic, not a live vendor):
    - email ending ``@invalid.test`` → invalid
    - email containing ``risky`` → risky
    - otherwise syntactically valid email → valid
    - phone matching E.164-ish pattern → valid; else invalid
    """

    key: str = "fake_verify"
    # Optional overrides: normalized value → status
    email_overrides: dict[str, str] = field(default_factory=dict)
    phone_overrides: dict[str, str] = field(default_factory=dict)

    @property
    def connector_key(self) -> str:
        return self.key

    async def verify(self, request: VerificationRequest) -> list[ChannelVerdict]:
        if not isinstance(request, VerificationRequest):
            raise VerificationError("request required")
        verdicts: list[ChannelVerdict] = []
        if request.email:
            verdicts.append(self._verify_email(request.email))
        if request.phone:
            verdicts.append(self._verify_phone(request.phone))
        if not verdicts:
            raise VerificationError("email or phone required")
        return verdicts

    def _verify_email(self, email: str) -> ChannelVerdict:
        if email in self.email_overrides:
            status = self.email_overrides[email]
            return ChannelVerdict(
                channel="email",
                value=email,
                status=status,
                confidence=0.9,
                reason="override",
            )
        if email.endswith("@invalid.test"):
            return ChannelVerdict(
                channel="email",
                value=email,
                status="invalid",
                confidence=0.95,
                reason="invalid.test sink",
            )
        if "risky" in email:
            return ChannelVerdict(
                channel="email",
                value=email,
                status="risky",
                confidence=0.7,
                reason="risky token",
            )
        if not _EMAIL_RE.match(email):
            return ChannelVerdict(
                channel="email",
                value=email,
                status="invalid",
                confidence=0.99,
                reason="syntax",
            )
        return ChannelVerdict(
            channel="email",
            value=email,
            status="valid",
            confidence=0.8,
            reason="syntax_ok",
        )

    def _verify_phone(self, phone: str) -> ChannelVerdict:
        compact = phone.replace(" ", "").replace("-", "")
        if compact in self.phone_overrides or phone in self.phone_overrides:
            status = self.phone_overrides.get(compact) or self.phone_overrides[phone]
            return ChannelVerdict(
                channel="phone",
                value=phone,
                status=status,
                confidence=0.9,
                reason="override",
            )
        if not _PHONE_RE.match(phone):
            return ChannelVerdict(
                channel="phone",
                value=phone,
                status="invalid",
                confidence=0.99,
                reason="syntax",
            )
        return ChannelVerdict(
            channel="phone",
            value=phone,
            status="valid",
            confidence=0.75,
            reason="syntax_ok",
        )


async def run_verification(
    request: VerificationRequest,
    connector: VerificationConnector,
) -> list[ChannelVerdict]:
    if not isinstance(connector, VerificationConnector):
        raise VerificationError("connector must implement VerificationConnector")
    return await connector.verify(request)
