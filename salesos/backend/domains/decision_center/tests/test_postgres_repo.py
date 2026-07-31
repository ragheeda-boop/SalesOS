"""Tests for PostgresDecisionCenterRepository — the code path GA-P0-SEC-01
(Decision Center cross-tenant IDOR) actually lived in. The service-level
InMemoryDecisionCenterRepository tests in test_decision_center.py never
exercise real SQL, so they cannot catch a regression in the tenant_id
filtering here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from domains.decision_center.models import (
    Decision,
    DecisionAudit,
    DecisionDomain,
    DecisionFeedback,
    DecisionStatus,
    DecisionType,
    FeedbackRating,
)
from domains.decision_center.postgres_repo import PostgresDecisionCenterRepository

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"


def _decision(tenant_id: str, entity_id: str = "co1", reasoning: str = "secret") -> Decision:
    return Decision(
        id=str(uuid.uuid4()),
        domain=DecisionDomain.PIPELINE,
        type=DecisionType.DEAL_SCORING,
        entity_id=entity_id,
        entity_type="company",
        decision="pursue",
        confidence=0.9,
        reasoning=reasoning,
        provider="rule_engine",
        status=DecisionStatus.ACTIVE,
        timestamp=datetime.now(timezone.utc),
        metadata={"tenant_id": tenant_id},
    )


class TestSaveAndGet:
    @pytest.mark.asyncio
    async def test_save_and_get_decision_scoped_to_tenant(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        dec = await repo.save_decision(_decision(TENANT_A))

        found = await repo.get_decision(dec.id, TENANT_A)
        assert found is not None
        assert found.reasoning == "secret"

    @pytest.mark.asyncio
    async def test_get_decision_cross_tenant_blocked(self, db_session):
        """GA-P0-SEC-01 repro: tenant B must not read tenant A's decision by ID."""
        repo = PostgresDecisionCenterRepository(db_session)
        dec = await repo.save_decision(_decision(TENANT_A))

        assert await repo.get_decision(dec.id, TENANT_B) is None
        # Sanity: the row does exist, just not visible cross-tenant.
        assert await repo.get_decision(dec.id, TENANT_A) is not None

    @pytest.mark.asyncio
    async def test_get_decision_invalid_uuid_returns_none(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        assert await repo.get_decision("not-a-uuid", TENANT_A) is None

    @pytest.mark.asyncio
    async def test_get_decision_missing_returns_none(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        assert await repo.get_decision(str(uuid.uuid4()), TENANT_A) is None


class TestListDecisions:
    @pytest.mark.asyncio
    async def test_list_decisions_isolated_by_tenant(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        await repo.save_decision(_decision(TENANT_A, entity_id="a-co"))
        await repo.save_decision(_decision(TENANT_B, entity_id="b-co"))

        items_a, total_a = await repo.list_decisions(TENANT_A)
        items_b, total_b = await repo.list_decisions(TENANT_B)

        assert total_a == 1 and items_a[0].entity_id == "a-co"
        assert total_b == 1 and items_b[0].entity_id == "b-co"

    @pytest.mark.asyncio
    async def test_decision_without_tenant_metadata_not_visible_to_real_tenants(self, db_session):
        """A decision saved with no tenant_id in metadata must not leak into any
        real tenant's listing (defends the `.get("tenant_id", "")` fallback)."""
        repo = PostgresDecisionCenterRepository(db_session)
        orphan = Decision(
            id=str(uuid.uuid4()),
            domain=DecisionDomain.GENERAL,
            type=DecisionType.OTHER,
            entity_id="orphan-co",
            entity_type="company",
            decision="x",
            confidence=0.5,
            reasoning="r",
            provider="p",
            timestamp=datetime.now(timezone.utc),
            metadata=None,
        )
        await repo.save_decision(orphan)

        items_a, total_a = await repo.list_decisions(TENANT_A)
        assert total_a == 0
        assert await repo.get_decision(orphan.id, TENANT_A) is None


class TestAuditAndFeedbackIsolation:
    @pytest.mark.asyncio
    async def test_get_audit_cross_tenant_blocked(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        dec = await repo.save_decision(_decision(TENANT_A))
        await repo.save_audit(
            DecisionAudit(
                decision_id=dec.id,
                input_context={"secret": True},
                reasoning_steps=[],
                confidence_breakdown={},
                provider_used="rule_engine",
                alternatives_considered=[],
                timestamp=datetime.now(timezone.utc),
            )
        )

        assert await repo.get_audit(dec.id, TENANT_B) is None
        audit = await repo.get_audit(dec.id, TENANT_A)
        assert audit is not None
        assert audit.input_context == {"secret": True}

    @pytest.mark.asyncio
    async def test_feedback_cross_tenant_blocked(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        dec = await repo.save_decision(_decision(TENANT_A))
        await repo.save_feedback(
            DecisionFeedback(
                id=str(uuid.uuid4()),
                decision_id=dec.id,
                rating=FeedbackRating.UP,
                created_at=datetime.now(timezone.utc),
            )
        )

        assert await repo.get_feedback_for_decision(dec.id, TENANT_B) == []
        feedback = await repo.get_feedback_for_decision(dec.id, TENANT_A)
        assert len(feedback) == 1

    @pytest.mark.asyncio
    async def test_feedback_aggregate_isolated_by_tenant(self, db_session):
        repo = PostgresDecisionCenterRepository(db_session)
        dec_a = await repo.save_decision(_decision(TENANT_A))
        dec_b = await repo.save_decision(_decision(TENANT_B))
        await repo.save_feedback(
            DecisionFeedback(id=str(uuid.uuid4()), decision_id=dec_a.id, rating=FeedbackRating.UP)
        )
        await repo.save_feedback(
            DecisionFeedback(id=str(uuid.uuid4()), decision_id=dec_b.id, rating=FeedbackRating.DOWN)
        )

        agg_a = await repo.get_feedback_by_type(TENANT_A)
        agg_b = await repo.get_feedback_by_type(TENANT_B)

        assert len(agg_a) == 1 and agg_a[0].up_count == 1 and agg_a[0].down_count == 0
        assert len(agg_b) == 1 and agg_b[0].up_count == 0 and agg_b[0].down_count == 1
