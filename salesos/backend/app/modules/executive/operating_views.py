"""Deterministic Manager OS and Revenue Leadership rollups."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable


def manager_seller_view(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, Decimal | int]] = defaultdict(
        lambda: {"opportunities": 0, "open_value": Decimal("0"), "won_value": Decimal("0")}
    )
    for record in records:
        owner = str(record.get("owner_id") or "unassigned")
        bucket = grouped[owner]
        bucket["opportunities"] = int(bucket["opportunities"]) + 1
        value = Decimal(str(record.get("value") or 0))
        if str(record.get("status") or "").lower() == "won":
            bucket["won_value"] = bucket["won_value"] + value
        else:
            bucket["open_value"] = bucket["open_value"] + value
    return [
        {"owner_id": owner, **{key: str(value) if isinstance(value, Decimal) else value for key, value in data.items()}}
        for owner, data in sorted(grouped.items())
    ]


def leadership_revenue_snapshot(records: Iterable[dict[str, object]]) -> dict[str, object]:
    by_segment: dict[str, Decimal] = defaultdict(Decimal)
    by_currency: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        if str(record.get("status") or "").lower() != "won":
            continue
        segment = str(record.get("segment") or "unknown")
        currency = str(record.get("currency") or "UNKNOWN").upper()
        by_segment[segment] += Decimal(str(record.get("value") or 0))
        by_currency[currency] += Decimal(str(record.get("value") or 0))
    return {
        "by_segment": {key: str(value) for key, value in sorted(by_segment.items())},
        "by_currency": {key: str(value) for key, value in sorted(by_currency.items())},
        "mixed_currency": len(by_currency) > 1,
    }
