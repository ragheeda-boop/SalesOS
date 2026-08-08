"""Tests for Decision Center domain — models, repository, service, and router."""

from __future__ import annotations

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from typing import Any

from domains.decision_center.models import (
    Decision,
    DecisionAudit,
    DecisionDomain,
    DecisionFeedback,
    DecisionStatus,
    DecisionTemplate,
    DecisionType,
    EnsembleVote,
    FeedbackAggregate,
    FeedbackRating,
)
from domains.decision_center.repository import InMemoryDecisionCenterRepository
from domains.decision_center.service import DecisionCenterService


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def repo() -> InMemoryDecisionCenterRepository:
    return InMemoryDecisionCenterRepository()


@pytest.fixture
def svc(repo: InMemoryDecisionCenterRepository) -> DecisionCenterService:
    return DecisionCenterService(repo)


TENANT = "tenant-001"


# ── Models Tests ──────────────────────────────────────────────────────


class TestModels:
    def test_decision_to_dict(self):
        d = Decision(
            id="d1",
            domain=DecisionDomain.PIPELINE,
            type=DecisionType.DEAL_SCORING,
            entity_id="e1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="Strong signals",
            provider="rule_engine",
        )
        result = d.to_dict()
        assert result["id"] == "d1"
        assert result["domain"] == "pipeline"
        assert result["type"] == "deal_scoring"
        assert result["confidence"] == 0.85
        assert result["isEnsemble"] is False
        assert result["ensembleVotes"] is None

    def test_decision_with_ensemble_votes(self):
        votes = [
            EnsembleVote(provider="openai", decision="pursue", confidence=0.9, reasoning="R1"),
            EnsembleVote(provider="anthropic", decision="pursue", confidence=0.8, reasoning="R2"),
        ]
        d = Decision(
            id="d2",
            domain=DecisionDomain.REVENUE,
            type=DecisionType.DEAL_PROGRESSION,
            entity_id="e2",
            entity_type="opportunity",
            decision="pursue",
            confidence=0.85,
            reasoning="Ensemble",
            provider="ensemble",
            ensemble_votes=votes,
            is_ensemble=True,
        )
        result = d.to_dict()
        assert result["isEnsemble"] is True
        assert len(result["ensembleVotes"]) == 2
        assert result["ensembleVotes"][0]["provider"] == "openai"

    def test_audit_to_dict(self):
        audit = DecisionAudit(
            decision_id="d1",
            input_context={"entity": "co1"},
            reasoning_steps=[{"step": 1, "desc": "check intent"}],
            confidence_breakdown={"intent": 0.8, "engagement": 0.6},
            provider_used="rule_engine",
            alternatives_considered=[{"action": "deprioritize", "confidence": 0.3}],
            timestamp=datetime.now(timezone.utc),
        )
        result = audit.to_dict()
        assert result["decisionId"] == "d1"
        assert result["providerUsed"] == "rule_engine"
        assert result["ensembleMetadata"] is None

    def test_feedback_to_dict(self):
        fb = DecisionFeedback(
            id="fb1",
            decision_id="d1",
            rating=FeedbackRating.UP,
            comment="Good decision",
            actor_id="user-1",
        )
        result = fb.to_dict()
        assert result["rating"] == "up"
        assert result["comment"] == "Good decision"

    def test_template_to_dict(self):
        t = DecisionTemplate(
            id="t1",
            name="Lead Qual",
            type=DecisionType.LEAD_QUALIFICATION,
            config={"threshold": 0.7},
        )
        result = t.to_dict()
        assert result["name"] == "Lead Qual"
        assert result["type"] == "lead_qualification"
        assert result["config"]["threshold"] == 0.7

    def test_feedback_aggregate_to_dict(self):
        agg = FeedbackAggregate(
            decision_type="deal_scoring",
            total_feedback=10,
            up_count=7,
            down_count=3,
            approval_rate=0.7,
        )
        result = agg.to_dict()
        assert result["approvalRate"] == 0.7

    def test_ensemble_vote_defaults(self):
        v = EnsembleVote(provider="test", decision="pursue", confidence=0.8, reasoning="x")
        assert v.raw_response is None
        assert v.latency_ms is None


