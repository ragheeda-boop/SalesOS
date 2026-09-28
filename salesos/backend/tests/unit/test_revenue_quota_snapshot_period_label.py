"""QuotaService.take_snapshot()'s auto-generated period_label used
strftime("%Y-Q%q") -- Python's strftime has no "%q" (quarter) directive.

Confirmed directly on both platforms:
  - Linux (this app's deployment platform): silently emits the literal
    characters "%q" unsubstituted, e.g. "2026-Q%q" instead of "2026-Q1".
  - Windows: raises ValueError: Invalid format string instead.

Either way, POST /api/v1/revenue-planning/quotas/snapshot (router.py's
take_quota_snapshot, whose period_label query param defaults to "") would
either persist a nonsensical label or crash outright, for every real call
that doesn't explicitly supply one. The only existing test
(test_quota_snapshots_rls.py) always supplies an explicit period_label,
so it never exercised this fallback path.

Fixed by computing the quarter number directly instead of relying on a
non-existent format directive.
"""

from __future__ import annotations

import re

import pytest

from domains.revenue.quota.in_memory_repo import InMemoryQuotaRepository
from domains.revenue.quota.service import QuotaService

_VALID_LABEL = re.compile(r"^\d{4}-Q[1-4]$")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "month, expected_quarter",
    [(1, 1), (3, 1), (4, 2), (6, 2), (7, 3), (9, 3), (10, 4), (12, 4)],
)
async def test_take_snapshot_computes_correct_quarter_for_every_month(
    month, expected_quarter, monkeypatch
) -> None:
    """Every month of the year must map to its correct calendar quarter,
    never to the literal, unsubstituted "%q" directive."""
    import datetime as dt_module

    class _FixedDatetime(dt_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, month, 15, 12, 0, 0, tzinfo=tz)

    monkeypatch.setattr(
        "domains.revenue.quota.service.datetime", _FixedDatetime
    )

    service = QuotaService(InMemoryQuotaRepository())
    snapshot = await service.take_snapshot(tenant_id="t-1", period_label="")

    assert snapshot.period_label == f"2026-Q{expected_quarter}"
    assert "%q" not in snapshot.period_label, (
        f"literal, unsubstituted strftime directive leaked into the label: "
        f"{snapshot.period_label!r}"
    )
    assert _VALID_LABEL.match(snapshot.period_label)


@pytest.mark.asyncio
async def test_take_snapshot_respects_an_explicit_period_label() -> None:
    service = QuotaService(InMemoryQuotaRepository())
    snapshot = await service.take_snapshot(tenant_id="t-1", period_label="2026-Q3")
    assert snapshot.period_label == "2026-Q3"
