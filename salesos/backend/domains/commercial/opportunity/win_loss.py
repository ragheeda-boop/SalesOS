"""Reviewed win/loss taxonomy and deterministic aggregation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

LOSS_REASONS: dict[str, tuple[str, ...]] = {
    "competitor": ("competitor", "منافس", "alternative"),
    "price": ("price", "budget", "سعر", "ميزانية"),
    "timing": ("timing", "延期", "توقيت", "later"),
    "no_decision": ("no decision", "no-decision", "لم يقرر", "عدم قرار"),
    "fit": ("fit", "feature", "ملاءمة", "ميزة"),
}


@dataclass(frozen=True)
class WinLossSummary:
    won: int
    lost: int
    unclassified_losses: int
    loss_reasons: dict[str, int]


def normalize_loss_reason(reason: str | None) -> str:
    text = " ".join((reason or "").lower().split())
    for category, keywords in LOSS_REASONS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "unclassified"


def summarize_win_loss(records: Iterable[dict[str, object]]) -> WinLossSummary:
    won = lost = 0
    categories: Counter[str] = Counter()
    for record in records:
        status = str(record.get("status") or record.get("outcome") or "").lower()
        if status in {"won", "closed_won"}:
            won += 1
        elif status in {"lost", "closed_lost"}:
            lost += 1
            categories[normalize_loss_reason(str(record.get("loss_reason") or ""))] += 1
    return WinLossSummary(
        won=won,
        lost=lost,
        unclassified_losses=categories.get("unclassified", 0),
        loss_reasons=dict(sorted(categories.items())),
    )
