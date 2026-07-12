"""Adapter bridging domain DecisionPlatform services to SDK scoring protocols.

The DashboardDecisionProvider depends on SDK interfaces (DecisionServiceProtocol,
RecommendationEngineProtocol). The actual implementations live in
domains.decision.* and use domain model types. This adapter converts between them.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sdk.scoring.interfaces import (
    DecisionContext as SDKDecisionContext,
    DecisionFactor as SDKDecisionFactor,
    DecisionServiceProtocol,
    Recommendation as SDKRecommendation,
    RecommendationEngineProtocol,
    RecommendationEvidence as SDKRecommendationEvidence,
)

from domains.decision.context.models import DecisionContext as DomainDecisionContext
from domains.decision.context.models import DecisionFactor as DomainDecisionFactor
from domains.decision.context.service import DecisionService
from domains.decision.recommendation.engine import RecommendationEngine
from domains.decision.recommendation.models import Recommendation as DomainRecommendation


class DecisionServiceAdapter(DecisionServiceProtocol):
    """Wraps the domain DecisionService to satisfy the SDK DecisionServiceProtocol."""

    def __init__(self, domain_service: DecisionService):
        self._service = domain_service

    async def build_context(
        self,
        tenant_id: str,
        target_id: str,
        target_type: str,
        factors: list[SDKDecisionFactor],
    ) -> SDKDecisionContext:
        domain_factors = [
            DomainDecisionFactor(
                source_layer=f.source_layer,
                source_domain=f.source_domain,
                key=f.key,
                value=f.value,
                label=f.label,
                severity=f.severity,
            )
            for f in factors
        ]
        domain_ctx = await self._service.build_context(
            tenant_id=tenant_id,
            target_id=target_id,
            target_type=target_type,
            factors=domain_factors,
        )
        return SDKDecisionContext(
            id=domain_ctx.id,
            tenant_id=domain_ctx.tenant_id,
            target_id=domain_ctx.target_id,
            target_type=domain_ctx.target_type,
            factors=[
                SDKDecisionFactor(
                    source_layer=f.source_layer,
                    source_domain=f.source_domain,
                    key=f.key,
                    value=f.value,
                    label=f.label,
                    severity=f.severity,
                )
                for f in domain_ctx.factors
            ],
        )

    async def get_latest_context(
        self, target_id: str, target_type: str
    ) -> Optional[SDKDecisionContext]:
        domain_ctx = await self._service.get_latest_context(target_id, target_type)
        if not domain_ctx:
            return None
        return SDKDecisionContext(
            id=domain_ctx.id,
            tenant_id=domain_ctx.tenant_id,
            target_id=domain_ctx.target_id,
            target_type=domain_ctx.target_type,
            factors=[
                SDKDecisionFactor(
                    source_layer=f.source_layer,
                    source_domain=f.source_domain,
                    key=f.key,
                    value=f.value,
                    label=f.label,
                    severity=f.severity,
                )
                for f in domain_ctx.factors
            ],
        )


class RecommendationEngineAdapter(RecommendationEngineProtocol):
    """Wraps the domain RecommendationEngine to satisfy the SDK RecommendationEngineProtocol."""

    def __init__(self, domain_engine: RecommendationEngine):
        self._engine = domain_engine

    async def evaluate(self, context: SDKDecisionContext) -> Optional[SDKRecommendation]:
        domain_factors = [
            DomainDecisionFactor(
                source_layer=f.source_layer,
                source_domain=f.source_domain,
                key=f.key,
                value=f.value,
                label=f.label,
                severity=f.severity,
            )
            for f in context.factors
        ]
        domain_ctx = DomainDecisionContext(
            id=context.id,
            tenant_id=context.tenant_id,
            target_id=context.target_id,
            target_type=context.target_type,
            factors=domain_factors,
        )
        domain_rec = await self._engine.evaluate(domain_ctx)
        if not domain_rec:
            return None
        return SDKRecommendation(
            title=domain_rec.title,
            description=domain_rec.description,
            confidence=domain_rec.confidence,
            evidence=[
                SDKRecommendationEvidence(
                    source_layer=e.source_layer,
                    source_domain=e.source_domain,
                    key=e.key,
                    value=e.value,
                    narrative=e.narrative,
                )
                for e in domain_rec.evidence
            ],
        )
