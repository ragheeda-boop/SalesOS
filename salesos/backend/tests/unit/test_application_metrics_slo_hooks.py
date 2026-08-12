"""Wave 8 SLO hooks — decision evaluate / fan-out / agent dispatch metrics."""

from __future__ import annotations

from app.metrics.collector import ApplicationMetricsCollector


def test_decision_evaluate_histogram_and_outcome_exported():
    c = ApplicationMetricsCollector()
    c.track_decision_evaluate(0.05, "ok")
    c.track_decision_evaluate(1.2, "blocked")
    text = c.generate()
    assert "salesos_decision_evaluate_duration_seconds" in text
    assert 'salesos_decision_evaluate_total{outcome="ok"} 1' in text
    assert 'salesos_decision_evaluate_total{outcome="blocked"} 1' in text
    # Legacy NBA histogram stays in sync with evaluate.
    assert "salesos_nba_processing_duration_seconds_count 2" in text


def test_event_fanout_failure_counter_exported():
    c = ApplicationMetricsCollector()
    c.track_event_fanout_failure("decision.created", "store_timeout")
    c.track_event_fanout_failure("decision.created", "subscriber_dead_lettered")
    text = c.generate()
    assert (
        'salesos_event_fanout_failures_total{event_type="decision.created",'
        'reason="store_timeout"} 1'
    ) in text
    assert "subscriber_dead_lettered" in text


def test_agent_dispatch_error_counter_exported():
    c = ApplicationMetricsCollector()
    c.track_agent_dispatch_error("il2a_handler_timeout")
    c.track_agent_dispatch_error("celery_fatal")
    text = c.generate()
    assert 'salesos_agent_dispatch_errors_total{reason="il2a_handler_timeout"} 1' in text
    assert 'salesos_agent_dispatch_errors_total{reason="celery_fatal"} 1' in text


def test_histogram_buckets_include_hang_class():
    c = ApplicationMetricsCollector()
    c.track_decision_evaluate(25.0, "ok")
    text = c.generate()
    assert 'salesos_decision_evaluate_duration_seconds_bucket{le="30.0"} 1' in text
    assert 'salesos_decision_evaluate_duration_seconds_bucket{le="10.0"} 0' in text
