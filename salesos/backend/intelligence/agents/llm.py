"""LLM service abstraction — now wraps the unified provider layer.

AI Foundation F1: Adds timeout, retry, circuit breaker (via ReliableProvider),
policy gate enforcement (PII, data class, provider/model allowlist), and
input sanitization for all paths including streaming.

AI Foundation F2: Canonical persistent cost tracking with pre-call budget
enforcement. Single accounting path at the service boundary. Budget checked
atomically (SELECT FOR UPDATE) before provider invocation.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from sdk.config import sdk_settings

from intelligence.providers import (
    ChatRequest,
    ChatResponse as ProviderChatResponse,
    LLMProvider,
    ProviderFactory,
    get_provider,
    StreamEvent,
    CostTracker,
    get_cost_tracker,
    init_cost_tracker,
    BudgetExceededError,
)
from intelligence.providers.reliability import ReliableProvider, ReliabilityConfig
from intelligence.providers.policy_gate import PolicyGate, PolicyGateResult
from intelligence.providers.base import estimate_cost
from intelligence.providers.observability import ai_observability, format_extra

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    cost: float = 0.0
    latency_ms: float = 0.0
    policy_findings: list[str] = field(default_factory=list)


class LLMService:
    """Unified LLM service that delegates to the provider layer.

    All agent code uses this service. Provider selection is done
    via the ProviderFactory, enabling zero-code provider switching.

    AI Foundation F1: Wraps providers with ReliableProvider for
    timeout/retry/circuit-breaker. Enforces policy gate (PII, data class,
    provider/model allowlist) on all paths.

    AI Foundation F2: Canonical cost tracking — all LLM costs are recorded
    once at the service boundary. Pre-call budget check prevents overspend.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        provider_type: str | None = None,
        cost_tracker: CostTracker | None = None,
        ai_audit_service: Any | None = None,
        reliability_config: ReliabilityConfig | None = None,
        policy_gate: PolicyGate | None = None,
    ):
        self._provider_type = provider_type
        self._model_override = model
        self._api_key_override = api_key
        self._ai_audit = ai_audit_service
        self._reliability_config = reliability_config or ReliabilityConfig()
        self._policy_gate = policy_gate or PolicyGate()
        self._reliable_provider: ReliableProvider | None = None

        try:
            self._cost_tracker = cost_tracker or get_cost_tracker()
        except RuntimeError:
            self._cost_tracker = cost_tracker

    def _get_raw_provider(self) -> LLMProvider:
        kwargs: dict[str, Any] = {}
        if self._api_key_override:
            kwargs["api_key"] = self._api_key_override
        if self._model_override:
            kwargs["model"] = self._model_override
        return get_provider(provider_type=self._provider_type, **kwargs)

    def _get_provider(self) -> ReliableProvider:
        if self._reliable_provider is None:
            raw = self._get_raw_provider()
            self._reliable_provider = ReliableProvider(raw, self._reliability_config)
        return self._reliable_provider

    async def chat(
        self,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        data_class: str = "internal",
        request_id: str | None = None,
    ) -> LLMResponse:
        provider = self._get_provider()
        resolved_model = model or self._model_override or provider.model_name

        # Policy gate: PII scrub, data class, provider/model allowlist
        input_text = ""
        if system:
            input_text += system + "\n"
        if messages:
            for msg in messages:
                input_text += msg.get("content", "") + "\n"

        gate_result = self._policy_gate.check_input(
            text=input_text,
            data_class=data_class,
            provider=provider.provider_name,
            model=resolved_model,
        )

        if not gate_result.allowed:
            return LLMResponse(
                content="",
                model=resolved_model,
                finish_reason="error",
                policy_findings=gate_result.findings,
            )

        # Apply sanitized text back to messages
        if gate_result.sanitized_text and messages:
            sanitized_msgs = []
            for msg in messages:
                sanitized_msgs.append({**msg, "content": gate_result.sanitized_text})
            messages = sanitized_msgs

        request = ChatRequest(
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=resolved_model,
            response_format=response_format,
            tools=tools,
            tenant_id=tenant_id,
            request_id=request_id,
        )

        # ── F2: Pre-call budget check ─────────────────────────────
        if tenant_id and self._cost_tracker:
            est_cost = estimate_cost(resolved_model, 500, 500)
            budget_check = await self._cost_tracker.check_budget(
                tenant_id, est_cost
            )
            if budget_check.would_exceed and budget_check.monthly_budget > 0:
                return LLMResponse(
                    content="",
                    model=resolved_model,
                    finish_reason="error",
                    cost=0.0,
                    policy_findings=[
                        f"Budget exceeded: ${budget_check.current_spend:.4f} / "
                        f"${budget_check.monthly_budget:.2f}"
                    ],
                )

        start = time.monotonic()
        response: ProviderChatResponse = await provider.chat(request)
        elapsed = (time.monotonic() - start) * 1000

        # ── F2: Canonical cost tracking ───────────────────────────
        if tenant_id and self._cost_tracker:
            try:
                await self._cost_tracker.track(
                    tenant_id=tenant_id,
                    provider=provider.provider_name,
                    model=response.model,
                    prompt_tokens=response.usage.get("prompt_tokens", 0),
                    completion_tokens=response.usage.get("completion_tokens", 0),
                    operation="chat",
                    user_id=user_id,
                    latency_ms=round(elapsed, 2),
                )
                await self._cost_tracker.deduct_budget(tenant_id, response.cost)

                # ── F3: Record observability metrics ──────────────
                ai_observability.record_llm_call(
                    provider=provider.provider_name,
                    model=response.model,
                    operation="chat",
                    status="success",
                    latency_ms=round(elapsed, 2),
                )
                ai_observability.record_tokens(
                    provider=provider.provider_name,
                    model=response.model,
                    prompt_tokens=response.usage.get("prompt_tokens", 0),
                    completion_tokens=response.usage.get("completion_tokens", 0),
                )
                ai_observability.record_cost(
                    provider=provider.provider_name,
                    model=response.model,
                    cost=response.cost,
                )
            except Exception:
                pass

        if self._ai_audit and tenant_id and user_id:
            try:
                await self._ai_audit.log_llm_call(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    model=response.model,
                    prompt_tokens=response.usage.get("prompt_tokens", 0),
                    completion_tokens=response.usage.get("completion_tokens", 0),
                    total_tokens=response.usage.get("total_tokens", 0),
                    cost=response.cost,
                    operation="completion",
                )
            except Exception:
                pass

        return LLMResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
            finish_reason=response.finish_reason.value,
            cost=response.cost,
            latency_ms=round(elapsed, 2),
            policy_findings=gate_result.findings,
        )

    async def chat_stream(
        self,
        system: str | None = None,
        messages: list[dict[str, str]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        data_class: str = "internal",
        tenant_id: str | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
    ) -> AsyncIterator[StreamEvent]:
        provider = self._get_provider()
        resolved_model = model or self._model_override or provider.model_name

        # Policy gate on streaming path (F1-5: close bypass)
        gate_result = self._policy_gate.check_stream_input(
            system=system,
            messages=messages,
            data_class=data_class,
            provider=provider.provider_name,
            model=resolved_model,
        )

        if not gate_result.allowed:
            yield StreamEvent(type="error", error=f"Policy blocked: {gate_result.blocked_reason}")
            return

        # ── F2: Pre-call budget check for streaming ───────────────
        if tenant_id and self._cost_tracker:
            est_cost = estimate_cost(resolved_model, 500, 500)
            budget_check = await self._cost_tracker.check_budget(
                tenant_id, est_cost
            )
            if budget_check.would_exceed and budget_check.monthly_budget > 0:
                yield StreamEvent(
                    type="error",
                    error=f"Budget exceeded: ${budget_check.current_spend:.4f} / ${budget_check.monthly_budget:.2f}",
                )
                return

        request = ChatRequest(
            system=system,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=resolved_model,
            stream=True,
            request_id=request_id,
        )

        total_content = ""
        start = time.monotonic()
        async for event in provider.chat_stream(request):
            if event.type == "content" and event.content:
                total_content += event.content
            elif event.type == "done":
                elapsed = (time.monotonic() - start) * 1000
                # ── F2: Track cost for streaming ──────────────────
                if tenant_id and self._cost_tracker:
                    try:
                        est = estimate_cost(resolved_model, 500, max(len(total_content) // 4, 50))
                        await self._cost_tracker.track(
                            tenant_id=tenant_id,
                            provider=provider.provider_name,
                            model=resolved_model,
                            prompt_tokens=500,
                            completion_tokens=max(len(total_content) // 4, 50),
                            operation="chat_stream",
                            user_id=user_id,
                            latency_ms=round(elapsed, 2),
                        )
                        await self._cost_tracker.deduct_budget(tenant_id, est)
                        # ── F3: Record observability metrics ──────
                        ai_observability.record_llm_call(
                            provider=provider.provider_name,
                            model=resolved_model,
                            operation="chat_stream",
                            status="success",
                            latency_ms=round(elapsed, 2),
                        )
                    except Exception:
                        pass
            yield event

    async def embed(self, text: str, model: str | None = None, tenant_id: str | None = None, request_id: str | None = None) -> list[float]:
        from intelligence.providers import EmbeddingRequest
        provider = self._get_provider()
        request = EmbeddingRequest(text=text, model=model, request_id=request_id)

        # ── F2: Pre-call budget check for embeddings ──────────────
        resolved_model = model or provider.model_name
        if tenant_id and self._cost_tracker:
            est_cost = estimate_cost(resolved_model, 200, 0)
            budget_check = await self._cost_tracker.check_budget(
                tenant_id, est_cost
            )
            if budget_check.would_exceed and budget_check.monthly_budget > 0:
                return []

        start = time.monotonic()
        response = await provider.embed(request)
        elapsed = (time.monotonic() - start) * 1000

        # ── F2: Canonical cost tracking for embeddings ────────────
        if tenant_id and self._cost_tracker:
            try:
                await self._cost_tracker.track(
                    tenant_id=tenant_id,
                    provider=provider.provider_name,
                    model=response.model,
                    prompt_tokens=response.usage.get("prompt_tokens", 0),
                    completion_tokens=0,
                    operation="embed",
                    latency_ms=round(elapsed, 2),
                )
                await self._cost_tracker.deduct_budget(tenant_id, response.cost)
                # ── F3: Record observability metrics ──────────────
                ai_observability.record_llm_call(
                    provider=provider.provider_name,
                    model=response.model,
                    operation="embed",
                    status="success",
                    latency_ms=round(elapsed, 2),
                )
            except Exception:
                pass

        if isinstance(response.embedding, list) and response.embedding and isinstance(response.embedding[0], float):
            return response.embedding
        return response.embedding[0] if isinstance(response.embedding, list) and response.embedding else []
