"""
Layer 4: Data Fabric
Connectors → Import/Sync → Validation → Identity Resolution → Entity Matching → Data Quality → Trust → Knowledge Graph
"""
from .connectors import ConnectorEngine, Connector, ConnectorType, ConnectorStatus
from .identity_resolution import IdentityResolver, ResolvedIdentity
from .entity_matching import EntityMatcher, MatchResult
from .quality import DataQualityEngine, QualityScore, FreshnessScore
from .fabric import DataFabric

__all__ = [
    "ConnectorEngine", "Connector", "ConnectorType", "ConnectorStatus",
    "IdentityResolver", "ResolvedIdentity",
    "EntityMatcher", "MatchResult",
    "DataQualityEngine", "QualityScore", "FreshnessScore",
    "DataFabric",
]
