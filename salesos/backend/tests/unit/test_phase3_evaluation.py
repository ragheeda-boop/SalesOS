"""Phase 3 Evaluation — Quality gates tests.

Covers P3-6: Groundedness, hallucination detection, quality gates.
"""
from __future__ import annotations

import asyncio
import pytest

from intelligence.evaluation.quality_gates import (
    EnhancedEvaluationRunner,
    GateResult,
    GroundednessScorer,
    HallucinationDetector,
    HallucinationResult,
    QualityGate,
)
from intelligence.evaluation.runner import TestCase


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══ Groundedness scorer tests ═══

class TestGroundednessScorer:

    def test_fully_grounded(self):
        scorer = GroundednessScorer()
        score = scorer.score(
            "The deal is worth 500K SAR",
            "The deal is worth 500K SAR and was created last week",
        )
        assert score >= 0.7

    def test_partially_grounded(self):
        scorer = GroundednessScorer()
        score = scorer.score(
            "The deal is worth 500K SAR and has great potential",
            "The deal is worth 500K SAR",
        )
        assert 0.3 <= score <= 0.8

    def test_not_grounded(self):
        scorer = GroundednessScorer()
        score = scorer.score(
            "The moon is made of cheese and the sky is purple",
            "The deal is worth 500K SAR",
        )
        assert score < 0.2

    def test_empty_output(self):
        scorer = GroundednessScorer()
        assert scorer.score("", "some source") == 0.0

    def test_empty_source(self):
        scorer = GroundednessScorer()
        assert scorer.score("some output", "") == 0.0


# ═══ Hallucination detector tests ═══

class TestHallucinationDetector:

    def test_no_hallucination(self):
        detector = HallucinationDetector()
        result = detector.detect(
            "The deal is worth 500K SAR. It was created last week.",
            "The deal is worth 500K SAR. It was created last week. The company is Acme Corp.",
        )
        assert result.claims_total >= 1
        assert result.hallucination_rate <= 0.3

    def test_some_hallucination(self):
        detector = HallucinationDetector()
        result = detector.detect(
            "The deal is worth 500K SAR. The moon landing was faked.",
            "The deal is worth 500K SAR.",
        )
        assert result.hallucination_rate > 0

    def test_all_hallucination(self):
        detector = HallucinationDetector()
        result = detector.detect(
            "The moon is made of cheese. The sky is purple. Fish can fly.",
            "The deal is worth 500K SAR.",
        )
        assert result.hallucination_rate >= 0.5

    def test_empty_output(self):
        detector = HallucinationDetector()
        result = detector.detect("", "some source")
        assert result.claims_total == 0
        assert result.hallucination_rate == 0.0

    def test_result_structure(self):
        detector = HallucinationDetector()
        result = detector.detect(
            "The deal is worth 500K SAR.",
            "The deal is worth 500K SAR.",
        )
        assert isinstance(result, HallucinationResult)
        assert result.claims_supported + result.claims_unsupported == result.claims_total


# ═══ Quality gate tests ═══

class TestQualityGate:

    def test_default_gate(self):
        gate = QualityGate()
        assert gate.min_faithfulness == 0.6
        assert gate.min_relevance == 0.5
        assert gate.min_accuracy == 0.5
        assert gate.min_groundedness == 0.6
        assert gate.max_hallucination_rate == 0.3
        assert gate.min_pass_rate == 0.7

    def test_custom_gate(self):
        gate = QualityGate(min_faithfulness=0.8, max_hallucination_rate=0.1)
        assert gate.min_faithfulness == 0.8
        assert gate.max_hallucination_rate == 0.1


# ═══ Gate evaluation tests ═══

class TestGateEvaluation:

    def _make_report(self, passed_count, total, details=None):
        from intelligence.evaluation.runner import EvalReport, EvalResult
        results = []
        for i in range(total):
            d = details or {}
            results.append(EvalResult(
                test_name=f"test_{i}",
                passed=i < passed_count,
                faithfulness=0.8,
                relevance=0.7,
                accuracy=0.7,
                details=d,
            ))
        return EvalReport(
            agent_name="test_agent",
            total=total,
            passed=passed_count,
            avg_faithfulness=0.8,
            avg_relevance=0.7,
            avg_accuracy=0.7,
            results=results,
        )

    def test_gate_pass(self):
        runner = EnhancedEvaluationRunner(gate=QualityGate(min_pass_rate=0.5))
        report = self._make_report(8, 10, {"groundedness": 0.8, "hallucination_rate": 0.1})
        result = runner.evaluate_gate(report)
        assert result.passed
        assert result.metrics["pass_rate"] == 0.8
        assert len(result.violations) == 0

    def test_gate_fail_low_pass_rate(self):
        runner = EnhancedEvaluationRunner(gate=QualityGate(min_pass_rate=0.8))
        report = self._make_report(5, 10, {"groundedness": 0.8, "hallucination_rate": 0.1})
        result = runner.evaluate_gate(report)
        assert not result.passed
        assert any("pass_rate" in v for v in result.violations)

    def test_gate_fail_high_hallucination(self):
        runner = EnhancedEvaluationRunner(gate=QualityGate(max_hallucination_rate=0.1))
        report = self._make_report(8, 10, {"groundedness": 0.8, "hallucination_rate": 0.5})
        result = runner.evaluate_gate(report)
        assert not result.passed
        assert any("hallucination_rate" in v for v in result.violations)

    def test_gate_fail_low_groundedness(self):
        runner = EnhancedEvaluationRunner(gate=QualityGate(min_groundedness=0.8))
        report = self._make_report(8, 10, {"groundedness": 0.3, "hallucination_rate": 0.1})
        result = runner.evaluate_gate(report)
        assert not result.passed
        assert any("groundedness" in v for v in result.violations)

    def test_gate_metrics(self):
        runner = EnhancedEvaluationRunner()
        report = self._make_report(9, 10, {"groundedness": 0.9, "hallucination_rate": 0.05})
        result = runner.evaluate_gate(report)
        assert "pass_rate" in result.metrics
        assert "avg_groundedness" in result.metrics
        assert "avg_hallucination_rate" in result.metrics


# ═══ Enhanced evaluation runner integration tests ═══

class TestEnhancedEvaluationRunner:

    def test_run_evaluation_with_grounding(self):
        runner = EnhancedEvaluationRunner()
        cases = [
            TestCase(
                name="test_1",
                input={"analysis": "The deal is worth 500K SAR"},
                expected={"confidence_min": 0.5},
                context_data={"deal_value": "500K SAR"},
            ),
        ]
        report = _run(runner.run_evaluation("test_agent", cases))
        assert report.total == 1
        assert report.results[0].details["groundedness"] > 0
        assert "hallucination_rate" in report.results[0].details

    def test_run_evaluation_with_gate(self):
        gate = QualityGate(min_faithfulness=0.0, min_relevance=0.0, min_accuracy=0.0, min_groundedness=0.0)
        runner = EnhancedEvaluationRunner(gate=gate)
        cases = [
            TestCase(
                name="test_1",
                input={"analysis": "The deal is worth 500K SAR"},
                expected={"confidence_min": 0.5},
                context_data={"deal_value": "500K SAR"},
            ),
        ]
        report = _run(runner.run_evaluation("test_agent", cases))
        gate_result = runner.evaluate_gate(report)
        assert gate_result.passed
