"""AI Foundation F3 — LLM observability: request_id propagation, metrics, structured logging.

Provides:
  - AIObservability: in-memory metrics collector for AI call patterns
  - log_context(): structured logger factory with request_id context
  - format_extra(): helper for structured log extra dicts
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any


class _Histogram:
    """Prometheus-style histogram for latency tracking."""
    BUCKETS = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]

    def __init__(self) -> None:
        self._buckets = {b: 0 for b in self.BUCKETS}
        self._sum: float = 0.0
        self._count: int = 0

    def observe(self, value: float) -> None:
        self._count += 1
        self._sum += value
        for b in self.BUCKETS:
            if value <= b:
                self._buckets[b] += 1

    def snapshot(self) -> dict[str, Any]:
        return {"buckets": dict(self._buckets), "sum": self._sum, "count": self._count}


@dataclass
class AIObservability:
    """Thread-safe in-memory metrics for AI/LLM calls.
    
    Counters: call count, tokens, cost, policy blocks, budget rejections.
    Histograms: latency per provider.
    """

    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Call counters: (provider, model, operation, status) -> count
    _call_counter: dict[tuple[str, str, str, str], int] = field(default_factory=dict)

    # Latency histograms: (provider, model) -> histogram
    _latency_histograms: dict[tuple[str, str], _Histogram] = field(default_factory=dict)

    # Token counters: (provider, model, tokentype) -> total tokens
    _tokens: dict[tuple[str, str, str], int] = field(default_factory=dict)

    # Cost counter: (provider, model) -> total cost (float)
    _cost: dict[tuple[str, str], float] = field(default_factory=dict)

    # Policy blocks: reason -> count
    _policy_blocks: dict[str, int] = field(default_factory=dict)

    # Budget rejections: tenant_id -> count
    _budget_rejections: dict[str, int] = field(default_factory=dict)

    # Circuit breaker transitions: provider -> transition_type -> count
    _cb_transitions: dict[tuple[str, str], int] = field(default_factory=dict)

    _start_time: float = field(default_factory=time.time)

    # ── Recording ───────────────────────────────────────────────────

    def record_llm_call(
        self,
        provider: str,
        model: str,
        operation: str,
        status: str,  # "success", "error", "blocked"
        latency_ms: float = 0.0,
    ) -> None:
        with self._lock:
            key = (provider, model, operation, status)
            self._call_counter[key] = self._call_counter.get(key, 0) + 1
            lk = (provider, model)
            if lk not in self._latency_histograms:
                self._latency_histograms[lk] = _Histogram()
            self._latency_histograms[lk].observe(latency_ms / 1000.0)

    def record_tokens(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        with self._lock:
            kp = (provider, model, "prompt")
            kc = (provider, model, "completion")
            self._tokens[kp] = self._tokens.get(kp, 0) + prompt_tokens
            self._tokens[kc] = self._tokens.get(kc, 0) + completion_tokens

    def record_cost(self, provider: str, model: str, cost: float) -> None:
        with self._lock:
            k = (provider, model)
            self._cost[k] = self._cost.get(k, 0.0) + cost

    def record_policy_block(self, reason: str) -> None:
        with self._lock:
            self._policy_blocks[reason] = self._policy_blocks.get(reason, 0) + 1

    def record_budget_rejection(self, tenant_id: str) -> None:
        with self._lock:
            self._budget_rejections[tenant_id] = self._budget_rejections.get(tenant_id, 0) + 1

    def record_circuit_breaker(self, provider: str, transition: str) -> None:
        with self._lock:
            k = (provider, transition)
            self._cb_transitions[k] = self._cb_transitions.get(k, 0) + 1

    # ── Snapshot ────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "calls": dict(self._call_counter),
                "tokens": dict(self._tokens),
                "cost": dict(self._cost),
                "policy_blocks": dict(self._policy_blocks),
                "budget_rejections": dict(self._budget_rejections),
                "cb_transitions": dict(self._cb_transitions),
                "uptime_seconds": time.time() - self._start_time,
            }

    # ── Prometheus text format ──────────────────────────────────────

    def generate(self) -> str:
        lines: list[str] = []

        def _l(text: str) -> None:
            lines.append(text)

        with self._lock:
            _l("# HELP salesos_ai_calls_total Total AI/LLM calls by provider, model, operation, status")
            _l("# TYPE salesos_ai_calls_total counter")
            for (prov, mdl, op, st), cnt in sorted(self._call_counter.items()):
                _l(f'salesos_ai_calls_total{{provider="{prov}",model="{mdl}",operation="{op}",status="{st}"}} {cnt}')

            _l("")
            _l("# HELP salesos_ai_call_latency_seconds AI call latency histogram by provider, model")
            _l("# TYPE salesos_ai_call_latency_seconds histogram")
            base = "salesos_ai_call_latency_seconds"
            for (prov, mdl), hist in sorted(self._latency_histograms.items()):
                labels = f'provider="{prov}",model="{mdl}"'
                snap = hist.snapshot()
                for bucket, count in sorted(snap["buckets"].items()):
                    _l(f'{base}_bucket{{{labels},le="{bucket}"}} {count}')
                _l(f'{base}_bucket{{{labels},le="+Inf"}} {snap["count"]}')
                _l(f"{base}_count{{{labels}}} {snap['count']}")
                _l(f"{base}_sum{{{labels}}} {snap['sum']:.6f}")

            _l("")
            _l("# HELP salesos_ai_tokens_total Total AI tokens by provider, model, type")
            _l("# TYPE salesos_ai_tokens_total counter")
            for (prov, mdl, tt), cnt in sorted(self._tokens.items()):
                _l(f'salesos_ai_tokens_total{{provider="{prov}",model="{mdl}",type="{tt}"}} {cnt}')

            _l("")
            _l("# HELP salesos_ai_cost_total Total AI cost by provider, model")
            _l("# TYPE salesos_ai_cost_total counter")
            for (prov, mdl), cst in sorted(self._cost.items()):
                _l(f'salesos_ai_cost_total{{provider="{prov}",model="{mdl}"}} {cst:.8f}')

            _l("")
            _l("# HELP salesos_ai_policy_blocks_total AI policy blocks by reason")
            _l("# TYPE salesos_ai_policy_blocks_total counter")
            for reason, cnt in sorted(self._policy_blocks.items()):
                reason_clean = reason.replace('"', '\\"')
                _l(f'salesos_ai_policy_blocks_total{{reason="{reason_clean}"}} {cnt}')

            _l("")
            _l("# HELP salesos_ai_budget_rejections_total AI budget rejections by tenant")
            _l("# TYPE salesos_ai_budget_rejections_total counter")
            for tid, cnt in sorted(self._budget_rejections.items()):
                _l(f'salesos_ai_budget_rejections_total{{tenant_id="{tid}"}} {cnt}')

            _l("")
            _l("# HELP salesos_ai_circuit_breaker_transitions Circuit breaker state transitions")
            _l("# TYPE salesos_ai_circuit_breaker_transitions gauge")
            for (prov, ts), cnt in sorted(self._cb_transitions.items()):
                _l(f'salesos_ai_circuit_breaker_transitions{{provider="{prov}",transition="{ts}"}} {cnt}')

            _l("")
            _l("# HELP salesos_ai_uptime_seconds AI observability uptime")
            _l("# TYPE salesos_ai_uptime_seconds gauge")
            _l(f"salesos_ai_uptime_seconds {time.time() - self._start_time:.0f}")

        return "\n".join(lines) + "\n"


ai_observability = AIObservability()


# ── Structured Logging Helpers ──────────────────────────────────────

def format_extra(**kwargs: Any) -> dict[str, Any]:
    """Build structured logging extra dict, filtering None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


def log_context(name: str, request_id: str | None = None, tenant_id: str | None = None) -> logging.Logger:
    """Return a logger for the given module name. Extra context attached via adapter pattern.

    Args:
        name: Logger name (typically __name__)
        request_id: Optional request ID for correlation
        tenant_id: Optional tenant ID

    Returns:
        Standard logging.Logger. Callers pass extra=format_extra(...) per call.
    """
    return logging.getLogger(name)
