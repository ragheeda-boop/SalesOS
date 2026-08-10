"""AI Foundation F1 — Policy gate: PII, data classification, provider/model allowlist.

Enforced at the LLM call boundary (LLMService) before reaching providers.
All providers pass through the same policy boundary.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from intelligence.guardrails import (
    add_input_moderation,
    detect_pii_leakage,
    sanitize_input,
    scrub_pii_for_rag,
)
from .observability import ai_observability, format_extra

logger = logging.getLogger(__name__)


# ── Data Classification ────────────────────────────────────────────

MODEL_TIER_RANK: dict[str, int] = {"economy": 0, "standard": 1, "full": 2}


@dataclass(frozen=True)
class DataClassRule:
    """Maps a data classification to an allowed model tier ceiling."""

    data_class: str
    max_model_tier: str
    require_pii_scrub: bool = True


DEFAULT_DATA_CLASS_RULES: list[DataClassRule] = [
    DataClassRule("public", "full", require_pii_scrub=False),
    DataClassRule("internal", "standard", require_pii_scrub=True),
    DataClassRule("pii", "economy", require_pii_scrub=True),
    DataClassRule("confidential", "economy", require_pii_scrub=True),
]


def get_model_tier(model: str) -> str:
    """Infer model tier from model name."""
    m = model.lower()
    if any(k in m for k in ("claude-3-5-sonnet", "claude-3-opus", "gemini-1.5-pro")):
        return "full"
    if m.startswith("gpt-4o") and "mini" not in m:
        return "full"
    if any(k in m for k in ("gpt-4o-mini", "claude-3-5-haiku", "gemini-1.5-flash", "gpt-3.5")):
        return "standard"
    if any(k in m for k in ("llama", "mistral", "ollama", "phi")):
        return "economy"
    return "standard"


def tier_allowed(requested_tier: str, ceiling_tier: str) -> bool:
    return MODEL_TIER_RANK.get(requested_tier, 0) <= MODEL_TIER_RANK.get(ceiling_tier, 0)


# ── Provider/Model Allowlist ───────────────────────────────────────

@dataclass
class ProviderModelPolicy:
    """Tenant-level allowlist for providers and models.

    Empty allowed_providers/allowed_models means ALL are allowed.
    blocked_providers/blocked_models always deny regardless of allowlist.
    """

    allowed_providers: set[str] = field(default_factory=set)
    blocked_providers: set[str] = field(default_factory=set)
    allowed_models: set[str] = field(default_factory=set)
    blocked_models: set[str] = field(default_factory=set)

    def is_provider_allowed(self, provider: str) -> bool:
        if provider in self.blocked_providers:
            return False
        if self.allowed_providers and provider not in self.allowed_providers:
            return False
        return True

    def is_model_allowed(self, model: str) -> bool:
        if model in self.blocked_models:
            return False
        if self.allowed_models and model not in self.allowed_models:
            return False
        return True


# ── Policy Gate Result ─────────────────────────────────────────────

@dataclass
class PolicyGateResult:
    allowed: bool = True
    sanitized_text: str = ""
    redactions: dict[str, int] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)
    blocked_reason: str = ""


# ── Policy Gate ────────────────────────────────────────────────────

class PolicyGate:
    """Enforces PII scrubbing, data classification, and provider/model policy.

    Called by LLMService before every LLM request. All providers pass
    through the same gate — no duplication across providers.
    """

    def __init__(
        self,
        data_class_rules: list[DataClassRule] | None = None,
        provider_model_policy: ProviderModelPolicy | None = None,
        enforce_pii: bool = True,
        enforce_data_class: bool = True,
        enforce_provider_policy: bool = True,
    ):
        self._rules = {r.data_class: r for r in (data_class_rules or DEFAULT_DATA_CLASS_RULES)}
        self._policy = provider_model_policy or ProviderModelPolicy()
        self._enforce_pii = enforce_pii
        self._enforce_data_class = enforce_data_class
        self._enforce_provider_policy = enforce_provider_policy

    def check_input(
        self,
        text: str,
        data_class: str = "internal",
        provider: str = "",
        model: str = "",
    ) -> PolicyGateResult:
        """Validate and scrub input before LLM call."""
        result = PolicyGateResult()

        # 1. Input sanitization (prompt injection)
        sanitized = sanitize_input(text)
        if sanitized != text:
            result.findings.append("input_sanitized")
        result.sanitized_text = sanitized

        # 2. Harmful content moderation
        if add_input_moderation(sanitized):
            result.allowed = False
            result.blocked_reason = "harmful_input_detected"
            result.findings.append("harmful_input_blocked")
            ai_observability.record_policy_block("harmful_input")
            logger.warning(
                "Policy gate blocked harmful input",
                extra=format_extra(
                    event="policy_block",
                    reason="harmful_input",
                    data_class=data_class,
                ),
            )
            return result

        # 3. PII scrubbing
        if self._enforce_pii:
            rule = self._rules.get(data_class, self._rules.get("internal"))
            if rule and rule.require_pii_scrub:
                scrubbed = scrub_pii_for_rag(sanitized)
                result.sanitized_text = scrubbed.text
                result.redactions = dict(scrubbed.redactions)
                if scrubbed.redaction_count > 0:
                    result.findings.append(f"pii_redacted:{scrubbed.redaction_count}")

            # Post-scrub PII check
            remaining = detect_pii_leakage(result.sanitized_text)
            if remaining:
                result.findings.append(f"pii_remaining:{','.join(remaining)}")

        # 4. Data class -> model tier enforcement
        if self._enforce_data_class and model:
            rule = self._rules.get(data_class, self._rules.get("internal"))
            if rule:
                requested_tier = get_model_tier(model)
                if not tier_allowed(requested_tier, rule.max_model_tier):
                    result.allowed = False
                    result.blocked_reason = (
                        f"model_tier_{requested_tier}_exceeds_ceiling_{rule.max_model_tier}_for_{data_class}"
                    )
                    result.findings.append(result.blocked_reason)
                    ai_observability.record_policy_block("model_tier")
                    logger.warning(
                        "Policy gate blocked model tier",
                        extra=format_extra(
                            event="policy_block",
                            reason="model_tier",
                            data_class=data_class,
                            model=model,
                            requested_tier=requested_tier,
                            ceiling=rule.max_model_tier,
                        ),
                    )
                    return result

        # 5. Provider/model allowlist
        if self._enforce_provider_policy:
            if provider and not self._policy.is_provider_allowed(provider):
                result.allowed = False
                result.blocked_reason = f"provider_{provider}_not_allowed"
                result.findings.append(result.blocked_reason)
                ai_observability.record_policy_block("provider_denied")
                logger.warning(
                    "Policy gate blocked provider",
                    extra=format_extra(
                        event="policy_block",
                        reason="provider_denied",
                        provider=provider,
                    ),
                )
                return result
            if model and not self._policy.is_model_allowed(model):
                result.allowed = False
                result.blocked_reason = f"model_{model}_not_allowed"
                result.findings.append(result.blocked_reason)
                ai_observability.record_policy_block("model_denied")
                logger.warning(
                    "Policy gate blocked model",
                    extra=format_extra(
                        event="policy_block",
                        reason="model_denied",
                        model=model,
                    ),
                )
                return result

        return result

    def check_stream_input(
        self,
        system: str | None,
        messages: list[dict[str, str]] | None,
        data_class: str = "internal",
        provider: str = "",
        model: str = "",
    ) -> PolicyGateResult:
        """Validate input for streaming path (applies same governance)."""
        parts: list[str] = []
        if system:
            parts.append(system)
        if messages:
            for msg in messages:
                parts.append(msg.get("content", ""))
        combined = "\n".join(parts)
        return self.check_input(combined, data_class, provider, model)