# ── Repository Tests ──────────────────────────────────────────────────


class TestInMemoryRepository:
    @pytest.mark.asyncio
    async def test_save_and_get_decision(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.COMPANY,
            type=DecisionType.HEALTH,
            entity_id="co1",
            entity_type="company",
            decision="monitor",
            confidence=0.6,
            reasoning="neutral",
            provider="rule",
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        result = await repo.get_decision("d1", TENANT)
        assert result is not None
        assert result.id == "d1"
        assert await repo.get_decision("d1", "other-tenant") is None

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, repo: InMemoryDecisionCenterRepository):
        assert await repo.get_decision("missing", TENANT) is None

    @pytest.mark.asyncio
    async def test_list_decisions_filters_domain(self, repo: InMemoryDecisionCenterRepository):
        for i, domain in enumerate(["pipeline", "employee", "company"]):
            d = Decision(
                id=f"d{i}",
                domain=DecisionDomain(domain),
                type=DecisionType.OTHER,
                entity_id="e1",
                entity_type="company",
                decision="x",
                confidence=0.5,
                reasoning="r",
                provider="p",
                metadata={"tenant_id": TENANT},
            )
            await repo.save_decision(d)
        items, total = await repo.list_decisions(TENANT, domain="pipeline")
        assert total == 1
        assert items[0].domain.value == "pipeline"

    @pytest.mark.asyncio
    async def test_list_decisions_filters_type(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.PIPELINE,
            type=DecisionType.DEAL_SCORING,
            entity_id="e1",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        items, total = await repo.list_decisions(TENANT, decision_type="deal_scoring")
        assert total == 1
        items2, total2 = await repo.list_decisions(TENANT, decision_type="pricing")
        assert total2 == 0

    @pytest.mark.asyncio
    async def test_list_decisions_filters_confidence(self, repo: InMemoryDecisionCenterRepository):
        for i, conf in enumerate([0.3, 0.6, 0.9]):
            d = Decision(
                id=f"d{i}",
                domain=DecisionDomain.PIPELINE,
                type=DecisionType.DEAL_SCORING,
                entity_id="e1",
                entity_type="company",
                decision="x",
                confidence=conf,
                reasoning="r",
                provider="p",
                metadata={"tenant_id": TENANT},
            )
            await repo.save_decision(d)
        items, total = await repo.list_decisions(
            TENANT, confidence_min=0.5, confidence_max=0.7
        )
        assert total == 1
        assert items[0].confidence == 0.6

    @pytest.mark.asyncio
    async def test_list_decisions_filters_entity_id(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.COMPANY,
            type=DecisionType.HEALTH,
            entity_id="co-xyz",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        items, total = await repo.list_decisions(TENANT, entity_id="co-xyz")
        assert total == 1
        items2, total2 = await repo.list_decisions(TENANT, entity_id="co-other")
        assert total2 == 0

    @pytest.mark.asyncio
    async def test_save_and_get_audit(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.PIPELINE,
            type=DecisionType.DEAL_SCORING,
            entity_id="e1",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        audit = DecisionAudit(
            decision_id="d1",
            input_context={"a": 1},
            reasoning_steps=[{"step": 1}],
            confidence_breakdown={"c": 0.8},
            provider_used="openai",
            alternatives_considered=[],
            timestamp=datetime.now(timezone.utc),
        )
        await repo.save_audit(audit)
        result = await repo.get_audit("d1", TENANT)
        assert result is not None
        assert result.provider_used == "openai"
        assert await repo.get_audit("d1", "other-tenant") is None

    @pytest.mark.asyncio
    async def test_get_audit_missing_returns_none(self, repo: InMemoryDecisionCenterRepository):
        assert await repo.get_audit("missing", TENANT) is None

    @pytest.mark.asyncio
    async def test_save_and_get_feedback(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.PIPELINE,
            type=DecisionType.DEAL_SCORING,
            entity_id="e1",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        fb = DecisionFeedback(
            id="fb1",
            decision_id="d1",
            rating=FeedbackRating.DOWN,
            comment="Too aggressive",
        )
        await repo.save_feedback(fb)
        results = await repo.get_feedback_for_decision("d1", TENANT)
        assert len(results) == 1
        assert results[0].rating == FeedbackRating.DOWN
        assert await repo.get_feedback_for_decision("d1", "other-tenant") == []

    @pytest.mark.asyncio
    async def test_feedback_aggregation(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.PIPELINE,
            type=DecisionType.DEAL_SCORING,
            entity_id="e1",
            entity_type="company",
            decision="x",
            confidence=0.8,
            reasoning="r",
            provider="p",
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        for i in range(3):
            await repo.save_feedback(
                DecisionFeedback(id=f"fb{i}", decision_id="d1", rating=FeedbackRating.UP)
            )
        await repo.save_feedback(
            DecisionFeedback(id="fb3", decision_id="d1", rating=FeedbackRating.DOWN)
        )
        aggs = await repo.get_feedback_by_type(TENANT)
        assert len(aggs) == 1
        assert aggs[0].up_count == 3
        assert aggs[0].down_count == 1
        assert aggs[0].approval_rate == 0.75

    @pytest.mark.asyncio
    async def test_save_and_get_template(self, repo: InMemoryDecisionCenterRepository):
        t = DecisionTemplate(
            id="t1",
            name="Test Template",
            type=DecisionType.PRICING,
            config={"discount_max": 0.3},
        )
        await repo.save_template(t)
        result = await repo.get_template("t1")
        assert result is not None
        assert result.name == "Test Template"

    @pytest.mark.asyncio
    async def test_list_templates_filters_type(self, repo: InMemoryDecisionCenterRepository):
        await repo.save_template(
            DecisionTemplate(id="t1", name="A", type=DecisionType.PRICING, config={})
        )
        await repo.save_template(
            DecisionTemplate(id="t2", name="B", type=DecisionType.RENEWAL_RISK, config={})
        )
        items = await repo.list_templates("pricing")
        assert len(items) == 1
        assert items[0].name == "A"

    @pytest.mark.asyncio
    async def test_delete_template(self, repo: InMemoryDecisionCenterRepository):
        await repo.save_template(
            DecisionTemplate(id="t1", name="A", type=DecisionType.PRICING, config={})
        )
        deleted = await repo.delete_template("t1")
        assert deleted is True
        assert await repo.get_template("t1") is None

    @pytest.mark.asyncio
    async def test_update_template(self, repo: InMemoryDecisionCenterRepository):
        await repo.save_template(
            DecisionTemplate(id="t1", name="A", type=DecisionType.PRICING, config={"x": 1})
        )
        result = await repo.update_template("t1", {"name": "B", "config": {"y": 2}})
        assert result is not None
        assert result.name == "B"
        assert result.config == {"y": 2}

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, repo: InMemoryDecisionCenterRepository):
        assert await repo.update_template("missing", {"name": "X"}) is None

    @pytest.mark.asyncio
    async def test_list_decisions_pagination(self, repo: InMemoryDecisionCenterRepository):
        for i in range(5):
            d = Decision(
                id=f"d{i}",
                domain=DecisionDomain.GENERAL,
                type=DecisionType.OTHER,
                entity_id="e1",
                entity_type="company",
                decision="x",
                confidence=0.5,
                reasoning="r",
                provider="p",
                metadata={"tenant_id": TENANT},
            )
            await repo.save_decision(d)
        items, total = await repo.list_decisions(TENANT, limit=2, offset=0)
        assert total == 5
        assert len(items) == 2
        items2, total2 = await repo.list_decisions(TENANT, limit=2, offset=4)
        assert len(items2) == 1

    @pytest.mark.asyncio
    async def test_list_decisions_date_filters(self, repo: InMemoryDecisionCenterRepository):
        now = datetime.now(timezone.utc)
        d = Decision(
            id="d1",
            domain=DecisionDomain.GENERAL,
            type=DecisionType.OTHER,
            entity_id="e1",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            timestamp=now,
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        date_from = (now - timedelta(hours=1)).isoformat()
        items, total = await repo.list_decisions(TENANT, date_from=date_from)
        assert total == 1

        date_to = (now - timedelta(days=2)).isoformat()
        items2, total2 = await repo.list_decisions(TENANT, date_to=date_to)
        assert total2 == 0

    @pytest.mark.asyncio
    async def test_list_decisions_status_filter(self, repo: InMemoryDecisionCenterRepository):
        d = Decision(
            id="d1",
            domain=DecisionDomain.GENERAL,
            type=DecisionType.OTHER,
            entity_id="e1",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            status=DecisionStatus.ACTIVE,
            metadata={"tenant_id": TENANT},
        )
        await repo.save_decision(d)
        items, total = await repo.list_decisions(TENANT, status="active")
        assert total == 1
        items2, total2 = await repo.list_decisions(TENANT, status="accepted")
        assert total2 == 0


# ── Service Tests ─────────────────────────────────────────────────────


class TestDecisionCenterService:
    @pytest.mark.asyncio
    async def test_create_decision(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="Strong signals",
            provider="rule_engine",
            tenant_id=TENANT,
        )
        assert d.id
        assert d.domain.value == "pipeline"
        assert d.is_ensemble is False

    @pytest.mark.asyncio
    async def test_create_decision_clamps_confidence(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=1.5,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        assert d.confidence == 1.0

    @pytest.mark.asyncio
    async def test_list_decisions(self, svc: DecisionCenterService):
        await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        items, total = await svc.list_decisions(TENANT)
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_decision(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="company",
            decision_type="health",
            entity_id="co1",
            entity_type="company",
            decision="monitor",
            confidence=0.6,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        result = await svc.get_decision(d.id, TENANT)
        assert result is not None
        assert result.entity_id == "co1"
        assert await svc.get_decision(d.id, "other-tenant") is None

    @pytest.mark.asyncio
    async def test_get_decision_not_found(self, svc: DecisionCenterService):
        assert await svc.get_decision("missing", TENANT) is None

    @pytest.mark.asyncio
    async def test_cross_tenant_idor_blocked(self, svc: DecisionCenterService):
        """PROD-W2-001 / GA-P0-SEC-01: tenant A must not read tenant B decisions."""
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.9,
            reasoning="secret",
            provider="p",
            tenant_id=TENANT,
        )
        other = "tenant-attacker"
        # Direct access blocked
        assert await svc.get_decision(d.id, other) is None
        assert await svc.get_audit(d.id, other) is None
        assert await svc.get_feedback_for_decision(d.id, other) == []
        assert await svc.submit_feedback(d.id, "up", other) is None
        assert await svc.create_audit(
            decision_id=d.id,
            input_context={},
            reasoning_steps=[],
            confidence_breakdown={},
            provider_used="x",
            alternatives_considered=[],
            tenant_id=other,
        ) is None
        # Listing isolation: attacker must not see victim data
        items, total = await svc.list_decisions(other)
        assert total == 0
        # Feedback aggregation isolation
        aggs = await svc.get_feedback_aggregates(other)
        assert len(aggs) == 0

    @pytest.mark.asyncio
    async def test_create_audit(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        audit = await svc.create_audit(
            decision_id=d.id,
            input_context={"entity": "co1"},
            reasoning_steps=[{"step": 1, "description": "Check intent"}],
            confidence_breakdown={"intent": 0.9},
            provider_used="rule_engine",
            alternatives_considered=[{"action": "nurture"}],
            tenant_id=TENANT,
        )
        assert audit is not None
        assert audit.decision_id == d.id

    @pytest.mark.asyncio
    async def test_create_audit_not_found(self, svc: DecisionCenterService):
        result = await svc.create_audit(
            decision_id="missing",
            input_context={},
            reasoning_steps=[],
            confidence_breakdown={},
            provider_used="x",
            alternatives_considered=[],
            tenant_id=TENANT,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_audit(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        await svc.create_audit(
            decision_id=d.id,
            input_context={"x": 1},
            reasoning_steps=[],
            confidence_breakdown={},
            provider_used="openai",
            alternatives_considered=[],
            tenant_id=TENANT,
        )
        audit = await svc.get_audit(d.id, TENANT)
        assert audit is not None
        assert audit.provider_used == "openai"

    @pytest.mark.asyncio
    async def test_submit_feedback(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        fb = await svc.submit_feedback(d.id, "up", TENANT, comment="Good", actor_id="u1")
        assert fb is not None
        assert fb.rating == FeedbackRating.UP
        refreshed = await svc.get_decision(d.id, TENANT)
        assert refreshed is not None
        assert refreshed.status == DecisionStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_submit_feedback_down_rejects(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.4,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        fb = await svc.submit_feedback(d.id, "down", TENANT)
        assert fb is not None
        refreshed = await svc.get_decision(d.id, TENANT)
        assert refreshed is not None
        assert refreshed.status == DecisionStatus.REJECTED

    @pytest.mark.asyncio
    async def test_submit_feedback_not_found(self, svc: DecisionCenterService):
        result = await svc.submit_feedback("missing", "down", TENANT)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_feedback_for_decision(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        await svc.submit_feedback(d.id, "up", TENANT)
        await svc.submit_feedback(d.id, "down", TENANT, comment="Nope")
        feedbacks = await svc.get_feedback_for_decision(d.id, TENANT)
        assert len(feedbacks) == 2

    @pytest.mark.asyncio
    async def test_get_feedback_aggregates(self, svc: DecisionCenterService):
        d = await svc.create_decision(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            decision="pursue",
            confidence=0.85,
            reasoning="r",
            provider="p",
            tenant_id=TENANT,
        )
        await svc.submit_feedback(d.id, "up", TENANT)
        await svc.submit_feedback(d.id, "up", TENANT)
        await svc.submit_feedback(d.id, "down", TENANT)
        aggs = await svc.get_feedback_aggregates(TENANT)
        assert len(aggs) == 1
        assert aggs[0].up_count == 2

    @pytest.mark.asyncio
    async def test_create_template(self, svc: DecisionCenterService):
        t = await svc.create_template("Test", "pricing", {"max_discount": 0.2}, TENANT)
        assert t.id
        assert t.name == "Test"
        assert t.type.value == "pricing"

    @pytest.mark.asyncio
    async def test_get_template(self, svc: DecisionCenterService):
        t = await svc.create_template("Test", "pricing", {}, TENANT)
        result = await svc.get_template(t.id, TENANT)
        assert result is not None

    @pytest.mark.asyncio
    async def test_list_templates(self, svc: DecisionCenterService):
        await svc.create_template("A", "pricing", {}, TENANT)
        await svc.create_template("B", "renewal_risk", {}, TENANT)
        items = await svc.list_templates(template_type=None, tenant_id=TENANT)
        assert len(items) == 2
        items_filtered = await svc.list_templates(template_type="pricing", tenant_id=TENANT)
        assert len(items_filtered) == 1

    @pytest.mark.asyncio
    async def test_update_template(self, svc: DecisionCenterService):
        t = await svc.create_template("A", "pricing", {"x": 1}, TENANT)
        result = await svc.update_template(t.id, name="B", config={"y": 2}, tenant_id=TENANT)
        assert result is not None
        assert result.name == "B"

    @pytest.mark.asyncio
    async def test_delete_template(self, svc: DecisionCenterService):
        t = await svc.create_template("A", "pricing", {}, TENANT)
        deleted = await svc.delete_template(t.id, TENANT)
        assert deleted is True
        assert await svc.get_template(t.id, TENANT) is None

    @pytest.mark.asyncio
    async def test_seed_default_templates(self, svc: DecisionCenterService):
        templates = await svc.seed_default_templates(TENANT)
        assert len(templates) == 4
        names = {t.name for t in templates}
        assert "Lead Qualification" in names
        assert "Deal Progression" in names
        assert "Renewal Risk" in names
        assert "Pricing Optimization" in names

    @pytest.mark.asyncio
    async def test_ensemble_decide_majority_vote(self, svc: DecisionCenterService):
        async def provider_a(ctx: dict) -> dict:
            return {"provider": "openai", "decision": "pursue", "confidence": 0.9, "reasoning": "A"}

        async def provider_b(ctx: dict) -> dict:
            return {"provider": "anthropic", "decision": "pursue", "confidence": 0.8, "reasoning": "B"}

        d = await svc.ensemble_decide(
            domain="pipeline",
            decision_type="deal_progression",
            entity_id="co1",
            entity_type="company",
            tenant_id=TENANT,
            providers=[provider_a, provider_b],
            context={"deal_value": 150000},
            deal_value=150000,
        )
        assert d.is_ensemble is True
        assert d.provider == "ensemble"
        assert d.decision == "pursue"
        assert d.confidence == 0.85
        assert len(d.ensemble_votes) == 2

    @pytest.mark.asyncio
    async def test_ensemble_decide_split_vote(self, svc: DecisionCenterService):
        async def provider_a(ctx: dict) -> dict:
            return {"provider": "openai", "decision": "pursue", "confidence": 0.9, "reasoning": "A"}

        async def provider_b(ctx: dict) -> dict:
            return {"provider": "anthropic", "decision": "deprioritize", "confidence": 0.7, "reasoning": "B"}

        async def provider_c(ctx: dict) -> dict:
            return {"provider": "mistral", "decision": "pursue", "confidence": 0.75, "reasoning": "C"}

        d = await svc.ensemble_decide(
            domain="pipeline",
            decision_type="deal_progression",
            entity_id="co1",
            entity_type="company",
            tenant_id=TENANT,
            providers=[provider_a, provider_b, provider_c],
            context={},
        )
        assert d.decision == "pursue"
        assert len(d.ensemble_votes) == 3

    @pytest.mark.asyncio
    async def test_ensemble_decide_error_handling(self, svc: DecisionCenterService):
        async def failing_provider(ctx: dict) -> dict:
            raise RuntimeError("Provider crashed")

        async def working_provider(ctx: dict) -> dict:
            return {"provider": "openai", "decision": "pursue", "confidence": 0.8, "reasoning": "ok"}

        d = await svc.ensemble_decide(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            tenant_id=TENANT,
            providers=[failing_provider, working_provider],
            context={},
        )
        assert d.decision == "pursue"
        assert len(d.ensemble_votes) == 2
        error_vote = [v for v in d.ensemble_votes if v.decision == "error"]
        assert len(error_vote) == 1

    @pytest.mark.asyncio
    async def test_ensemble_decide_requires_two_providers(self, svc: DecisionCenterService):
        async def provider(ctx: dict) -> dict:
            return {"provider": "openai", "decision": "pursue", "confidence": 0.8, "reasoning": "ok"}

        with pytest.raises(ValueError, match="at least 2 providers"):
            await svc.ensemble_decide(
                domain="pipeline",
                decision_type="deal_scoring",
                entity_id="co1",
                entity_type="company",
                tenant_id=TENANT,
                providers=[provider],
                context={},
            )

    @pytest.mark.asyncio
    async def test_ensemble_all_errors_returns_insufficient_data(self, svc: DecisionCenterService):
        async def fail1(ctx: dict) -> dict:
            raise RuntimeError("err1")

        async def fail2(ctx: dict) -> dict:
            raise RuntimeError("err2")

        d = await svc.ensemble_decide(
            domain="pipeline",
            decision_type="deal_scoring",
            entity_id="co1",
            entity_type="company",
            tenant_id=TENANT,
            providers=[fail1, fail2],
            context={},
        )
        assert d.decision == "insufficient_data"
        assert d.confidence == 0.0

    @pytest.mark.asyncio
    async def test_create_audit_with_ensemble(self, svc: DecisionCenterService):
        async def p1(ctx):
            return {"provider": "openai", "decision": "pursue", "confidence": 0.9, "reasoning": "A"}

        async def p2(ctx):
            return {"provider": "anthropic", "decision": "pursue", "confidence": 0.8, "reasoning": "B"}

        d = await svc.ensemble_decide(
            domain="pipeline",
            decision_type="deal_progression",
            entity_id="co1",
            entity_type="company",
            tenant_id=TENANT,
            providers=[p1, p2],
            context={},
        )
        audit = await svc.create_audit(
            decision_id=d.id,
            input_context={"deal_value": 150000},
            reasoning_steps=[{"step": 1, "desc": "gather votes"}],
            confidence_breakdown={"openai": 0.9, "anthropic": 0.8},
            provider_used="ensemble",
            alternatives_considered=[],
            tenant_id=TENANT,
        )
        assert audit.ensemble_metadata is not None
        assert audit.ensemble_metadata["isEnsemble"] is True
        assert audit.ensemble_metadata["voteCount"] == 2
