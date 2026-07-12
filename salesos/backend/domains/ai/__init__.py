"""AI domain — evaluation framework, prompt registry, and model-agnostic service."""
from domains.ai.models import AIModel, PromptTemplate, AIEvaluation, EvaluationMetric
from domains.ai.registry import PromptRegistry
from domains.ai.evaluator import AIEvaluator, BUILTIN_METRICS
from domains.ai.service import AIService, AIProvider, OpenAIProvider, DecisionPlatformProvider

__all__ = [
    "AIModel",
    "PromptTemplate",
    "AIEvaluation",
    "EvaluationMetric",
    "PromptRegistry",
    "AIEvaluator",
    "BUILTIN_METRICS",
    "AIService",
    "AIProvider",
    "OpenAIProvider",
    "DecisionPlatformProvider",
]
