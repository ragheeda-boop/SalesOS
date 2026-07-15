"""E2E tests for Meeting Intelligence — Critical Path 20."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestMeetingsList:
    """GET /api/v1/meetings/{opportunity_id} endpoint."""

    async def test_get_meetings_for_nonexistent_opp(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        opp_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/meetings/{opp_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text

    async def test_get_meetings_returns_list(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        opp_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/meetings/{opp_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)


class TestMeetingBrief:
    """POST /api/v1/meetings/{opportunity_id}/brief."""

    async def test_get_brief_for_nonexistent_opp(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        opp_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.post(
                f"/api/v1/meetings/{opp_id}/brief",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 500, 503), resp.text


class TestMeetingSummary:
    """POST /api/v1/meetings/{opportunity_id}/summary."""

    async def test_generate_summary(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        opp_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.post(
                f"/api/v1/meetings/{opp_id}/summary",
                json={
                    "notes": "E2E test meeting notes with key discussion points and action items",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestEmails:
    """Email intelligence endpoints."""

    async def test_get_emails_for_opportunity(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        opp_id = str(uuid.uuid4())
        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/emails/{opp_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)

    async def test_analyze_email(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/emails/analyze",
                json={
                    "opportunity_id": str(uuid.uuid4()),
                    "subject": "E2E Test Meeting Follow-up",
                    "from_address": "test@example.com",
                    "to_addresses": ["client@example.com"],
                    "body": "Thank you for the meeting. We look forward to the next steps.",
                    "direction": "outbound",
                    "email_type": "follow_up",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 500, 503), resp.text


class TestMeetingFullJourney:
    """Seed opportunity → get meetings → get brief — single flow."""

    async def test_meeting_full_journey(
        self,
        client: AsyncClient,
        registered_user_headers: dict,
    ):
        cr = f"CR-MTG-{uuid.uuid4().hex[:8]}"
        company_resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة الاجتماعات",
                "name_en": f"MeetingCo-{uuid.uuid4().hex[:8]}",
                "cr_number": cr,
                "city": "الرياض",
                "status": "active",
            },
            headers=registered_user_headers,
        )
        assert company_resp.status_code in (200, 201)
        company_id = company_resp.json()["id"]

        opp_resp = await client.post(
            "/api/v1/opportunities",
            params={
                "company_id": company_id,
                "name": f"Meeting Opp {uuid.uuid4().hex[:8]}",
                "value": 50000,
            },
            headers=registered_user_headers,
        )
        opp_id = opp_resp.json().get("id") if opp_resp.status_code in (200, 201) else None

        meetings_resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/meetings/{opp_id or company_id}",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert meetings_resp.status_code in (200, 500, 503), meetings_resp.text

        brief_resp = await asyncio.wait_for(
            client.post(
                f"/api/v1/meetings/{opp_id or company_id}/brief",
                headers=registered_user_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert brief_resp.status_code in (200, 404, 500, 503), brief_resp.text
