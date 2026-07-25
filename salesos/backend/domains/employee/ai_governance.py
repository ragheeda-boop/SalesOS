"""AI Governance — token tracking, cost controls, prompt registry, caching, circuit breaker.

Enterprise controls for the EmployeeAIPipeline.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from typing import Any


# ── Prompt Registry ───────────────────────────────────────────────

PROMPT_VERSION = "1.0.0"

PROMPT_REGISTRY: dict[str, dict] = {
    "meeting_summary": {
        "version": "1.0",
        "template": "Summarize this meeting in 2-3 sentences. Extract action items.\nMeeting title: {title}\nDescription: {description}",
        "max_tokens": 300,
        "temperature": 0.3,
        "model": "gpt-4o-mini",
    },
    "email_summary": {
        "version": "1.0",
        "template": "Analyze this email. Provide summary, sentiment, and action items.\nSubject: {subject}\nBody: {body}",
        "max_tokens": 300,
        "temperature": 0.3,
        "model": "gpt-4o-mini",
    },
    "weekly_digest": {
        "version": "1.0",
        "template": "Write a concise weekly performance digest for {name}.\nThis week: {signals} activities, {meetings} meetings, {emails} emails. Score: {score}/100.\nProvide 2-3 specific coaching tips in Arabic.",
        "max_tokens": 500,
        "temperature": 0.5,
        "model": "gpt-4o-mini",
    },
    "executive_brief": {
        "version": "1.0",
        "template": "Write an executive AI brief in Arabic.\nOrganization: {total} employees, {signals} activities. Avg score: {score}/100. At-risk: {risk}.\nProvide assessment, trends, recommendations.",
        "max_tokens": 600,
        "temperature": 0.4,
        "model": "gpt-4o-mini",
    },
    "coaching_insight": {
        "version": "1.0",
        "template": "Provide personalized sales coaching advice for {name} in Arabic.\nLast 30 days: {signals} activities. Breakdown: {breakdown}.\nIdentify 2-3 actionable improvements.",
        "max_tokens": 400,
        "temperature": 0.5,
        "model": "gpt-4o-mini",
    },
}


# ── Cost Tracking ──────────────────────────────────────────────────

MODEL_PRICING = {
    "gpt-4o-mini":     {"input": 0.15,  "output": 0.60},   # per 1M tokens (USD)
    "gpt-3.5-turbo":   {"input": 0.50,  "output": 1.50},
    "gpt-4o":          {"input": 2.50,  "output": 10.00},
}


@dataclass
class AICostTracker:
    """Tracks AI usage costs per tenant with budget limits."""

    daily_budget_usd: float = 1.00
    monthly_budget_usd: float = 25.00
    _daily_usage: float = 0.0
    _monthly_usage: float = 0.0
    _daily_reset_at: str = ""
    _monthly_reset_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc)
        self._daily_reset_at = now.replace(hour=0, minute=0, second=0).isoformat()
        self._monthly_reset_at = now.replace(day=1, hour=0, minute=0, second=0).isoformat()

    def _check_reset(self):
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0)
        if today.isoformat() > self._daily_reset_at:
            self._daily_usage = 0.0
            self._daily_reset_at = today.isoformat()
        month = now.replace(day=1, hour=0, minute=0, second=0)
        if month.isoformat() > self._monthly_reset_at:
            self._monthly_usage = 0.0
            self._monthly_reset_at = month.isoformat()

    def record_usage(self, model: str, input_tokens: int, output_tokens: int):
        pricing = MODEL_PRICING.get(model, {"input": 0.15, "output": 0.60})
        cost = (input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]
        self._daily_usage += cost
        self._monthly_usage += cost

    @property
    def daily_usage(self) -> float:
        self._check_reset()
        return round(self._daily_usage, 4)

    @property
    def monthly_usage(self) -> float:
        self._check_reset()
        return round(self._monthly_usage, 4)

    @property
    def daily_remaining(self) -> float:
        return round(max(0, self.daily_budget_usd - self.daily_usage), 4)

    @property
    def monthly_remaining(self) -> float:
        return round(max(0, self.monthly_budget_usd - self.monthly_usage), 4)

    def can_call(self) -> bool:
        self._check_reset()
        return self.daily_usage < self.daily_budget_usd and self.monthly_usage < self.monthly_budget_usd


# ── Circuit Breaker ────────────────────────────────────────────────

@dataclass
class AICircuitBreaker:
    """Prevents cascading AI failures by opening circuit after consecutive errors."""

    max_failures: int = 5
    reset_timeout_seconds: int = 60
    half_open_max: int = 1
    _failure_count: int = 0
    _last_failure_time: float = 0.0
    _state: str = "closed"  # closed, open, half_open
    _half_open_attempts: int = 0

    def record_success(self):
        self._failure_count = 0
        self._half_open_attempts = 0
        self._state = "closed"

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.max_failures:
            self._state = "open"

    def allow_request(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            if time.time() - self._last_failure_time > self.reset_timeout_seconds:
                self._state = "half_open"
                self._half_open_attempts = 0
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


# ── AI Response Cache ──────────────────────────────────────────────

class AIResponseCache:
    """Simple in-memory cache for AI responses with TTL."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[float, dict]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def _key(self, prompt_type: str, params: dict) -> str:
        raw = f"{prompt_type}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, prompt_type: str, params: dict) -> dict | None:
        key = self._key(prompt_type, params)
        if key in self._cache:
            cached_at, result = self._cache[key]
            if time.time() - cached_at < self._ttl:
                return result
            del self._cache[key]
        return None

    def set(self, prompt_type: str, params: dict, result: dict):
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        key = self._key(prompt_type, params)
        self._cache[key] = (time.time(), result)

    def clear(self):
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# ── AI Metrics Collector ──────────────────────────────────────────

@dataclass
class AIMetrics:
    """Collects AI usage metrics for monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    cached_hits: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    _latency_samples: list[float] = field(default_factory=list)

    def record_call(self, model: str, input_tokens: int, output_tokens: int,
                    latency_ms: float, success: bool, cached: bool = False):
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        if cached:
            self.cached_hits += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        pricing = MODEL_PRICING.get(model, {"input": 0.15, "output": 0.60})
        cost = (input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]
        self.total_cost_usd += cost
        self._latency_samples.append(latency_ms)
        if len(self._latency_samples) > 1000:
            self._latency_samples = self._latency_samples[-1000:]
        if self._latency_samples:
            self.avg_latency_ms = round(sum(self._latency_samples) / len(self._latency_samples), 1)

    @property
    def success_rate(self) -> float:
        return round(self.successful_calls / max(1, self.total_calls) * 100, 1)

    @property
    def cache_hit_rate(self) -> float:
        return round(self.cached_hits / max(1, self.total_calls) * 100, 1)

    def snapshot(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "successful": self.successful_calls,
            "failed": self.failed_calls,
            "success_rate": self.success_rate,
            "cached_hits": self.cached_hits,
            "cache_hit_rate": self.cache_hit_rate,
            "total_tokens_in": self.total_input_tokens,
            "total_tokens_out": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "avg_latency_ms": self.avg_latency_ms,
        }
