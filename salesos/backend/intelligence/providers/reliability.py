"""AI Foundation F1 — Provider reliability: timeout, retry, circuit breaker.

All providers pass through these primitives. Configuration-driven,
no hardcoded values in business logic.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import ChatRequest, ChatResponse, EmbeddingRequest, EmbeddingResponse, FinishReason, StreamEvent
from .protocol import LLMProvider

logger = logging.getLogger(__name__)


# ── Error Classification ──────────────────────────────────────────

class ErrorClass(str, Enum):
    RETRYABLE = "retryable"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


_RETRYABLE_EXCEPTION_TYPES: tuple[type[Exception], ...] = (
    asyncio.TimeoutError,
    ConnectionError,
    ConnectionRefusedError,
    ConnectionResetError,
)

_RETRYABLE_FINISH_REASONS: set[FinishReason] = {
    FinishReason.ERROR,
}

_PERMANENT_FINISH_REASONS: set[FinishReason] = {
    FinishReason.CONTENT_FILTER,
}


def classify_error(exc: Exception | None, response: ChatResponse | None = None) -> ErrorClass:
    """Classify whether a failure is retryable."""
    if exc is not None:
        if isinstance(exc, _RETRYABLE_EXCEPTION_TYPES):
            return ErrorClass.RETRYABLE
        exc_name = type(exc).__name__.lower()
        exc_msg = str(exc).lower()
        combined = f"{exc_name} {exc_msg}"
        if any(k in combined for k in ("ratelimit", "rate_limit", "throttl", "429", "too_many")):
            return ErrorClass.RETRYABLE
        if any(k in combined for k in ("timeout", "deadline", "read")):
            return ErrorClass.RETRYABLE
        if any(k in combined for k in ("auth", "permission", "forbidden", "invalid_request", "content_policy")):
            return ErrorClass.PERMANENT
        return ErrorClass.UNKNOWN

    if response is not None:
        if response.finish_reason in _PERMANENT_FINISH_REASONS:
            return ErrorClass.PERMANENT
        if response.finish_reason == FinishReason.ERROR and not response.content:
            return ErrorClass.RETRYABLE

    return ErrorClass.UNKNOWN


# ── Circuit Breaker ────────────────────────────────────────────────

@dataclass
class CircuitBreaker:
    """Per-provider circuit breaker with 3 states: closed/open/half_open."""

    max_failures: int = 5
    reset_timeout_seconds: float = 60.0
    half_open_max: int = 1
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _state: str = field(default="closed", init=False)
    _half_open_attempts: int = field(default=0, init=False)

    def record_success(self) -> None:
        self._failure_count = 0
        self._half_open_attempts = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.max_failures:
            self._state = "open"
            logger.warning(
                "Circuit breaker OPEN after %d failures (reset in %.0fs)",
                self._failure_count,
                self.reset_timeout_seconds,
            )

    def allow_request(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            if time.monotonic() - self._last_failure_time > self.reset_timeout_seconds:
                self._state = "half_open"
                self._half_open_attempts = 0
                logger.info("Circuit breaker -> half_open (probe allowed)")
            else:
                return False
        if self._state == "half_open":
            if self._half_open_attempts < self.half_open_max:
                self._half_open_attempts += 1
                return True
            return False
        return False

    @property
    def is_open(self) -> bool:
        return self._state == "open"

    @property
    def state(self) -> str:
        return self._state


# ── Provider Reliability Wrapper ───────────────────────────────────

@dataclass
class ReliabilityConfig:
    """Configuration for provider reliability. All values config-driven."""

    timeout_seconds: float = 30.0
    max_retries: int = 3
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 30.0
    circuit_breaker_max_failures: int = 5
    circuit_breaker_reset_seconds: float = 60.0


class ReliableProvider:
    """Wraps an LLMProvider with timeout, retry, and circuit breaker.

    All provider calls go through this wrapper. Policy enforcement
    (PII scrub, data class, allowlist) is handled by LLMService before
    reaching this layer.
    """

    def __init__(self, provider: LLMProvider, config: ReliabilityConfig | None = None):
        self._provider = provider
        self._config = config or ReliabilityConfig()
        self._circuit = CircuitBreaker(
            max_failures=self._config.circuit_breaker_max_failures,
            reset_timeout_seconds=self._config.circuit_breaker_reset_seconds,
        )

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        return self._circuit

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self._circuit.allow_request():
            logger.warning(
                "Circuit breaker OPEN for %s — rejecting request",
                self._provider.provider_name,
            )
            return ChatResponse(
                content="",
                model=self._provider.model_name,
                finish_reason=FinishReason.ERROR,
                usage={},
            )

        last_exc: Exception | None = None
        last_response: ChatResponse | None = None

        for attempt in range(self._config.max_retries):
            try:
                response = await asyncio.wait_for(
                    self._provider.chat(request),
                    timeout=self._config.timeout_seconds,
                )

                error_class = classify_error(None, response)
                if error_class == ErrorClass.PERMANENT:
                    self._circuit.record_failure()
                    return response

                if response.finish_reason == FinishReason.ERROR and not response.content:
                    last_response = response
                    error_class = classify_error(None, response)
                    if error_class == ErrorClass.RETRYABLE and attempt < self._config.max_retries - 1:
                        delay = self._backoff(attempt)
                        logger.warning(
                            "Retryable error from %s (attempt %d/%d), waiting %.1fs",
                            self._provider.provider_name,
                            attempt + 1,
                            self._config.max_retries,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    self._circuit.record_failure()
                    return response

                self._circuit.record_success()
                return response

            except asyncio.TimeoutError as exc:
                last_exc = exc
                error_class = classify_error(exc)
                if attempt < self._config.max_retries - 1:
                    delay = self._backoff(attempt)
                    logger.warning(
                        "Timeout from %s (attempt %d/%d), waiting %.1fs",
                        self._provider.provider_name,
                        attempt + 1,
                        self._config.max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

            except Exception as exc:
                last_exc = exc
                error_class = classify_error(exc)
                if error_class == ErrorClass.PERMANENT:
                    self._circuit.record_failure()
                    return ChatResponse(
                        content="",
                        model=self._provider.model_name,
                        finish_reason=FinishReason.ERROR,
                        usage={},
                    )
                if attempt < self._config.max_retries - 1:
                    delay = self._backoff(attempt)
                    logger.warning(
                        "Retryable error from %s (attempt %d/%d): %s, waiting %.1fs",
                        self._provider.provider_name,
                        attempt + 1,
                        self._config.max_retries,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

        self._circuit.record_failure()
        if last_response is not None:
            return last_response
        return ChatResponse(
            content="",
            model=self._provider.model_name,
            finish_reason=FinishReason.ERROR,
            usage={},
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        if not self._circuit.allow_request():
            yield StreamEvent(type="error", error="Circuit breaker open")
            return

        try:
            async for event in self._provider.chat_stream(request):
                yield event
            self._circuit.record_success()
        except Exception as exc:
            self._circuit.record_failure()
            yield StreamEvent(type="error", error=str(exc))

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        if not self._circuit.allow_request():
            return EmbeddingResponse(
                embedding=[] if isinstance(request.text, str) else [[]],
                model=request.model or self._provider.model_name,
            )

        last_exc: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                response = await asyncio.wait_for(
                    self._provider.embed(request),
                    timeout=self._config.timeout_seconds,
                )
                self._circuit.record_success()
                return response
            except Exception as exc:
                last_exc = exc
                error_class = classify_error(exc)
                if error_class == ErrorClass.PERMANENT:
                    self._circuit.record_failure()
                    break
                if attempt < self._config.max_retries - 1:
                    delay = self._backoff(attempt)
                    await asyncio.sleep(delay)
                    continue

        self._circuit.record_failure()
        model = request.model or self._provider.model_name
        return EmbeddingResponse(
            embedding=[] if isinstance(request.text, str) else [[]],
            model=model,
        )

    def _backoff(self, attempt: int) -> float:
        delay = self._config.base_backoff_seconds * (2 ** attempt)
        return min(delay, self._config.max_backoff_seconds)


from typing import AsyncIterator
