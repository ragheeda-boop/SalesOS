from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TestCase:
    name: str
    input: dict[str, Any]
    expected: dict[str, Any]
    context_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    test_name: str
    passed: bool
    faithfulness: float
    relevance: float
    accuracy: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalReport:
    agent_name: str
    total: int
    passed: int
    avg_faithfulness: float
    avg_relevance: float
    avg_accuracy: float
    results: list[EvalResult]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationRunner:
    def __init__(self, test_cases_dir: str | None = None):
        self._test_cases_dir = test_cases_dir

    async def run_evaluation(self, agent_name: str, test_cases: list[TestCase]) -> EvalReport:
        results: list[EvalResult] = []
        for tc in test_cases:
            faithfulness = await self.measure_faithfulness(tc.input, tc.context_data)
            relevance = await self.measure_relevance(tc.input, tc.input.get("goal", ""))
            accuracy = await self.calculate_accuracy(tc.input, tc.expected)
            passed = (
                faithfulness >= 0.6
                and relevance >= 0.5
                and accuracy >= 0.5
            )
            results.append(EvalResult(
                test_name=tc.name,
                passed=passed,
                faithfulness=round(faithfulness, 3),
                relevance=round(relevance, 3),
                accuracy=round(accuracy, 3),
                details={
                    "input_keys": list(tc.input.keys()),
                    "expected_checks": list(tc.expected.keys()),
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

    async def measure_faithfulness(
        self, agent_output: dict[str, Any], source_data: dict[str, Any]
    ) -> float:
        if not source_data:
            return 0.0
        analysis = str(agent_output.get("analysis", ""))
        if not analysis:
            return 0.0
        source_text = str(source_data)
        contained = sum(1 for word in analysis.split()[:20] if word in source_text)
        total = min(len(analysis.split()), 20)
        return contained / max(total, 1)

    async def measure_relevance(
        self, agent_output: dict[str, Any], query: str
    ) -> float:
        if not query:
            return 0.5
        analysis = str(agent_output.get("analysis", "")).lower()
        query_words = [w for w in query.lower().split() if len(w) > 2]
        if not query_words:
            return 0.5
        matched = sum(1 for w in query_words if w in analysis)
        return matched / len(query_words)

    async def calculate_accuracy(
        self, agent_output: dict[str, Any], expected: dict[str, Any]
    ) -> float:
        checks = []
        if expected.get("has_competitors"):
            checks.append(bool(agent_output.get("competitors")))
        if expected.get("has_market_position"):
            checks.append(bool(agent_output.get("market_position")))
        if expected.get("has_agenda"):
            checks.append(bool(agent_output.get("agenda")))
        if expected.get("has_talking_points"):
            checks.append(bool(agent_output.get("talking_points")))
        if "evidence_count_min" in expected:
            checks.append(len(agent_output.get("evidence", [])) >= expected["evidence_count_min"])
        if "sources_count_min" in expected:
            checks.append(len(agent_output.get("sources", [])) >= expected["sources_count_min"])
        if "confidence_min" in expected:
            checks.append(agent_output.get("confidence", 0) >= expected["confidence_min"])
        if not checks:
            return 1.0
        return sum(1 for c in checks if c) / len(checks)

    def load_test_cases(self, agent_name: str) -> list[TestCase]:
        if not self._test_cases_dir:
            return []
        cases = []
        for filename in os.listdir(self._test_cases_dir):
            if filename.endswith((".yaml", ".yml")) and agent_name in filename:
                path = os.path.join(self._test_cases_dir, filename)
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                cases.append(TestCase(
                    name=filename.replace(".yaml", "").replace(".yml", ""),
                    input=data.get("input", {}),
                    expected=data.get("expected", {}),
                    context_data=data.get("context_data", {}),
                ))
        return cases

    def generate_report(self, report: EvalReport) -> str:
        lines = [
            f"تقرير تقييم: {report.agent_name}",
            f"التاريخ: {report.generated_at.isoformat()}",
            "",
            f"النتائج: {report.passed}/{report.total} اختبار ناجح",
            f"متوسط الدقة (Accuracy): {report.avg_accuracy:.1%}",
            f"متوسط الالتزام (Faithfulness): {report.avg_faithfulness:.1%}",
            f"متوسط الملاءمة (Relevance): {report.avg_relevance:.1%}",
            "",
            "تفاصيل الاختبارات:",
        ]
        for r in report.results:
            status = "✅" if r.passed else "❌"
            lines.append(f"  {status} {r.test_name}")
            lines.append(f"     Faithfulness: {r.faithfulness:.1%}, Relevance: {r.relevance:.1%}, Accuracy: {r.accuracy:.1%}")
        return "\n".join(lines)
