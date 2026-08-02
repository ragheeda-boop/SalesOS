"""STORY-12-02 — AI Policies engine (reuses intelligence.guardrails)."""

from __future__ import annotations

from typing import Any

from app.modules.tenant_studio.ai_policies import (
    AiPolicyError,
    AiPolicySet,
    DataClassRule,
    tier_allowed,
)
from intelligence.guardrails import (
    add_input_moderation,
    sanitize_input,
    scrub_pii_for_rag,
)


def resolve_rule(policy: AiPolicySet, data_class: str) -> DataClassRule:
    dc = (data_class or "").strip().lower()
    for rule in policy.data_class_rules:
        if rule.data_class == dc:
            return rule
    raise AiPolicyError(f"no rule for data_class: {dc}")


def evaluate_policy(
    policy: AiPolicySet,
    *,
    data_class: str,
    requested_model_tier: str,
    sample_text: str = "",
) -> dict[str, Any]:
    """Apply tenant policy + existing AI-GR primitives (no live LLM)."""
    rule = resolve_rule(policy, data_class)
    req_tier = (requested_model_tier or "economy").strip().lower()
    allowed = tier_allowed(req_tier, rule.max_model_tier)

    findings: list[str] = []
    text_out = sample_text or ""
    redactions: dict[str, int] = {}

    if policy.guardrails.get("AI-GR-001", True) and (rule.require_pii_scrub or sample_text):
        text_out = sanitize_input(text_out)
        scrubbed = scrub_pii_for_rag(text_out)
        text_out = scrubbed.text
        redactions = dict(scrubbed.redactions)
        if redactions:
            findings.append("AI-GR-001:pii_redacted")

    if (
        policy.guardrails.get("AI-GR-002", True)
        and sample_text
        and add_input_moderation(sample_text)
    ):
        findings.append("AI-GR-002:harmful_input_detected")
        allowed = False

    if policy.guardrails.get("AI-GR-004", True) and not allowed:
        findings.append(
            f"AI-GR-004:tier {req_tier} exceeds ceiling {rule.max_model_tier} for {rule.data_class}"
        )

    if policy.guardrails.get("AI-GR-005", True):
        findings.append("AI-GR-005:live_rag_blocked_feature_ai_copilot_false")

    if policy.guardrails.get("AI-GR-006", True):
        findings.append("AI-GR-006:policy_eval_recorded")

    return {
        "allowed": allowed and "AI-GR-002:harmful_input_detected" not in findings,
        "data_class": rule.data_class,
        "requested_model_tier": req_tier,
        "max_model_tier": rule.max_model_tier,
        "require_pii_scrub": rule.require_pii_scrub,
        "sanitized_preview": text_out[:500],
        "redactions": redactions,
        "findings": findings,
        "live_llm": False,
        "feature_ai_copilot": False,
    }
