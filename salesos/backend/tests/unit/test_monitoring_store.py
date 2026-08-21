"""Tests for monitoring module — _MonitoringStore (in-memory, zero DB deps).

Covers ingest, aggregate, health, percentile math, and ring-buffer eviction.
"""

from __future__ import annotations

import time

import pytest

from app.modules.monitoring.router import (
    MonitoringEventSchema,
    _MonitoringStore,
)


def _event(**overrides) -> MonitoringEventSchema:
    defaults = dict(
        type="api_call",
        timestamp="2026-08-21T12:00:00Z",
        method="GET",
        path="/api/v1/companies",
        duration_ms=100,
        status=200,
    )
    defaults.update(overrides)
    return MonitoringEventSchema(**defaults)


class TestIngest:
    def test_api_call_ingest(self):
        s = _MonitoringStore()
        s.ingest(_event(type="api_call"))
        assert len(s.api_calls) == 1
        assert s.api_calls[0]["method"] == "GET"
        assert s.api_calls[0]["duration_ms"] == 100

    def test_error_ingest(self):
        s = _MonitoringStore()
        s.ingest(_event(type="error", error_message="boom", error_stack="trace", context="auth"))
        assert len(s.errors) == 1
        assert s.errors[0]["message"] == "boom"

    def test_page_load_ingest(self):
        s = _MonitoringStore()
        s.ingest(_event(type="page_load", route="/dashboard", duration_ms=500, fcp=120.5, dom_interactive=300, dom_complete=450, memory_used_mb=64.2))
        assert len(s.page_loads) == 1
        assert s.page_loads[0]["route"] == "/dashboard"
        assert s.page_loads[0]["fcp"] == 120.5

    def test_web_vital_ingest(self):
        s = _MonitoringStore()
        s.ingest(_event(type="web_vital", name="lcp", value=2500))
        s.ingest(_event(type="web_vital", name="lcp", value=2800))
        assert s.web_vitals["lcp"] == [2500, 2800]

    def test_metric_ingest(self):
        s = _MonitoringStore()
        s.ingest(_event(type="metric", name="active_users", value=42))
        assert s.custom_metrics["active_users"] == [42]

    def test_unknown_type_ignored(self):
        s = _MonitoringStore()
        s.ingest(_event(type="unknown_type"))
        assert len(s.api_calls) == 0
        assert len(s.errors) == 0


class TestRingBuffer:
    def test_api_calls_eviction(self):
        s = _MonitoringStore()
        s.max_samples = 3
        for _ in range(5):
            s.ingest(_event(type="api_call", duration_ms=10))
        assert len(s.api_calls) == 3

    def test_errors_eviction(self):
        s = _MonitoringStore()
        s.max_samples = 2
        s.ingest(_event(type="error", error_message="e1"))
        s.ingest(_event(type="error", error_message="e2"))
        s.ingest(_event(type="error", error_message="e3"))
        assert len(s.errors) == 2
        assert s.errors[0]["message"] == "e2"

    def test_web_vital_eviction(self):
        s = _MonitoringStore()
        s.max_samples = 2
        s.ingest(_event(type="web_vital", name="fid", value=1))
        s.ingest(_event(type="web_vital", name="fid", value=2))
        s.ingest(_event(type="web_vital", name="fid", value=3))
        assert s.web_vitals["fid"] == [2, 3]


class TestPercentile:
    def test_empty_data(self):
        assert _MonitoringStore._percentile([], 50) == 0

    def test_single_value(self):
        assert _MonitoringStore._percentile([100], 50) == 100

    def test_median(self):
        assert _MonitoringStore._percentile([1, 2, 3, 4, 5], 50) == 3

    def test_p99_high(self):
        data = list(range(1, 101))
        p99 = _MonitoringStore._percentile(data, 99)
        assert 99 <= p99 <= 100


class TestAggregate:
    def test_empty_store(self):
        s = _MonitoringStore()
        result = s.aggregate()
        assert result["api_calls"]["total"] == 0
        assert result["errors"]["total"] == 0
        assert result["page_loads"]["total"] == 0
        assert result["web_vitals"]["lcp"] is None

    def test_api_call_percentiles(self):
        s = _MonitoringStore()
        for ms in [10, 20, 30, 40, 50]:
            s.ingest(_event(type="api_call", duration_ms=ms))
        result = s.aggregate()
        assert result["api_calls"]["total"] == 5
        assert result["api_calls"]["p50_ms"] == 30

    def test_error_by_context(self):
        s = _MonitoringStore()
        s.ingest(_event(type="error", error_message="e1", context="auth"))
        s.ingest(_event(type="error", error_message="e2", context="auth"))
        s.ingest(_event(type="error", error_message="e3", context="db"))
        result = s.aggregate()
        assert result["errors"]["by_context"]["auth"] == 2
        assert result["errors"]["by_context"]["db"] == 1

    def test_page_load_averages(self):
        s = _MonitoringStore()
        s.ingest(_event(type="page_load", duration_ms=100, dom_interactive=200))
        s.ingest(_event(type="page_load", duration_ms=200, dom_interactive=300))
        result = s.aggregate()
        assert result["page_loads"]["avg_load_ms"] == 150.0
        assert result["page_loads"]["avg_dom_interactive_ms"] == 250.0

    def test_web_vitals_averages(self):
        s = _MonitoringStore()
        s.ingest(_event(type="web_vital", name="lcp", value=2000))
        s.ingest(_event(type="web_vital", name="lcp", value=3000))
        s.ingest(_event(type="web_vital", name="cls", value=0.1))
        result = s.aggregate()
        assert result["web_vitals"]["lcp"] == 2500.0
        assert result["web_vitals"]["cls"] == 0.1


class TestHealth:
    def test_health_counts_all_events(self):
        s = _MonitoringStore()
        s.ingest(_event(type="api_call"))
        s.ingest(_event(type="error", error_message="x"))
        s.ingest(_event(type="page_load"))
        s.ingest(_event(type="web_vital", name="lcp", value=100))
        s.ingest(_event(type="metric", name="cpu", value=50))
        h = s.health()
        assert h["status"] == "ok"
        assert h["events_ingested"] == 5
        assert h["api_calls_total"] == 1
        assert h["errors_total"] == 1
        assert h["page_loads_total"] == 1

    def test_health_uptime_positive(self):
        s = _MonitoringStore()
        h = s.health()
        assert h["uptime_seconds"] >= 0
