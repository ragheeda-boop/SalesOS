"""SalesOS intelligence package.

Subpackages are imported explicitly (e.g. ``intelligence.activity_intelligence``)
to avoid eager loading of optional LLM provider dependencies at import time.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "ProviderFactory",
    "get_provider",
    "CompanyIntelligenceEngine",
    "EnrichmentService",
    "MarketIntelligenceEngine",
    "RelationshipGraphService",
    "SignalEngine",
    "RevenueBrain",
    "DataFabric",
    "AgentCoordinator",
    "TwinEngine",
    "SimulationEngine",
    "DecisionIntelligence",
]

_LAZY_MAP = {
    "LLMProvider": "intelligence.providers.protocol:LLMProvider",
    "OpenAIProvider": "intelligence.providers.openai_provider:OpenAIProvider",
    "ProviderFactory": "intelligence.providers.factory:ProviderFactory",
    "get_provider": "intelligence.providers.factory:get_provider",
    "CompanyIntelligenceEngine": "intelligence.company:CompanyIntelligenceEngine",
    "EnrichmentService": "intelligence.enrichment:EnrichmentService",
    "MarketIntelligenceEngine": "intelligence.market:MarketIntelligenceEngine",
    "RelationshipGraphService": "intelligence.graph:RelationshipGraphService",
    "SignalEngine": "intelligence.signals:SignalEngine",
    "RevenueBrain": "intelligence.revenue_brain:RevenueBrain",
    "DataFabric": "intelligence.data_fabric:DataFabric",
    "AgentCoordinator": "intelligence.agents:AgentCoordinator",
    "TwinEngine": "intelligence.digital_twin:TwinEngine",
    "SimulationEngine": "intelligence.simulation:SimulationEngine",
    "DecisionIntelligence": "intelligence.simulation:DecisionIntelligence",
}


def __getattr__(name: str) -> Any:
    target = _LAZY_MAP.get(name)
    if not target:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_path, attr = target.split(":")
    import importlib

    module = importlib.import_module(module_path)
    value = getattr(module, attr)
    globals()[name] = value
    return value
