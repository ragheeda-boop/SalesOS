"""Unit tests for MetricsTracker — HTTP, DB, AI metrics and Prometheus output."""

from __future__ import annotations

import time

from app.common.metrics import MetricsTracker, _Histogram, metrics


class TestHistogram:
    def test_observe_within_bucket(self):
        h = _Histogram()
        h.observe(0.003)
        assert h._count == 1
        assert h._sum == 0.003
        assert h._buckets[0.005] == 1
        assert h._buckets[0.01] == 1

    def test_observe_beyond_all_buckets(self):
        h = _Histogram()
        h.observe(20.0)
        assert h._count == 1
        assert h._sum == 20.0
        for b in h.BUCKETS:
            assert h._buckets[b] == 0

    def test_observe_exact_boundary(self):
        h = _Histogram()
        h.observe(0.1)
        assert h._buckets[0.1] == 1
        assert h._buckets[0.05] == 0

    def test_multiple_observations(self):
        h = _Histogram()
        h.observe(0.01)
        h.observe(0.05)
        h.observe(0.5)
        assert h._count == 3
        assert abs(h._sum - 0.56) < 1e-10

    def test_snapshot_returns_copy(self):
        h = _Histogram()
        h.observe(0.02)
        snap = h.snapshot()
        assert snap["count"] == 1
        assert snap["sum"] == 0.02
        assert isinstance(snap["buckets"], dict)


class TestMetricsTracker:
    def test_track_http_request(self):
        t = MetricsTracker()
        t.track_http_request("GET", "/api/v1/companies", 200, 0.05)
        output = t.generate()
        assert "salesos_http_requests_total" in output
        assert "GET" in output
        assert "/api/v1/companies" in output

    def test_track_http_request_multiple(self):
        t = MetricsTracker()
        t.track_http_request("GET", "/api/v1/companies", 200, 0.05)
        t.track_http_request("POST", "/api/v1/companies", 201, 0.1)
        t.track_http_request("GET", "/api/v1/companies", 200, 0.03)
        output = t.generate()
        assert output.count("salesos_http_requests_total") >= 2

    def test_track_db_query(self):
        t = MetricsTracker()
        t.track_db_query("get_companies", 0.02)
        output = t.generate()
        assert "salesos_db_query_duration_seconds" in output
        assert 'query_name="get_companies"' in output

    def test_track_ai_inference(self):
        t = MetricsTracker()
        t.track_ai_inference("gpt-4o", 1.5)
        output = t.generate()
        assert "salesos_ai_inference_duration_seconds" in output
        assert 'model="gpt-4o"' in output

    def test_db_timer_context_manager(self):
        t = MetricsTracker()
        with t.db_timer("slow_query"):
            time.sleep(0.001)
        output = t.generate()
        assert "slow_query" in output

    def test_ai_timer_context_manager(self):
        t = MetricsTracker()
        with t.ai_timer("claude-3"):
            time.sleep(0.001)
        output = t.generate()
        assert "claude-3" in output

    def test_uptime_in_output(self):
        t = MetricsTracker()
        output = t.generate()
        assert "salesos_uptime_seconds" in output

    def test_eof_marker(self):
        t = MetricsTracker()
        output = t.generate()
        assert output.strip().startswith("# EOF") or "# EOF" in output

    def test_histogram_bucket_output(self):
        t = MetricsTracker()
        t.track_http_request("GET", "/test", 200, 0.003)
        output = t.generate()
        assert "le=" in output

    def test_empty_tracker_output(self):
        t = MetricsTracker()
        output = t.generate()
        assert "salesos_http_requests_total" in output
        assert "salesos_uptime_seconds" in output

    def test_special_characters_in_path(self):
        t = MetricsTracker()
        t.track_http_request("GET", '/path/with"quotes', 200, 0.01)
        output = t.generate()
        assert "path/with" in output

    def test_global_metrics_singleton(self):
        assert isinstance(metrics, MetricsTracker)
