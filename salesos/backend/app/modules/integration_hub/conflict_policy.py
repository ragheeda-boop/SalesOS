"""STORY-08-06 — ConflictResolutionPolicy pure rules (OBJ-333).

Write-back feedback-loop exclusion: SalesOS-authored fields must never be
pulled back as fresh source data. Enforced here (and via FieldMapping filter),
not developer memory. Not Production GO.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from app.modules.integration_hub.field_mapping import FieldMapEntry

Winner = Literal["source", "salesos"]

_DEFAULT_SALESOS = frozenset({"risk_score", "ai_sentiment", "ai_score"})
_DEFAULT_OPERATIONAL = frozenset(
    {"name", "email", "phone", "cr_number", "stage", "amount", "currency"}
)


@dataclass(frozen=True)
class FieldConflictRule:
    internal: str
    winner: Winner
    exclude_from_pull: bool = False


@dataclass(frozen=True)
class ConflictResolutionPolicy:
    """Per-connection policy used by ACL ConflictResolver + pull filtering."""

    rules: tuple[FieldConflictRule, ...]
    salesos_authored_fields: frozenset[str]
    operational_fields: frozenset[str]

    @classmethod
    def default(cls) -> ConflictResolutionPolicy:
        authored = _DEFAULT_SALESOS
        rules = tuple(
            FieldConflictRule(internal=f, winner="salesos", exclude_from_pull=True)
            for f in sorted(authored)
        ) + tuple(
            FieldConflictRule(internal=f, winner="source", exclude_from_pull=False)
            for f in sorted(_DEFAULT_OPERATIONAL)
        )
        return cls(
            rules=rules,
            salesos_authored_fields=authored,
            operational_fields=_DEFAULT_OPERATIONAL,
        )


class FeedbackLoopExclusionError(ValueError):
    """Raised when a SalesOS-authored field would be pulled as fresh source data."""


def parse_conflict_rules(raw: Any) -> tuple[FieldConflictRule, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("rules must be a list")
    out: list[FieldConflictRule] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("each rule must be an object")
        internal = str(item.get("internal") or "").strip()
        winner = str(item.get("winner") or "").strip().lower()
        if not internal:
            raise ValueError("rule.internal required")
        if winner not in {"source", "salesos"}:
            raise ValueError(f"rule.winner must be source|salesos, got {winner!r}")
        exclude = bool(item.get("exclude_from_pull", winner == "salesos"))
        out.append(
            FieldConflictRule(
                internal=internal,
                winner=winner,  # type: ignore[arg-type]
                exclude_from_pull=exclude,
            )
        )
    return tuple(out)


def policy_from_row(
    *,
    rules: Any,
    salesos_authored_fields: Any,
    operational_fields: Any,
) -> ConflictResolutionPolicy:
    authored = (
        frozenset(str(x).strip() for x in (salesos_authored_fields or []) if str(x).strip())
        or _DEFAULT_SALESOS
    )
    operational = (
        frozenset(str(x).strip() for x in (operational_fields or []) if str(x).strip())
        or _DEFAULT_OPERATIONAL
    )
    parsed = parse_conflict_rules(rules)
    # Ensure every salesos-authored field has exclude_from_pull=True.
    by_field = {r.internal: r for r in parsed}
    for f in authored:
        existing = by_field.get(f)
        if existing is None or (not existing.exclude_from_pull or existing.winner != "salesos"):
            by_field[f] = FieldConflictRule(internal=f, winner="salesos", exclude_from_pull=True)
    return ConflictResolutionPolicy(
        rules=tuple(by_field.values()),
        salesos_authored_fields=authored,
        operational_fields=operational,
    )


def pull_excluded_fields(policy: ConflictResolutionPolicy) -> frozenset[str]:
    """Fields permanently excluded from reverse/pull mapping."""
    excluded = set(policy.salesos_authored_fields)
    for rule in policy.rules:
        if rule.exclude_from_pull:
            excluded.add(rule.internal)
    return frozenset(excluded)


def filter_mappings_for_pull(
    entries: Sequence[FieldMapEntry],
    policy: ConflictResolutionPolicy,
) -> tuple[FieldMapEntry, ...]:
    """Strip pull/bidirectional maps for feedback-excluded (SalesOS-authored) fields."""
    banned = pull_excluded_fields(policy)
    out: list[FieldMapEntry] = []
    for e in entries:
        if e.internal in banned and e.direction in {"pull", "bidirectional"}:
            # Keep push-only if bidirectional was requested — force push.
            if e.direction == "bidirectional":
                out.append(
                    FieldMapEntry(internal=e.internal, external=e.external, direction="push")
                )
            continue
        out.append(e)
    return tuple(out)


def assert_no_feedback_loop_pull(
    entries: Iterable[FieldMapEntry],
    policy: ConflictResolutionPolicy,
) -> None:
    """Dedicated AC check: SalesOS-authored fields must not pull as fresh source."""
    banned = pull_excluded_fields(policy)
    offenders = sorted(
        {
            e.internal
            for e in entries
            if e.internal in banned and e.direction in {"pull", "bidirectional"}
        }
    )
    if offenders:
        raise FeedbackLoopExclusionError(
            "write-back feedback-loop exclusion violated: "
            f"SalesOS-authored fields must not pull as fresh source data: {offenders}"
        )
