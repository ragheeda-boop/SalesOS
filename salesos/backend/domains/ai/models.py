"""AI domain models — evaluation, prompts, and model abstraction."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EvaluationMetric:
    name: str
    value: float
    threshold: float
    passed: bool


@dataclass
class AIEvaluation:
    id: str
    prompt_id: str
    input: str
    output: str
    expected: str | None = None
    score: float = 0.0
    metrics: list[EvaluationMetric] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PromptTemplate:
    id: str
    name: str
    version: str
    template: str
    variables: list[str] = field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    domain: str = ""
    active: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AIModel:
    provider: str
    model_name: str
    capabilities: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
