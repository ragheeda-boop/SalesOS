"""Evaluation configuration for AI agent quality gates."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationConfig:
    """Configuration for AI evaluation suite."""
    min_grounding_confidence: float = 0.3
    min_faithfulness_score: float = 0.7
    max_hallucination_ratio: float = 0.2
    required_sources_per_agent: int = 1
    eval_models: list[str] = field(default_factory=lambda: ["gpt-4o-mini"])
    faithfulness_eval_model: str = "gpt-4o-mini"
    max_evals_per_run: int = 10
    output_dir: str = "reports/evaluation"


EVAL_CONFIG = EvaluationConfig()


AGENT_EVAL_MAP: dict[str, dict[str, Any]] = {
    "competitor": {
        "required_fields": ["analysis", "confidence", "competitors", "market_position"],
        "min_confidence": 0.3,
        "grounding_requirements": ["company_info", "relationships"],
    },
    "research": {
        "required_fields": ["analysis", "key_facts", "opportunities"],
        "min_confidence": 0.3,
        "grounding_requirements": ["company_info"],
    },
    "meeting": {
        "required_fields": ["analysis", "agenda", "talking_points"],
        "min_confidence": 0.3,
        "grounding_requirements": ["contacts", "recent_activity"],
    },
    "pricing": {
        "required_fields": ["analysis", "confidence"],
        "min_confidence": 0.3,
        "grounding_requirements": ["opportunities"],
    },
    "forecast": {
        "required_fields": ["analysis", "predicted_revenue"],
        "min_confidence": 0.3,
        "grounding_requirements": ["opportunities"],
    },
}
