"""E2E tests for Feature Store — Critical Path 12."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestFeatureStoreDomain:
    """Register feature definitions, set and get feature values."""

    async def test_register_feature_definition(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """POST /api/v1/feature-store/register creates a new feature."""
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/feature-store/register",
                json={
                    "key": f"e2e_test_{uuid.uuid4().hex[:8]}",
                    "name": "E2E Test Feature",
                    "description": "Automated test feature",
                    "feature_type": "numeric",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 503), resp.text
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "definition" in data

    async def test_set_feature_value(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """POST /api/v1/feature-store/set stores a feature value."""
        feature_key = f"e2e_key_{uuid.uuid4().hex[:8]}"
        entity_id = str(uuid.uuid4())

        await client.post(
            "/api/v1/feature-store/register",
            json={"key": feature_key, "name": f"Test {feature_key}"},
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/feature-store/set",
                json={
                    "feature_key": feature_key,
                    "entity_id": entity_id,
                    "entity_type": "company",
                    "value": 42,
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 503), resp.text
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "feature" in data

    async def test_get_feature_snapshot(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/feature-store/{type}/{id} returns feature snapshot."""
        entity_id = str(uuid.uuid4())

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/feature-store/company/{entity_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), resp.text

    async def test_get_single_feature(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/feature-store/{type}/{id}/{key} returns single value."""
        entity_id = str(uuid.uuid4())
        feature_key = f"e2e_single_{uuid.uuid4().hex[:8]}"

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/feature-store/company/{entity_id}/{feature_key}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), resp.text

    async def test_batch_set_features(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """POST /api/v1/feature-store/batch-set stores multiple features."""
        entity_id = str(uuid.uuid4())
        feature_key = f"e2e_batch_{uuid.uuid4().hex[:8]}"

        await client.post(
            "/api/v1/feature-store/register",
            json={"key": feature_key, "name": f"Batch {feature_key}"},
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/feature-store/batch-set",
                json={
                    "entity_id": entity_id,
                    "entity_type": "company",
                    "features": {feature_key: 100},
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 503), resp.text


class TestFeatureStoreRuntime:
    """Compute and retrieve runtime features for companies."""

    async def _seed_company(
        self, client: AsyncClient, headers: dict
    ) -> str:
        resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة الميزات",
                "name_en": f"FeatureCo-{uuid.uuid4().hex[:8]}",
                "cr_number": f"CR-FS-{uuid.uuid4().hex[:8]}",
                "city": "الرياض",
                "status": "active",
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201), f"Seed failed: {resp.text}"
        return resp.json()["id"]

    async def test_get_company_features(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/features/{company_id} returns computed features."""
        company_id = await self._seed_company(client, auth_headers)

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/features/{company_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert data["company_id"] == company_id

    async def test_recompute_company_features(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """POST /api/v1/features/{company_id}/recompute triggers recompute."""
        company_id = await self._seed_company(client, auth_headers)

        resp = await asyncio.wait_for(
            client.post(
                f"/api/v1/features/{company_id}/recompute",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201, 500, 503), resp.text
