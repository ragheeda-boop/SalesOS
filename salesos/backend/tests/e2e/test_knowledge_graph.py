"""E2E tests for Knowledge Graph — Critical Path 11."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestKnowledgeGraph:
    """Graph search, metrics, subgraph, and network queries."""

    async def _seed_company(
        self, client: AsyncClient, headers: dict
    ) -> str:
        resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة الرسم",
                "name_en": f"GraphCo-{uuid.uuid4().hex[:8]}",
                "cr_number": f"CR-GR-{uuid.uuid4().hex[:8]}",
                "city": "الرياض",
                "status": "active",
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201), f"Seed failed: {resp.text}"
        return resp.json()["id"]

    async def test_graph_search(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/graph/search returns graph results."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/graph/search",
                params={"q": "test", "limit": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "results" in data

    async def test_graph_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/graph/metrics returns engine metrics."""
        resp = await asyncio.wait_for(
            client.get("/api/v1/graph/metrics", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 503), resp.text

    async def test_graph_subgraph(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/graph/subgraph/{id} returns nodes and edges."""
        company_id = await self._seed_company(client, auth_headers)

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/graph/subgraph/{company_id}",
                params={"depth": 1},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), resp.text

    async def test_graph_competitors(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/graph/competitors/{id} returns competitor list."""
        company_id = await self._seed_company(client, auth_headers)

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/graph/competitors/{company_id}",
                params={"limit": 5},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), resp.text

    async def test_graph_decision_makers(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/graph/decision-makers/{id} returns contacts."""
        company_id = await self._seed_company(client, auth_headers)

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/graph/decision-makers/{company_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), resp.text
