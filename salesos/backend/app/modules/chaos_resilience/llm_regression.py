"""STORY-14-07 — LLM regression suite (non-prod).

Golden-output fixtures + similarity scoring. Detects deliberately injected
quality regressions. No live LLM. feature_ai_copilot remains False.
Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config import settings
from typing import Any, Literal

VALID_LLM_REGRESSION_MODES: frozenset[str] = frozenset(
    {
        "baseline",
        "injected_regression",
        "promote_gate",
    }
)

# Minimum token-Jaccard similarity vs golden reference to pass a case.
SIMILARITY_THRESHOLD: float = 0.70

ModelMode = Literal["good", "degraded"]


@dataclass(frozen=True)
class GoldenCase:
    """Fixed prompt + human-acceptable reference output (fixture only)."""

    case_id: str
    prompt_id: str
    input: str
    reference: str
    required_keywords: tuple[str, ...] = ()


GOLDEN_CASES: tuple[GoldenCase, ...] = (
    GoldenCase(
        case_id="icp_summary_v1",
        prompt_id="gtm.icp.summary.v1",
        input="Summarize ICP for B2B SaaS mid-market in GCC.",
        reference=(
            "Target mid-market B2B SaaS buyers in GCC with 50-500 employees, "
            "clear buying committee, and budget for governed sales tooling."
        ),
        required_keywords=("mid-market", "GCC", "B2B"),
    ),
    GoldenCase(
        case_id="outreach_draft_v1",
        prompt_id="gtm.ai_outreach.v1",
        input="Draft a short outreach opener for a VP Sales.",
        reference=(
            "Hi {{first_name}}, noticed your team is scaling outbound in the region. "
            "Happy to share how peers keep AI-assist drafts human-reviewed."
        ),
        required_keywords=("human-reviewed", "outbound"),
    ),
    GoldenCase(
        case_id="decision_honesty_v1",
        prompt_id="studio.ai_policies.v1",
        input="State the AI honesty principle for tenant-facing copy.",
        reference=(
            "AI assists. Humans decide. Evidence governs. Do not market stubs as live GA AI."
        ),
        required_keywords=("Humans decide", "Evidence governs"),
    ),
)


def token_jaccard(a: str, b: str) -> float:
    """Case-insensitive word-level Jaccard similarity in [0, 1]."""
    ta = {t for t in a.lower().split() if t}
    tb = {t for t in b.lower().split() if t}
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def fixture_model_output(case: GoldenCase, mode: ModelMode) -> str:
    """Deterministic fake model — never opens a network socket."""
    if mode == "good":
        return case.reference
    # Deliberate quality regression: strip substance, invent fluff.
    return (
        f"Lorem ipsum placeholder reply for {case.case_id}. "
        "This output ignores the prompt and omits required domain keywords."
    )


@dataclass
class CaseResult:
    case_id: str
    prompt_id: str
    similarity: float
    keywords_ok: bool
    passed: bool
    output: str
    reference: str
    threshold: float = SIMILARITY_THRESHOLD

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "prompt_id": self.prompt_id,
            "similarity": round(self.similarity, 4),
            "keywords_ok": self.keywords_ok,
            "passed": self.passed,
            "threshold": self.threshold,
            "output": self.output,
            "reference": self.reference,
        }


@dataclass
class RegressionRunResult:
    mode: str
    ok: bool
    baseline_established: bool
    regression_detected: bool
    promotion_blocked: bool
    cases_passed: int
    cases_total: int
    similarity_threshold: float = SIMILARITY_THRESHOLD
    case_results: list[CaseResult] = field(default_factory=list)
    feature_ai_copilot: bool = field(default_factory=lambda: settings.feature_ai_copilot)
    live_llm: bool = False
    honesty: str = (
        "Non-prod LLM regression suite (golden fixtures + similarity). "
        "Live LLM / feature_ai_copilot / Production GO not claimed."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ok": self.ok,
            "baseline_established": self.baseline_established,
            "regression_detected": self.regression_detected,
            "promotion_blocked": self.promotion_blocked,
            "cases_passed": self.cases_passed,
            "cases_total": self.cases_total,
            "similarity_threshold": self.similarity_threshold,
            "case_results": [c.as_dict() for c in self.case_results],
            "feature_ai_copilot": self.feature_ai_copilot,
            "live_llm": self.live_llm,
            "honesty": self.honesty,
        }


def evaluate_case(case: GoldenCase, output: str) -> CaseResult:
    sim = token_jaccard(output, case.reference)
    keywords_ok = all(k.lower() in output.lower() for k in case.required_keywords)
    passed = sim >= SIMILARITY_THRESHOLD and keywords_ok
    return CaseResult(
        case_id=case.case_id,
        prompt_id=case.prompt_id,
        similarity=sim,
        keywords_ok=keywords_ok,
        passed=passed,
        output=output,
        reference=case.reference,
    )


def run_llm_regression(mode: str) -> RegressionRunResult:
    """Run golden suite under baseline or injected-regression fixture model."""
    kind = (mode or "").strip().lower()
    if kind not in VALID_LLM_REGRESSION_MODES:
        raise ValueError(
            f"unknown mode={mode!r}; expected one of {sorted(VALID_LLM_REGRESSION_MODES)}"
        )

    model_mode: ModelMode = "degraded" if kind == "injected_regression" else "good"
    results = [evaluate_case(case, fixture_model_output(case, model_mode)) for case in GOLDEN_CASES]
    passed_n = sum(1 for r in results if r.passed)
    total = len(results)
    all_pass = passed_n == total
    any_fail = passed_n < total

    if kind == "baseline":
        # Baseline established only when every golden case passes.
        return RegressionRunResult(
            mode=kind,
            ok=all_pass,
            baseline_established=all_pass,
            regression_detected=False,
            promotion_blocked=False,
            cases_passed=passed_n,
            cases_total=total,
            case_results=results,
        )

    if kind == "injected_regression":
        # Success = suite detects the injected quality drop.
        detected = any_fail
        return RegressionRunResult(
            mode=kind,
            ok=detected,
            baseline_established=False,
            regression_detected=detected,
            promotion_blocked=False,
            cases_passed=passed_n,
            cases_total=total,
            case_results=results,
        )

    # promote_gate: simulate promotion attempt after a degraded model would fail.
    degraded = [
        evaluate_case(case, fixture_model_output(case, "degraded")) for case in GOLDEN_CASES
    ]
    degraded_fail = any(not r.passed for r in degraded)
    blocked = degraded_fail
    return RegressionRunResult(
        mode=kind,
        ok=blocked,  # gate correctly blocks promotion when regression present
        baseline_established=False,
        regression_detected=degraded_fail,
        promotion_blocked=blocked,
        cases_passed=sum(1 for r in degraded if r.passed),
        cases_total=len(degraded),
        case_results=degraded,
    )
