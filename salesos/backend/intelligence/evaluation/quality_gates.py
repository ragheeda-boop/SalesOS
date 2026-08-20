"""AI Evaluation — groundedness, hallucination detection, quality gates.

P3-6: Extends EvaluationRunner with:
- Groundedness scoring (source-grounded vs. hallucinated claims)
- Hallucination detection (factual claims not in source)
- Quality gate enforcement (pass/fail thresholds for CI)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .runner import EvalReport, EvalResult, EvaluationRunner, TestCase


# ── Quality gate thresholds ────────────────────────────────────────

@dataclass(frozen=True)
class QualityGate:
    """Pass/fail thresholds for AI evaluation quality gates."""
    min_faithfulness: float = 0.6
    min_relevance: float = 0.5
    min_accuracy: float = 0.5
    min_groundedness: float = 0.6
    max_hallucination_rate: float = 0.3
    min_pass_rate: float = 0.7  # % of test cases that must pass


@dataclass
class GateResult:
    """Result of evaluating a quality gate against an EvalReport."""
    gate_name: str
    passed: bool
    metrics: dict[str, float]
    violations: list[str] = field(default_factory=list)


# ── Groundedness scorer ──────────────────────────────────────────

class GroundednessScorer:
    """Scores how well AI output is grounded in source/context data."""

    def score(self, output_text: str, source_text: str) -> float:
        if not output_text or not source_text:
            return 0.0
        output_words = set(self._tokenize(output_text))
        source_words = set(self._tokenize(source_text))
        if not output_words:
            return 0.0
        grounded = output_words & source_words
        return len(grounded) / len(output_words)

    def _tokenize(self, text: str) -> list[str]:
        words = re.findall(r'\b[a-zA-Z0-9\u0600-\u06FF]{3,}\b', text.lower())
        return [w for w in words if w not in _STOP_WORDS]


_STOP_WORDS = frozenset({
    "the", "and", "is", "in", "to", "for", "of", "that", "with", "on",
    "at", "by", "from", "or", "an", "this", "are", "was", "be", "has",
    "have", "been", "will", "would", "could", "should", "may", "can",
    "not", "but", "if", "so", "than", "too", "very", "just", "about",
    "more", "some", "any", "each", "all", "both", "few", "many", "much",
    "their", "there", "then", "when", "where", "how", "what", "which",
    "who", "whom", "whose", "why", "its", "it", "he", "she", "they",
    "we", "you", "me", "him", "her", "us", "them", "my", "your",
    "his", "our", "your", "their", "this", "that", "these", "those",
})


# ── Hallucination detector ────────────────────────────────────────

@dataclass
class HallucinationResult:
    """Result of hallucination detection on a text."""
    claims_total: int
    claims_supported: int
    claims_unsupported: int
    hallucination_rate: float
    unsupported_claims: list[str] = field(default_factory=list)


class HallucinationDetector:
    """Detects factual claims in AI output not supported by source data."""

    def detect(self, output_text: str, source_text: str) -> HallucinationResult:
        claims = self._extract_claims(output_text)
        if not claims:
            return HallucinationResult(
                claims_total=0, claims_supported=0,
                claims_unsupported=0, hallucination_rate=0.0,
            )

        supported = 0
        unsupported = []
        source_lower = source_text.lower()
        for claim in claims:
            if self._is_supported(claim, source_lower):
                supported += 1
            else:
                unsupported.append(claim)

        total = len(claims)
        hallucination_rate = (total - supported) / max(total, 1)
        return HallucinationResult(
            claims_total=total,
            claims_supported=supported,
            claims_unsupported=total - supported,
            hallucination_rate=round(hallucination_rate, 3),
            unsupported_claims=unsupported,
        )

    def _extract_claims(self, text: str) -> list[str]:
        sentences = re.split(r'[.!?؟\n]+', text)
        claims = []
        for s in sentences:
            s = s.strip()
            if len(s) > 15 and not s.startswith(('*', '-', '#')):
                claims.append(s)
        return claims

    def _tokenize(self, text: str) -> list[str]:
        words = re.findall(r'\b[a-zA-Z0-9\u0600-\u06FF]{3,}\b', text.lower())
        return [w for w in words if w not in _STOP_WORDS]

    def _is_supported(self, claim: str, source_lower: str) -> bool:
        claim_words = set(self._tokenize(claim))
        source_words = set(re.findall(r'\b[a-zA-Z0-9\u0600-\u06FF]{3,}\b', source_lower))
        if not claim_words:
            return True
        overlap = claim_words & source_words
        return len(overlap) / len(claim_words) >= 0.4


# ── Enhanced evaluation runner ──────────────────────────────────────

class EnhancedEvaluationRunner(EvaluationRunner):
    """P3-6: Enhanced evaluation runner with groundedness + hallucination + quality gates."""

    def __init__(self, test_cases_dir: str | None = None, gate: QualityGate | None = None):
        super().__init__(test_cases_dir)
        self._gate = gate or QualityGate()
        self._groundedness = GroundednessScorer()
        self._hallucination = HallucinationDetector()

    async def run_evaluation(self, agent_name: str, test_cases: list[TestCase]) -> EvalReport:
        results: list[EvalResult] = []
        for tc in test_cases:
            faithfulness = await self.measure_faithfulness(tc.input, tc.context_data)
            relevance = await self.measure_relevance(tc.input, tc.input.get("goal", ""))
            accuracy = await self.calculate_accuracy(tc.input, tc.expected)

            output_text = str(tc.input.get("analysis", "") or tc.input.get("goal", ""))
            source_text = str(tc.context_data) if tc.context_data else str(tc.input)

            groundedness = self._groundedness.score(output_text, source_text)
            hallucination = self._hallucination.detect(output_text, source_text)

            passed = (
                faithfulness >= self._gate.min_faithfulness
                and relevance >= self._gate.min_relevance
                and accuracy >= self._gate.min_accuracy
                and groundedness >= self._gate.min_groundedness
                and hallucination.hallucination_rate <= self._gate.max_hallucination_rate
            )

            results.append(EvalResult(
                test_name=tc.name,
                passed=passed,
                faithfulness=round(faithfulness, 3),
                relevance=round(relevance, 3),
                accuracy=round(accuracy, 3),
                details={
                    "groundedness": round(groundedness, 3),
                    "hallucination_rate": hallucination.hallucination_rate,
                    "claims_total": hallucination.claims_total,
                    "claims_supported": hallucination.claims_supported,
                    "unsupported_claims": hallucination.unsupported_claims[:3],
                },
            ))

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        return EvalReport(
            agent_name=agent_name,
            total=total,
            passed=passed_count,
            avg_faithfulness=round(sum(r.faithfulness for r in results) / max(total, 1), 3),
            avg_relevance=round(sum(r.relevance for r in results) / max(total, 1), 3),
            avg_accuracy=round(sum(r.accuracy for r in results) / max(total, 1), 3),
            results=results,
        )

    def evaluate_gate(self, report: EvalReport) -> GateResult:
        violations = []
        pass_rate = report.passed / max(report.total, 1)
        if pass_rate < self._gate.min_pass_rate:
            violations.append(f"pass_rate={pass_rate:.1%} < {self._gate.min_pass_rate:.1%}")
        if report.avg_faithfulness < self._gate.min_faithfulness:
            violations.append(f"faithfulness={report.avg_faithfulness:.1%} < {self._gate.min_faithfulness:.1%}")
        if report.avg_relevance < self._gate.min_relevance:
            violations.append(f"relevance={report.avg_relevance:.1%} < {self._gate.min_relevance:.1%}")
        if report.avg_accuracy < self._gate.min_accuracy:
            violations.append(f"accuracy={report.avg_accuracy:.1%} < {self._gate.min_accuracy:.1%}")

        halluc_rates = [
            r.details.get("hallucination_rate", 0) for r in report.results
        ]
        avg_halluc = sum(halluc_rates) / max(len(halluc_rates), 1)
        if avg_halluc > self._gate.max_hallucination_rate:
            violations.append(f"hallucination_rate={avg_halluc:.1%} > {self._gate.max_hallucination_rate:.1%}")

        grounded_scores = [
            r.details.get("groundedness", 0) for r in report.results
        ]
        avg_grounded = sum(grounded_scores) / max(len(grounded_scores), 1)
        if avg_grounded < self._gate.min_groundedness:
            violations.append(f"groundedness={avg_grounded:.1%} < {self._gate.min_groundedness:.1%}")

        return GateResult(
            gate_name="ai_quality",
            passed=len(violations) == 0,
            metrics={
                "pass_rate": round(pass_rate, 3),
                "avg_faithfulness": report.avg_faithfulness,
                "avg_relevance": report.avg_relevance,
                "avg_accuracy": report.avg_accuracy,
                "avg_groundedness": round(avg_grounded, 3),
                "avg_hallucination_rate": round(avg_halluc, 3),
            },
            violations=violations,
        )
