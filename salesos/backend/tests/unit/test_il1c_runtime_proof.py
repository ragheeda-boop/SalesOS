"""IL-1C: Runtime Proof — signal-decision-agent flow invariants."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from intelligence.signals import SignalEngine, BuyingSignal, Recommendation
from intelligence.business_objects import SignalType
from intelligence.signals.marketplace_bridge import (
    SignalMarketplaceBridge,
    _map_priority,
    _resolve_signal_type,
    create_bridge,
)
from app.modules.signal_marketplace.models import Signal, SignalEvent
from app.modules.signal_marketplace.service import SignalMarketplaceService


class TestCanonicalSignalPath:
    def test_domain_to_signal_type_mapping(self):
        assert _resolve_signal_type(Signal(id="s1", name="F", domain="funding")) == SignalType.FUNDING
        assert _resolve_signal_type(Signal(id="s2", name="H", domain="hiring")) == SignalType.HIRING

    def test_unknown_defaults_to_news(self):
        assert _resolve_signal_type(Signal(id="sx", name="X", domain="xyz")) == SignalType.NEWS

    def test_map_priority(self):
        assert _map_priority("critical").value == "high"
        assert _map_priority("medium").value == "medium"

    def test_create_bridge_factory(self):
        bridge = create_bridge(SignalMarketplaceService(), SignalEngine())
        assert isinstance(bridge, SignalMarketplaceBridge)


class TestRevenueBrainWiring:
    def test_revenue_brain_accepts_decision_center(self):
        from intelligence.revenue_brain import RevenueBrain
        from intelligence.company import CompanyIntelligenceEngine
        from intelligence.enrichment import EnrichmentService
        ce = CompanyIntelligenceEngine()
        brain = RevenueBrain(
            company_engine=ce,
            signal_engine=SignalEngine(),
            market_engine=MagicMock(),
            graph_service=MagicMock(),
            enrichment_service=EnrichmentService(company_engine=ce),
            decision_center=MagicMock(),
        )
        assert brain._decision_center is not None

    def test_revenue_brain_without_decision_center(self):
        from intelligence.revenue_brain import RevenueBrain
        from intelligence.company import CompanyIntelligenceEngine
        from intelligence.enrichment import EnrichmentService
        ce = CompanyIntelligenceEngine()
        brain = RevenueBrain(
            company_engine=ce,
            signal_engine=SignalEngine(),
            market_engine=MagicMock(),
            graph_service=MagicMock(),
            enrichment_service=EnrichmentService(company_engine=ce),
        )
        assert brain._decision_center is None


class TestNBASignalReady:
    def test_nba_accepts_signal_engine(self):
        from runtime.nba_engine import NBAEngine
        engine = NBAEngine(session_factory=MagicMock, signal_engine=SignalEngine())
        assert engine._signal_engine is not None

    def test_nba_without_signal_engine(self):
        from runtime.nba_engine import NBAEngine
        engine = NBAEngine(session_factory=MagicMock)
        assert engine._signal_engine is None


class TestSignalToRecommendation:
    def test_signal_produces_nba(self):
        engine = SignalEngine()
        engine.ingest_signal(company_id="c1", signal_type=SignalType.FUNDING, title="T", intensity=0.95, source="test")
        nba = engine.get_next_best_action("c1")
        assert nba is not None
        assert nba.category.value == "next_best_action"

    def test_signal_produces_recommendations(self):
        engine = SignalEngine()
        engine.ingest_signal(company_id="c1", signal_type=SignalType.FUNDING, title="T", source="test")
        recs = engine.get_recommendations("c1")
        assert len(recs) > 0


class TestStageConsistency:
    def test_backend_stages_match(self):
        from domains.commercial.opportunity.contracts.models import OpportunityStage
        names = {s.name for s in OpportunityStage.default_pipeline()}
        assert names == {"prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"}

    def test_pipeline_count(self):
        from domains.commercial.opportunity.contracts.models import OpportunityStage
        assert len(OpportunityStage.default_pipeline()) == 6


class TestImportChain:
    def test_core_imports(self):
        from intelligence.revenue_brain import RevenueBrain
        from intelligence.company import CompanyIntelligenceEngine
        from intelligence.signals.marketplace_bridge import SignalMarketplaceBridge
        from runtime.nba_engine import NBAEngine
        assert True
