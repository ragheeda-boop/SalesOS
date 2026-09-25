"""Source-aware market sizing contract for TAM/SAM/SOM outputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class MarketEstimate:
    metric: str
    amount: Decimal
    currency: str
    source: str
    as_of: date
    methodology: str

    def __post_init__(self) -> None:
        if self.metric not in {"TAM", "SAM", "SOM"}:
            raise ValueError("metric must be TAM, SAM, or SOM")
        if self.amount < 0:
            raise ValueError("market amount cannot be negative")
        if not self.source.strip() or not self.methodology.strip():
            raise ValueError("market estimates require source and methodology")


def validate_market_stack(estimates: list[MarketEstimate]) -> dict[str, object]:
    by_metric = {item.metric: item for item in estimates}
    missing = [metric for metric in ("TAM", "SAM", "SOM") if metric not in by_metric]
    ordered = [by_metric[item] for item in ("TAM", "SAM", "SOM") if item in by_metric]
    monotonic = len(ordered) < 2 or all(left.amount >= right.amount for left, right in zip(ordered, ordered[1:]))
    return {
        "valid": not missing and monotonic,
        "missing": missing,
        "monotonic": monotonic,
        "currency": ordered[0].currency if ordered else None,
        "as_of": max(item.as_of for item in ordered).isoformat() if ordered else None,
    }
