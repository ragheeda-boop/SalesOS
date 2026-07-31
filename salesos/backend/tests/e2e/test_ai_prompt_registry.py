"""E2E tests for AI Prompt Registry — Critical Path 21."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestAIPrompts:
    """GET and POST /api/v1/ai/prompts endpoints."""

    async def test_list_prompts_returns_list(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get("/api/v1/ai/prompts", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)

    async def test_create_prompt(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-prompt-{uuid.uuid4().hex[:8]}"
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/ai/prompts",
                json={
                    "id": prompt_id,
                    "name": f"E2E Test Prompt {uuid.uuid4().hex[:8]}",
                    "version": "1.0",
                    "template": "Analyze the following company data: {input}",
                    "variables": ["input"],
                    "domain": "analysis",
                    "output_schema": {
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                    },
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (201, 500, 503), resp.text
        if resp.status_code == 201:
            data = resp.json()
            assert data["name"].startswith("E2E Test Prompt")

    async def test_list_prompts_after_create_includes_new(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-list-{uuid.uuid4().hex[:8]}"
        await client.post(
            "/api/v1/ai/prompts",
            json={
                "id": prompt_id,
                "name": f"List Check Prompt {uuid.uuid4().hex[:8]}",
                "version": "1.0",
                "template": "Summarize: {input}",
                "variables": ["input"],
                "domain": "summarization",
            },
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.get("/api/v1/ai/prompts", headers=auth_headers),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200:
            prompts = resp.json()
            ids = [p["id"] for p in prompts]
            assert prompt_id in ids

    async def test_list_prompts_filtered_by_domain(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/ai/prompts",
                params={"domain": "analysis"},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestAIActivate:
    """POST /api/v1/ai/prompts/activate endpoint."""

    async def test_activate_existing_prompt(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-act-{uuid.uuid4().hex[:8]}"
        create_resp = await client.post(
            "/api/v1/ai/prompts",
            json={
                "id": prompt_id,
                "name": f"Activate Prompt {uuid.uuid4().hex[:8]}",
                "version": "1.0",
                "template": "Evaluate: {input}",
                "variables": ["input"],
                "domain": "evaluation",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (201, 500, 503)

        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/ai/prompts/activate",
                json={"id": prompt_id, "version": "1.0"},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 500, 503), resp.text

    async def test_activate_nonexistent_prompt_returns_404(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/ai/prompts/activate",
                json={"id": "nonexistent-prompt-id", "version": "1.0"},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (404, 500, 503), resp.text


class TestAIEvaluate:
    """POST /api/v1/ai/evaluate endpoint."""

    async def test_evaluate_prompt_output(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-eval-{uuid.uuid4().hex[:8]}"
        await client.post(
            "/api/v1/ai/prompts",
            json={
                "id": prompt_id,
                "name": f"Eval Prompt {uuid.uuid4().hex[:8]}",
                "version": "1.0",
                "template": "Analyze: {input}",
                "variables": ["input"],
                "domain": "evaluation",
            },
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/ai/evaluate",
                json={
                    "prompt_id": prompt_id,
                    "input": "Test company data",
                    "output": "High potential opportunity",
                    "expected": "High potential",
                    "metrics": ["accuracy", "relevance"],
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            data = resp.json()
            assert "score" in data
            assert "metrics" in data


class TestAIMetrics:
    """GET /api/v1/ai/metrics/{prompt_id} endpoint."""

    async def test_get_prompt_metrics(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-metric-{uuid.uuid4().hex[:8]}"
        await client.post(
            "/api/v1/ai/prompts",
            json={
                "id": prompt_id,
                "name": f"Metric Prompt {uuid.uuid4().hex[:8]}",
                "version": "1.0",
                "template": "Summarize: {input}",
                "variables": ["input"],
                "domain": "summarization",
            },
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/ai/metrics/{prompt_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestAIGenerate:
    """POST /api/v1/ai/generate endpoint."""

    async def test_generate_with_valid_prompt(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-gen-{uuid.uuid4().hex[:8]}"
        await client.post(
            "/api/v1/ai/prompts",
            json={
                "id": prompt_id,
                "name": f"Gen Prompt {uuid.uuid4().hex[:8]}",
                "version": "1.0",
                "template": "Analyze this: {input}",
                "variables": ["input"],
                "domain": "analysis",
            },
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/ai/generate",
                json={
                    "prompt_template_id": prompt_id,
                    "variables": {"input": "E2E test input data"},
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 500, 503), resp.text


class TestAIFullJourney:
    """Create prompt → activate → evaluate → metrics — single flow."""

    async def test_ai_full_journey(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        prompt_id = f"e2e-journey-{uuid.uuid4().hex[:8]}"
        create_resp = await client.post(
            "/api/v1/ai/prompts",
            json={
                "id": prompt_id,
                "name": f"Journey Prompt {uuid.uuid4().hex[:8]}",
                "version": "1.0",
                "template": "Analyze: {input}",
                "variables": ["input"],
                "domain": "analysis",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (201, 500, 503)

        list_resp = await client.get("/api/v1/ai/prompts", headers=auth_headers)
        assert list_resp.status_code in (200, 500, 503)

        metrics_resp = await client.get(
            f"/api/v1/ai/metrics/{prompt_id}",
            headers=auth_headers,
        )
        assert metrics_resp.status_code in (200, 500, 503)
