"""Tenant-scoped, proposal-only bridge from persisted Agent Reach evidence.

This module is an internal adapter, not an HTTP authentication boundary. A future
caller must enforce the Agent Reach permission/budget gates before invoking it.
Proposed scalar values must occur in the captured title or summary. Observations
remain cited claims and can never auto-apply.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from unicodedata import normalize
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_reach.models import ChannelType
from app.modules.company.models import Company
from app.modules.facts.service import FactPolicyRejected, FactProposalResult, FactProposalService
from domains.commercial.evidence.contracts.models import (
    ConfidenceLevel,
    EvidenceKind,
    EvidenceSource,
)
from domains.commercial.evidence.contracts.models import (
    EvidenceItem as FactEvidenceItem,
)
from domains.commercial.evidence.contracts.models import (
    EvidenceType as FactEvidenceType,
)


def _uuid(value: str | uuid.UUID, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise FactPolicyRejected(f"{label} must be a UUID") from exc


def _public_https_source_url(value: Any) -> tuple[str, str]:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise FactPolicyRejected("Agent Reach evidence requires a bounded public HTTPS source URL")
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise FactPolicyRejected("Agent Reach source URL contains whitespace or control characters")
    try:
        parsed = urlsplit(value)
        hostname = (parsed.hostname or "").rstrip(".").lower()
        port = parsed.port
    except ValueError as exc:
        raise FactPolicyRejected("Agent Reach source URL is malformed") from exc

    if (
        parsed.scheme.lower() != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or hostname == "localhost"
        or hostname.endswith((".localhost", ".local", ".internal", ".home.arpa"))
        or "%" in hostname
    ):
        raise FactPolicyRejected(
            "Agent Reach source URL must use HTTPS without credentials or reserved local host notation"
        )

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise FactPolicyRejected("Agent Reach source URL must not use a private or special IP address")

    safe_hostname = hostname
    if address is None:
        # URL stacks often accept legacy numeric IPv4 spellings such as 127.1,
        # 2130706433, and 0x7f000001 even though ipaddress rejects them.
        if re.fullmatch(
            r"(?:0[xX][0-9a-fA-F]+|[0-9]+)(?:\.(?:0[xX][0-9a-fA-F]+|[0-9]+))*",
            hostname,
        ):
            raise FactPolicyRejected("Agent Reach source URL must not use an ambiguous numeric host")
        try:
            safe_hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise FactPolicyRejected("Agent Reach source URL hostname is invalid") from exc
        labels = safe_hostname.rstrip(".").split(".")
        if "." not in safe_hostname or any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            or not re.fullmatch(r"[a-z0-9-]+", label)
            for label in labels
        ):
            raise FactPolicyRejected("Agent Reach source URL hostname is not a syntactically valid DNS name")

    # Drop query strings and fragments: they can contain tracking identifiers or
    # credentials and are not needed to identify the public source page.
    netloc = f"[{safe_hostname}]" if ":" in safe_hostname else safe_hostname
    safe_url = urlunsplit(("https", netloc, parsed.path or "/", "", ""))
    return safe_url, safe_hostname


def _fact_evidence_from_agent_row(row: Mapping[str, Any]) -> FactEvidenceItem:
    evidence_id = str(_uuid(str(row.get("id", "")), "Agent Reach evidence id"))
    safe_url, hostname = _public_https_source_url(row.get("source_url"))
    channel = str(row.get("channel", "")).strip().lower()
    supported_channels = {item.value for item in ChannelType}
    if channel not in supported_channels:
        raise FactPolicyRejected("Agent Reach evidence channel is missing or invalid")
    collected_at = row.get("collected_at")
    if not isinstance(collected_at, datetime) or collected_at.tzinfo is None:
        raise FactPolicyRejected("Agent Reach evidence must include a timezone-aware collection time")

    title = str(row.get("title") or "").strip()[:300]
    summary = str(row.get("summary") or "").strip()[:1200]
    description = " — ".join(part for part in (title, summary) if part)
    if not description:
        description = "Agent Reach captured this public source; verify the proposed value manually."

    return FactEvidenceItem(
        id=evidence_id,
        evidence_type=FactEvidenceType.MARKET_SIGNAL,
        source=EvidenceSource(
            source_domain="agent_reach",
            source_type=f"public_web_{channel}"[:64],
            source_id=evidence_id,
            source_name=hostname[:255],
        ),
        description=description,
        confidence=0.4,
        confidence_level=ConfidenceLevel.UNKNOWN,
        evidence_kind=EvidenceKind.CITED_CLAIM,
        data={
            "agent_reach_evidence_id": evidence_id,
            "channel": channel,
            "source_url": safe_url,
            "observed_at": collected_at.isoformat(),
        },
        recorded_at=collected_at,
    )


def _normalized_company_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(normalize("NFKC", value).casefold().split())


def _evidence_company_matches_company(row: Mapping[str, Any], company: Company) -> bool:
    source_name = _normalized_company_name(str(row.get("company_name") or ""))
    canonical_names = {
        _normalized_company_name(company.name_ar),
        _normalized_company_name(company.name_en),
    }
    canonical_names.discard("")
    return bool(source_name and source_name in canonical_names)


def _evidence_supports_proposed_value(row: Mapping[str, Any], proposed_value: Any) -> bool:
    """Require a bounded scalar claim to appear as a whole phrase in captured text."""
    if isinstance(proposed_value, bool) or not isinstance(proposed_value, (str, int, float)):
        return False
    claim_value = str(proposed_value).strip()
    if not claim_value or len(claim_value) > 512:
        return False
    claim = " ".join(normalize("NFKC", claim_value).casefold().split())
    captured_text = " ".join(
        normalize(
            "NFKC",
            " ".join(str(row.get(key) or "") for key in ("title", "summary")),
        )
        .casefold()
        .split()
    )
    return bool(
        captured_text
        and re.search(rf"(?<!\w){re.escape(claim)}(?!\w)", captured_text, flags=re.UNICODE)
    )


def _idempotency_token(
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    field_name: str,
    proposed_value: Any,
    evidence_id: uuid.UUID,
) -> str:
    try:
        canonical_value = json.dumps(
            proposed_value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise FactPolicyRejected("proposal value must be finite JSON") from exc
    raw = "\x1f".join(
        (str(tenant_id), str(company_id), field_name, canonical_value, str(evidence_id))
    )
    return "agent-reach-v1:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AgentReachFactProposalBridge:
    """Convert persisted Agent Reach evidence into a human-review proposal."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def propose_from_evidence(
        self,
        *,
        tenant_id: str | uuid.UUID,
        company_id: str | uuid.UUID,
        evidence_id: str | uuid.UUID,
        field_name: str,
        proposed_value: Any,
        requested_by: str | None = None,
        service_actor_id: str | None = None,
    ) -> FactProposalResult:
        tenant_uuid = _uuid(tenant_id, "tenant_id")
        company_uuid = _uuid(company_id, "company_id")
        evidence_uuid = _uuid(evidence_id, "Agent Reach evidence id")

        current_tenant = (
            await self.session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        ).scalar_one_or_none()
        if current_tenant != str(tenant_uuid):
            raise FactPolicyRejected("tenant_id must match the authenticated database tenant scope")

        result = await self.session.execute(
            text(
                """
                SELECT id::text AS id, company_name, channel, source_url, title, summary,
                       collected_at, expires_at
                FROM agent_evidence
                WHERE tenant_id = :tenant_id AND id = CAST(:evidence_id AS uuid)
                  AND (expires_at IS NULL OR expires_at > now())
                """
            ),
            {"tenant_id": str(tenant_uuid), "evidence_id": str(evidence_uuid)},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise FactPolicyRejected("Agent Reach evidence was not found in the authenticated tenant")

        company = await self.session.scalar(
            select(Company).where(
                Company.id == company_uuid,
                Company.tenant_id == tenant_uuid,
            )
        )
        if company is None:
            raise FactPolicyRejected("CRM company does not exist in the authenticated tenant")
        if not _evidence_company_matches_company(row, company):
            raise FactPolicyRejected(
                "Agent Reach evidence company name does not exactly match the target CRM company"
            )
        if not _evidence_supports_proposed_value(row, proposed_value):
            raise FactPolicyRejected(
                "Agent Reach evidence title or summary does not contain the proposed scalar value"
            )

        evidence = _fact_evidence_from_agent_row(row)
        if requested_by is not None and service_actor_id is not None:
            raise FactPolicyRejected("proposal actor must be either a human or a service principal")

        actor_type = "agent"
        actor_id = service_actor_id or f"agent_reach:evidence:{evidence_uuid}"
        if service_actor_id is not None and (
            not service_actor_id.strip() or len(service_actor_id) > 128
        ):
            raise FactPolicyRejected("service_actor_id must be a bounded non-empty identity")
        if service_actor_id is not None:
            actor_id = service_actor_id.strip()
        if requested_by is not None:
            if not isinstance(requested_by, str) or not requested_by.strip() or len(requested_by) > 128:
                raise FactPolicyRejected("requested_by must be a verified non-empty identity")
            actor_type = "human"
            actor_id = requested_by.strip()
        return await FactProposalService(self.session).propose(
            tenant_id=tenant_uuid,
            subject_type="company",
            subject_id=company_uuid,
            field_name=field_name,
            proposed_value=proposed_value,
            evidence=[evidence],
            idempotency_token=_idempotency_token(
                tenant_id=tenant_uuid,
                company_id=company_uuid,
                field_name=field_name,
                proposed_value=proposed_value,
                evidence_id=evidence_uuid,
            ),
            actor_type=actor_type,
            actor_id=actor_id,
        )
