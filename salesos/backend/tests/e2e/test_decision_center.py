"""E2E tests for Decision Center — Critical Path 16."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestDecisionEvaluate:
    """POST /api/v1/decision/evaluate and batch evaluation."""

    async def test_evaluate_decision(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/decision/evaluate",
                json={
                    "tenant_id": auth_headers["X-Tenant-Id"],
                    "actor_id": "e2e-tester",
                    "entity_id": str(uuid.uuid4()),
                    "entity_type": "opportunity",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 422, 503), resp.text

    async def test_batch_evaluate(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/decision/batch",
                json=[
                    {
                        "tenant_id": auth_headers["X-Tenant-Id"],
                        "actor_id": "e2e-tester",
                        "entity_id": str(uuid.uuid4()),
                        "entity_type": "opportunity",
                    }
                ],
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 422, 503), resp.text


class TestDecisionRecommendations:
    """GET /api/v1/decision/recommendations and scores."""

    async def test_get_recommendations(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/recommendations",
                params={"entity_type": "opportunity", "status": "pending", "limit": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "items" in data

    async def test_get_scores(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        entity_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/scores",
                params={"entity_id": entity_id, "entity_type": "opportunity"},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text


class TestDecisionHistory:
    """GET /api/v1/decision/history returns decision log."""

    async def test_decision_history(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/history",
                params={"limit": 10, "offset": 0},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "items" in data

    async def test_decision_history_with_filters(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/history",
                params={"entity_type": "opportunity", "limit": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text


class TestDecisionRules:
    """CRUD for decision rules."""

    async def test_list_rules(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/rules",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text

    async def test_create_rule(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/decision/rules",
                json={
                    "name": f"E2E Rule {uuid.uuid4().hex[:8]}",
                    "description": "Test rule from e2e",
                    "priority": 5,
                    "category": "lead_scoring",
                    "version": "1.0",
                    "conditions": {"min_value": 10000},
                    "action": "escalate",
                    "weight": 1.0,
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (201, 409, 503), resp.text


class TestDecisionLearning:
    """Learning quality and trends endpoints."""

    async def test_learning_quality(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/learning/quality",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text

    async def test_learning_trends(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/learning/trends",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text


class TestDecisionFeedback:
    """POST /api/v1/decision/feedback and stats."""

    async def test_submit_feedback(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/decision/feedback",
                json={
                    "decision_id": f"e2e-{uuid.uuid4().hex[:8]}",
                    "tenant_id": auth_headers["X-Tenant-Id"],
                    "actor_id": "e2e-tester",
                    "outcome": "accepted",
                    "reason": "E2E test feedback",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 400, 503), resp.text

    async def test_feedback_stats(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/feedback/stats",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "total" in data


class TestDecisionEvidence:
    """GET /api/v1/decision/evidence endpoint."""

    async def test_get_evidence(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        entity_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/decision/evidence",
                params={
                    "entity_id": entity_id,
                    "entity_type": "opportunity",
                    "limit": 5,
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text


class TestDecisionExplain:
    """GET /api/v1/decision/{id}/explain endpoint."""

    async def test_explain_nonexistent_decision(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/decision/{uuid.uuid4()}/explain",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (404, 503), resp.text
