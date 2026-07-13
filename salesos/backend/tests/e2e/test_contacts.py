"""E2E tests for Contact CRUD — Critical Path 8."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e
_TEST_TIMEOUT = 30


class TestContactCRUD:
    """Create, read, update, delete contacts."""

    async def _seed_company(
        self, client: AsyncClient, headers: dict
    ) -> str:
        """Create a company and return its ID."""
        resp = await client.post(
            "/api/v1/companies",
            json={
                "name_ar": "شركة التجارب",
                "name_en": f"ContactTestCo-{uuid.uuid4().hex[:8]}",
                "cr_number": f"CR-CT-{uuid.uuid4().hex[:8]}",
                "city": "الرياض",
                "status": "active",
            },
            headers=headers,
        )
        assert resp.status_code in (200, 201), f"Seed company failed: {resp.text}"
        return resp.json()["id"]

    async def test_create_contact(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """POST /api/v1/contacts creates a new contact."""
        company_id = await self._seed_company(client, auth_headers)
        email = f"contact-{uuid.uuid4().hex[:8]}@test.com"

        resp = await asyncio.wait_for(
            client.post(
                "/api/v1/contacts",
                json={
                    "name": "E2E Test Contact",
                    "name_ar": "جهة اتصال",
                    "email": email,
                    "phone": "+966500000000",
                    "mobile": "+966555000000",
                    "position": "CEO",
                    "position_ar": "رئيس تنفيذي",
                    "department": "Executive",
                    "company_id": company_id,
                    "is_primary": True,
                    "tags": ["e2e", "test"],
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["name"] == "E2E Test Contact"
        assert data["email"] == email
        assert data["is_primary"] is True
        assert "id" in data
        assert data["company_id"] == company_id

    async def test_list_contacts_paginated(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/contacts returns paginated contact list."""
        resp = await asyncio.wait_for(
            client.get(
                "/api/v1/contacts",
                params={"page": 1, "page_size": 10},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_get_contacts_by_company(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/contacts/by-company/{id} returns company contacts."""
        company_id = await self._seed_company(client, auth_headers)
        await client.post(
            "/api/v1/contacts",
            json={
                "name": "Company Contact",
                "company_id": company_id,
            },
            headers=auth_headers,
        )

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/contacts/by-company/{company_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_contact_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """GET /api/v1/contacts/{id} returns single contact."""
        company_id = await self._seed_company(client, auth_headers)
        create = await client.post(
            "/api/v1/contacts",
            json={
                "name": "Get Me",
                "email": f"getme-{uuid.uuid4().hex[:8]}@test.com",
                "company_id": company_id,
            },
            headers=auth_headers,
        )
        contact_id = create.json()["id"]

        resp = await asyncio.wait_for(
            client.get(
                f"/api/v1/contacts/{contact_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == contact_id

    async def test_update_contact(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """PATCH /api/v1/contacts/{id} updates a contact."""
        company_id = await self._seed_company(client, auth_headers)
        create = await client.post(
            "/api/v1/contacts",
            json={
                "name": "Before Update",
                "company_id": company_id,
            },
            headers=auth_headers,
        )
        contact_id = create.json()["id"]

        resp = await asyncio.wait_for(
            client.patch(
                f"/api/v1/contacts/{contact_id}",
                json={"name": "After Update", "department": "Engineering"},
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["name"] == "After Update"
        assert data["department"] == "Engineering"

    async def test_delete_contact(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """DELETE /api/v1/contacts/{id} removes a contact."""
        company_id = await self._seed_company(client, auth_headers)
        create = await client.post(
            "/api/v1/contacts",
            json={
                "name": "Delete Me",
                "company_id": company_id,
            },
            headers=auth_headers,
        )
        contact_id = create.json()["id"]

        resp = await asyncio.wait_for(
            client.delete(
                f"/api/v1/contacts/{contact_id}",
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert resp.status_code in (200, 204), resp.text

    async def test_full_contact_journey(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Create → List → Get → Update → Delete — single flow."""
        company_id = await self._seed_company(client, auth_headers)
        email = f"journey-{uuid.uuid4().hex[:8]}@test.com"

        # Step 1 — Create
        create = await asyncio.wait_for(
            client.post(
                "/api/v1/contacts",
                json={
                    "name": "Journey Contact",
                    "email": email,
                    "company_id": company_id,
                    "department": "Sales",
                },
                headers=auth_headers,
            ),
            timeout=_TEST_TIMEOUT,
        )
        assert create.status_code in (200, 201)
        contact_id = create.json()["id"]

        # Step 2 — List and find
        list_resp = await client.get(
            "/api/v1/contacts",
            params={"email": email},
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Step 3 — Get by ID
        get_resp = await client.get(
            f"/api/v1/contacts/{contact_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["email"] == email

        # Step 4 — Update
        patch = await client.patch(
            f"/api/v1/contacts/{contact_id}",
            json={"position": "VP Sales"},
            headers=auth_headers,
        )
        assert patch.status_code == 200
        assert patch.json()["position"] == "VP Sales"

        # Step 5 — Delete
        delete = await client.delete(
            f"/api/v1/contacts/{contact_id}",
            headers=auth_headers,
        )
        assert delete.status_code in (200, 204)
