"""STORY-11-09b — Compliant partner channel senders (LinkedIn + WhatsApp).

LinkedIn via compliant partner API shape only — no browser/ToS-risk automation.
WhatsApp via Business-API-shaped partner port. Live network sends not claimed.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.modules.gtm.sequencing import SequenceStep, SequencingError

# Forbidden automation modes (ToS-risk) — rejected at send time.
FORBIDDEN_AUTOMATION_MODES: frozenset[str] = frozenset(
    {
        "browser_automation",
        "scraping",
        "unofficial_api",
        "session_cookie",
        "selenium",
        "puppeteer",
    }
)


@dataclass(frozen=True)
class ChannelSendResult:
    ok: bool
    channel: str
    provider_key: str
    external_message_id: str = ""
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "channel": self.channel,
            "provider_key": self.provider_key,
            "external_message_id": self.external_message_id,
            "message": self.message,
        }


@runtime_checkable
class CompliantChannelSender(Protocol):
    """Partner-API-shaped channel sender — swappable, no ToS-risk automation."""

    @property
    def channel(self) -> str: ...

    @property
    def provider_key(self) -> str: ...

    async def send(
        self,
        *,
        step: SequenceStep,
        contact_email: str,
        contact_handles: dict[str, str],
        mode: str = "partner_api",
    ) -> ChannelSendResult: ...


def assert_compliant_mode(mode: str) -> None:
    m = (mode or "").strip().lower() or "partner_api"
    if m in FORBIDDEN_AUTOMATION_MODES:
        raise SequencingError(
            f"forbidden channel mode {m!r}: LinkedIn/WhatsApp require compliant "
            "partner API only (no ToS-risk automation)"
        )
    if m not in ("partner_api", "recorded", "email_recorded"):
        raise SequencingError(f"unsupported channel mode {m!r}")


@dataclass
class MemEmailRecordedSender:
    """Email channel: record-only (no live SMTP)."""

    key: str = "email_recorded"
    sent: list[dict[str, Any]] = field(default_factory=list)

    @property
    def channel(self) -> str:
        return "email"

    @property
    def provider_key(self) -> str:
        return self.key

    async def send(
        self,
        *,
        step: SequenceStep,
        contact_email: str,
        contact_handles: dict[str, str],
        mode: str = "email_recorded",
    ) -> ChannelSendResult:
        _ = contact_handles
        assert_compliant_mode(mode if mode != "partner_api" else "email_recorded")
        msg_id = f"email-{len(self.sent) + 1}"
        self.sent.append(
            {"to": contact_email, "subject": step.subject, "body": step.body, "id": msg_id}
        )
        return ChannelSendResult(
            ok=True,
            channel="email",
            provider_key=self.key,
            external_message_id=msg_id,
            message="recorded (no live SMTP)",
        )


@dataclass
class MemLinkedInPartnerSender:
    """LinkedIn via compliant partner API shape (CI fake — not live network)."""

    key: str = "linkedin_partner_fake"
    sent: list[dict[str, Any]] = field(default_factory=list)

    @property
    def channel(self) -> str:
        return "linkedin"

    @property
    def provider_key(self) -> str:
        return self.key

    async def send(
        self,
        *,
        step: SequenceStep,
        contact_email: str,
        contact_handles: dict[str, str],
        mode: str = "partner_api",
    ) -> ChannelSendResult:
        assert_compliant_mode(mode)
        urn = (contact_handles.get("linkedin") or "").strip()
        if not urn:
            raise SequencingError("linkedin step requires contact_handles.linkedin (member URN)")
        if not urn.startswith("urn:") and not urn.startswith("linkedin:"):
            raise SequencingError(
                "linkedin handle must be partner URN (urn:… or linkedin:…) — "
                "not a profile scrape URL"
            )
        msg_id = f"li-{len(self.sent) + 1}"
        self.sent.append(
            {
                "urn": urn,
                "email": contact_email,
                "subject": step.subject,
                "body": step.body,
                "id": msg_id,
            }
        )
        return ChannelSendResult(
            ok=True,
            channel="linkedin",
            provider_key=self.key,
            external_message_id=msg_id,
            message="partner_api recorded (live LinkedIn not claimed)",
        )


@dataclass
class MemWhatsAppPartnerSender:
    """WhatsApp Business-API-shaped partner port (CI fake — not live network)."""

    key: str = "whatsapp_partner_fake"
    sent: list[dict[str, Any]] = field(default_factory=list)

    @property
    def channel(self) -> str:
        return "whatsapp"

    @property
    def provider_key(self) -> str:
        return self.key

    async def send(
        self,
        *,
        step: SequenceStep,
        contact_email: str,
        contact_handles: dict[str, str],
        mode: str = "partner_api",
    ) -> ChannelSendResult:
        assert_compliant_mode(mode)
        phone = (contact_handles.get("whatsapp") or "").strip()
        if not phone:
            raise SequencingError("whatsapp step requires contact_handles.whatsapp (E.164)")
        if not phone.startswith("+") or len(phone) < 8:
            raise SequencingError("whatsapp handle must be E.164 (+…)")
        msg_id = f"wa-{len(self.sent) + 1}"
        self.sent.append(
            {
                "to": phone,
                "email": contact_email,
                "body": step.body or step.subject,
                "id": msg_id,
            }
        )
        return ChannelSendResult(
            ok=True,
            channel="whatsapp",
            provider_key=self.key,
            external_message_id=msg_id,
            message="partner_api recorded (live WhatsApp not claimed)",
        )


def build_default_channel_senders() -> dict[str, CompliantChannelSender]:
    return {
        "email": MemEmailRecordedSender(),
        "linkedin": MemLinkedInPartnerSender(),
        "whatsapp": MemWhatsAppPartnerSender(),
    }
