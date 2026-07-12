"""Tests for the AI Evaluator — validates evaluation framework, built-in metrics, and aggregation."""
from __future__ import annotations

from domains.ai.evaluator import AIEvaluator
from domains.ai.models import AIEvaluation, EvaluationMetric


def test_evaluate_exact_match():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-1",
        input="What is 2+2?",
        output="4",
        expected="4",
        metrics=["exact_match"],
    )
    assert result.score == 1.0
    assert result.metrics[0].passed is True
    assert result.metrics[0].value == 1.0


def test_evaluate_exact_match_fails():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-1",
        input="What is 2+2?",
        output="5",
        expected="4",
        metrics=["exact_match"],
    )
    assert result.score == 0.0
    assert result.metrics[0].passed is False


def test_contains_keyword():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-2",
        input="Describe SalesOS",
        output="SalesOS is a company intelligence platform",
        expected="SalesOS",
        metrics=["contains_keyword"],
    )
    assert result.score == 1.0
    assert result.metrics[0].passed is True


def test_contains_keyword_missing():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-2",
        input="Describe SalesOS",
        output="It is a great platform",
        expected="SalesOS",
        metrics=["contains_keyword"],
    )
    assert result.score == 0.0
    assert result.metrics[0].passed is False


def test_length_check():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-3",
        input="Say hello",
        output="Hello world",
        metrics=["length_check"],
    )
    assert result.score == 1.0


def test_length_check_empty():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-3",
        input="Say nothing",
        output="",
        metrics=["length_check"],
    )
    assert result.score == 0.0
    assert result.metrics[0].passed is False


def test_json_valid():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-4",
        input="Output JSON",
        output='{"name": "test", "value": 42}',
        metrics=["json_valid"],
    )
    assert result.score == 1.0


def test_json_valid_fails():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-4",
        input="Output JSON",
        output="not json at all",
        metrics=["json_valid"],
    )
    assert result.score == 0.0


def test_confidence_threshold():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-5",
        input="Score this",
        output='{"confidence": 0.85, "decision": "approve"}',
        metrics=["confidence_threshold"],
    )
    assert result.score == 1.0
    assert result.metrics[0].passed is True


def test_confidence_threshold_below():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-5",
        input="Score this",
        output='{"confidence": 0.3, "decision": "reject"}',
        metrics=["confidence_threshold"],
        thresholds={"confidence_threshold": 0.7},
    )
    assert result.score == 0.0
    assert result.metrics[0].passed is False


def test_multiple_metrics():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-6",
        input="Generate JSON greeting",
        output='{"greeting": "Hello", "target": "world"}',
        expected="Hello",
        metrics=["exact_match", "json_valid"],
    )
    assert result.metrics[0].name == "exact_match"
    assert result.metrics[1].name == "json_valid"
    assert 0.0 < result.score <= 1.0


def test_evaluate_batch():
    evaluator = AIEvaluator()
    results = [
        {"prompt_id": "p1", "input": "Q1", "output": "A1", "expected": "A1", "metrics": ["exact_match"]},
        {"prompt_id": "p1", "input": "Q2", "output": "A2", "expected": "Wrong", "metrics": ["exact_match"]},
        {"prompt_id": "p2", "input": "Q3", "output": '{"ok": true}', "metrics": ["json_valid"]},
    ]
    evaluations = evaluator.evaluate_batch(results)
    assert len(evaluations) == 3
    assert evaluations[0].score == 1.0
    assert evaluations[1].score == 0.0
    assert evaluations[2].score == 1.0


def test_get_metrics_aggregation():
    evaluator = AIEvaluator()
    evaluator.evaluate(
        prompt_id="agg-prompt",
        input="Q1", output="Correct", expected="Correct",
        metrics=["exact_match"],
    )
    evaluator.evaluate(
        prompt_id="agg-prompt",
        input="Q2", output="Wrong", expected="Correct",
        metrics=["exact_match"],
    )
    metrics = evaluator.get_metrics("agg-prompt")
    assert metrics["total_evaluations"] == 2
    assert metrics["average_score"] == 0.5
    assert metrics["metrics"]["exact_match"]["pass_rate"] == 50.0


def test_get_metrics_empty():
    evaluator = AIEvaluator()
    metrics = evaluator.get_metrics("nonexistent")
    assert metrics["total_evaluations"] == 0


def test_evaluation_has_id():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-id",
        input="test",
        output="test",
        expected="test",
        metrics=["exact_match"],
    )
    assert result.id is not None
    assert len(result.id) > 0


def test_evaluation_timestamp():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-id",
        input="test",
        output="test",
        expected="test",
        metrics=["exact_match"],
    )
    assert result.timestamp is not None


def test_evaluate_with_custom_threshold():
    evaluator = AIEvaluator()
    result = evaluator.evaluate(
        prompt_id="prompt-7",
        input="Short response",
        output="Hi",
        metrics=["length_check"],
        thresholds={"length_check": 5.0},
    )
    assert result.score == 0.0
    assert result.metrics[0].passed is False
