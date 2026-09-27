"""update_opportunity_contact() re-fetches the row after the UPDATE statement
commits, then passes it straight to `_to_response()` with no None-check.
`_to_response()` accesses `.id`/`.tenant_id`/etc. unconditionally --
`_to_response(None)` raises `AttributeError: 'NoneType' object has no
attribute 'id'`. The row is checked to exist before the UPDATE, but a
concurrent delete between that check and the post-update re-fetch would
still surface as an unhandled 500 instead of a clean 404.

Live, mounted route (`PATCH /opportunity-contacts/{oc_id}`, confirmed
registered in app/boot/routers.py). Reproduced here with a mocked
repository whose `get()` returns a real row on the first call (the
pre-update existence check) and None on the second (the post-update
re-fetch), simulating exactly that race without needing real concurrency
or a database.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.routers.opportunity_contacts import (
    OpportunityContactUpdateBody,
    update_opportunity_contact,
)
from domains.commercial.opportunity.contracts.opportunity_contact_repository import (
    OpportunityContact,
)


def _make_existing(tenant_id: uuid.UUID) -> OpportunityContact:
    return OpportunityContact(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        opportunity_id="opp-1",
        contact_id=uuid.uuid4(),
        role="champion",
        is_primary=False,
    )


@pytest.mark.asyncio
async def test_update_raises_404_not_attributeerror_when_row_vanishes_after_update():
    tenant_id = uuid.uuid4()
    existing = _make_existing(tenant_id)

    repo = MagicMock()
    repo.get = AsyncMock(side_effect=[existing, None])
    repo.session = MagicMock()
    repo.session.begin = MagicMock()
    repo.session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    repo.session.begin.return_value.__aexit__ = AsyncMock(return_value=False)
    repo.session.execute = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await update_opportunity_contact(
            oc_id=existing.id,
            body=OpportunityContactUpdateBody(role="sponsor"),
            tenant_id=str(tenant_id),
            repo=repo,
            _rbac=None,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_returns_the_updated_row_on_the_normal_path():
    tenant_id = uuid.uuid4()
    existing = _make_existing(tenant_id)
    updated = _make_existing(tenant_id)
    updated.id = existing.id
    updated.role = "sponsor"

    repo = MagicMock()
    repo.get = AsyncMock(side_effect=[existing, updated])
    repo.session = MagicMock()
    repo.session.begin = MagicMock()
    repo.session.begin.return_value.__aenter__ = AsyncMock(return_value=None)
    repo.session.begin.return_value.__aexit__ = AsyncMock(return_value=False)
    repo.session.execute = AsyncMock()

    result = await update_opportunity_contact(
        oc_id=existing.id,
        body=OpportunityContactUpdateBody(role="sponsor"),
        tenant_id=str(tenant_id),
        repo=repo,
        _rbac=None,
    )

    assert result.role == "sponsor"
