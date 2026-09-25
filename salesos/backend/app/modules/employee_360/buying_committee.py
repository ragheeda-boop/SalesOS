"""Deterministic buying-committee view over tenant-scoped people records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

ROLE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("economic_buyer", ("ceo", "cfo", "chief executive", "chief financial", "owner", "مالك")),
    ("champion", ("vp", "director", "head", "مدير", "رئيس")),
    ("technical_buyer", ("cto", "cio", "engineering", "it", "technology", "تقنية")),
    ("procurement", ("procurement", "purchasing", "sourcing", "مشتريات")),
    ("user", ("manager", "specialist", "analyst", "مشرف", "أخصائي")),
)

_ROLE_ORDER = {role: index for index, (role, _keywords) in enumerate(ROLE_KEYWORDS)}


@dataclass(frozen=True)
class CommitteeMember:
    person_id: str
    name: str
    title: str
    role: str
    confidence: float
    evidence: str


def classify_committee_role(title: str | None) -> tuple[str, float]:
    normalized = " ".join((title or "").lower().replace("-", " ").split())
    for role, keywords in ROLE_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return role, 0.85
    return "unknown", 0.35


def build_buying_committee(people: Iterable[dict[str, Any]]) -> list[CommitteeMember]:
    """Return stable role assignments; no title inference changes source data."""
    members: list[CommitteeMember] = []
    for person in people:
        person_id = str(person.get("id") or "").strip()
        name = str(person.get("name") or "").strip()
        title = str(person.get("title") or person.get("position") or "").strip()
        if not person_id or not name:
            continue
        role, confidence = classify_committee_role(title)
        members.append(
            CommitteeMember(
                person_id=person_id,
                name=name,
                title=title,
                role=role,
                confidence=confidence,
                evidence="title_keyword" if role != "unknown" else "title_missing_or_unclassified",
            )
        )
    return sorted(members, key=lambda item: (_ROLE_ORDER.get(item.role, 99), item.name.casefold()))
