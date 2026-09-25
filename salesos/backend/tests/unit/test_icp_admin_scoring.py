"""Pure API-handler checks for persistent-profile ICP scoring."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.gtm.icp import ICPProfile, normalize_criteria, normalize_weights
from app.modules.gtm.icp_admin_router import ICPScoreIn, score_icp_profile


@pytest.mark.asyncio
async def test_score_uses_the_tenant_profile_and_reports_matches(monkeypatch):
    profile = ICPProfile(
        id="profile-1",
        tenant_id="tenant-1",
        name="Saudi technology buyers",
        criteria=normalize_criteria(industries=["technology"], cities=["riyadh"]),
        weights=normalize_weights(industry=2, city=1),
    )
    repo = AsyncMock()
    repo.get.return_value = profile
    monkeypatch.setattr("app.modules.gtm.icp_admin_router._REPO", repo)

    result = await score_icp_profile(
        "profile-1",
        ICPScoreIn(industry="Technology", city="Riyadh", name="Acme"),
        tenant_id="tenant-1",
    )

    repo.get.assert_awaited_once_with("profile-1", tenant_id="tenant-1")
    assert result["fit_ratio"] == 1.0
    assert result["matched"]["industry"] is True
    assert result["matched"]["city"] is True
    assert result["schema_version"] == profile.schema_version


@pytest.mark.asyncio
async def test_score_returns_not_found_for_profile_outside_tenant(monkeypatch):
    repo = AsyncMock()
    repo.get.return_value = None
    monkeypatch.setattr("app.modules.gtm.icp_admin_router._REPO", repo)

    with pytest.raises(HTTPException) as error:
        await score_icp_profile(
            "foreign-profile",
            ICPScoreIn(industry="technology"),
            tenant_id="tenant-2",
        )

    assert error.value.status_code == 404
    repo.get.assert_awaited_once_with("foreign-profile", tenant_id="tenant-2")
