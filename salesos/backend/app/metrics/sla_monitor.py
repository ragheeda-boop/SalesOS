"""SLA Monitoring — circular-buffer latency tracking with violation alerting.

Tracks p50/p95/p99 per endpoint category over a 24h sliding window.
Violates SLA when latency or error-rate thresholds defined in SLA_CONFIG.json are breached.
"""

from __future__ import annotations

import json
import os
import time
import threading
import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

_SLA_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "SLA_CONFIG.json")
_WINDOW_SECONDS = 86400  # 24h circular buffer


class _CircularBuffer:
    """Fixed-size ring buffer for timestamped latency samples."""

    __slots__ = ("_capacity", "_buf", "_head", "_count")

    def __init__(self, capacity: int = 100_000) -> None:
        self._capacity = capacity
        self._buf: list[tuple[float, float]] = [0.0, 0.0] * capacity  # placeholder
        self._buf = [(0.0, 0.0)] * capacity
        self._head = 0
        self._count = 0

    def append(self, timestamp: float, value: float) -> None:
        self._buf[self._head] = (timestamp, value)
        self._head = (self._head + 1) % self._capacity
        self._count = min(self._count + 1, self._capacity)

    def values_within(self, now: float, window: float) -> list[float]:
        cutoff = now - window
        values: list[float] = []
        n = min(self._count, self._capacity)
        for i in range(n):
            idx = (self._head - 1 - i) % self._capacity
            ts, val = self._buf[idx]
            if ts < cutoff:
                break
            values.append(val)
        return values


class SLAMonitor:
    """Per-process SLA monitor using circular buffers for 24h latency windows."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buffers: dict[str, _CircularBuffer] = defaultdict(lambda: _CircularBuffer())
        self._error_counts: dict[str, int] = defaultdict(int)
        self._total_counts: dict[str, int] = defaultdict(int)
        self._violations: list[dict[str, Any]] = []
        self._max_violations = 500
        self._config: dict[str, Any] | None = None

    def _load_config(self) -> dict[str, Any]:
        if self._config is not None:
            return self._config
        try:
            with open(_SLA_CONFIG_PATH, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {"categories": {}, "alerting": {"evaluation_window_seconds": 300}}
        return self._config

    def record_request(self, category: str, latency_ms: float, status_code: int) -> None:
        now = time.time()
        with self._lock:
            self._buffers[category].append(now, latency_ms)
            self._total_counts[category] += 1
            if status_code >= 500:
                self._error_counts[category] += 1

    def _percentile(self, sorted_values: list[float], p: float) -> float:
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * p / 100
        f = int(k)
        c = f + 1
        if c >= len(sorted_values):
            return sorted_values[-1]
        return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])

    def evaluate(self) -> list[dict[str, Any]]:
        config = self._load_config()
        now = time.time()
        window = config.get("alerting", {}).get("evaluation_window_seconds", 300)
        violations: list[dict[str, Any]] = []

        with self._lock:
            categories = dict(self._buffers)
            total = dict(self._total_counts)
            errors = dict(self._error_counts)

        category_slas = config.get("categories", {})
        for cat_name, cat_def in category_slas.items():
            sla = cat_def.get("sla", {})
            buf = categories.get(cat_name)
            if buf is None:
                continue

            values = buf.values_within(now, window)
            if not values:
                continue

            values_sorted = sorted(values)
            p50 = self._percentile(values_sorted, 50)
            p95 = self._percentile(values_sorted, 95)
            p99 = self._percentile(values_sorted, 99)

            total_req = total.get(cat_name, 0)
            err_req = errors.get(cat_name, 0)
            error_rate = (err_req / total_req * 100) if total_req > 0 else 0.0

            sla_p50 = sla.get("p50_ms", float("inf"))
            sla_p95 = sla.get("p95_ms", float("inf"))
            sla_p99 = sla.get("p99_ms", float("inf"))
            sla_err = sla.get("error_budget_percent", 100)

            reasons: list[str] = []
            if p50 > sla_p50:
                reasons.append(f"p50={p50:.1f}ms > {sla_p50}ms")
            if p95 > sla_p95:
                reasons.append(f"p95={p95:.1f}ms > {sla_p95}ms")
            if p99 > sla_p99:
                reasons.append(f"p99={p99:.1f}ms > {sla_p99}ms")
            if error_rate > sla_err:
                reasons.append(f"error_rate={error_rate:.2f}% > {sla_err}%")

            violation = {
                "category": cat_name,
                "breached": len(reasons) > 0,
                "reasons": reasons,
                "metrics": {
                    "p50_ms": round(p50, 1),
                    "p95_ms": round(p95, 1),
                    "p99_ms": round(p99, 1),
                    "error_rate_percent": round(error_rate, 2),
                    "sample_count": len(values),
                    "total_requests": total_req,
                },
                "thresholds": {
                    "p50_ms": sla_p50,
                    "p95_ms": sla_p95,
                    "p99_ms": sla_p99,
                    "error_budget_percent": sla_err,
                },
                "evaluated_at": now,
            }
            violations.append(violation)

            if reasons:
                severity = "critical" if any("p99" in r or "error_budget" in r for r in reasons) else "warning"
                entry = {**violation, "severity": severity}
                self._violations.append(entry)
                if len(self._violations) > self._max_violations:
                    self._violations = self._violations[-self._max_violations:]
                logger.warning(
                    "SLA violation category=%s severity=%s reasons=%s",
                    cat_name, severity, "; ".join(reasons),
                )

        return violations

    def get_violations(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._violations[-limit:])

    def get_report(self) -> dict[str, Any]:
        config = self._load_config()
        now = time.time()
        violations = self.evaluate()

        breached = [v for v in violations if v["breached"]]
        healthy = [v for v in violations if not v["breached"]]

        return {
            "status": "degraded" if breached else "healthy",
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "breached_count": len(breached),
            "healthy_count": len(healthy),
            "categories": violations,
            "recent_violations": self.get_violations(10),
        }


sla_monitor = SLAMonitor()
