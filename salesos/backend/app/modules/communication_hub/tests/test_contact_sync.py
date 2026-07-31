"""Tests for contact_sync upsert (company-linked only)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.communication_hub.contact_sync import (
    _display_name_from_email,
    _normalize_email,
    upsert_contacts_from_addresses,
)


def test_normalize_skips_free_and_invalid():
    assert _normalize_email("Alice <alice@acme.com>") == "alice@acme.com"
    assert _normalize_email("bob@gmail.com") is None
    assert _normalize_email("not-an-email") is None
    assert _normalize_email("") is None


def test_display_name_from_email():
    assert _display_name_from_email("jane.doe@acme.com") == "Jane Doe"


@pytest.mark.asyncio
async def test_upsert_skips_when_no_company():
    db = AsyncMock()
    with patch(
        "app.modules.communication_hub.contact_sync.resolve_company_ids_for_addresses",
        new=AsyncMock(return_value=[]),
    ):
        result = await upsert_contacts_from_addresses(db, uuid4(), ["person@partner.example"])
    assert result["skipped"] == 1
    assert result["created"] == 0
    assert db.execute.await_count == 0


@pytest.mark.asyncio
async def test_upsert_creates_when_company_matched():
    db = AsyncMock()
    company_id = str(uuid4())
    empty = MagicMock()
    empty.mappings.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=empty)

    with patch(
        "app.modules.communication_hub.contact_sync.resolve_company_ids_for_addresses",
        new=AsyncMock(return_value=[company_id]),
    ):
        result = await upsert_contacts_from_addresses(db, uuid4(), ["alice@partner.example"])
    assert result["created"] == 1
    assert result["updated"] == 0
    assert db.execute.await_count == 2  # SELECT + INSERT


@pytest.mark.asyncio
async def test_upsert_updates_existing():
    db = AsyncMock()
    company_id = str(uuid4())
    existing = MagicMock()
    existing.mappings.return_value.first.return_value = {"id": str(uuid4())}
    db.execute = AsyncMock(return_value=existing)

    with patch(
        "app.modules.communication_hub.contact_sync.resolve_company_ids_for_addresses",
        new=AsyncMock(return_value=[company_id]),
    ):
        result = await upsert_contacts_from_addresses(db, uuid4(), ["alice@partner.example"])
    assert result["updated"] == 1
    assert result["created"] == 0
