"""STORY-08-03 — FieldMappingConfig shapes + drift detection (pure).

fields_get()-equivalent: compare mapped external fields to a remote schema
snapshot. Vendor-neutral (no Odoo symbols). Not Production GO.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

Direction = Literal["pull", "push", "bidirectional"]


@dataclass(frozen=True)
class FieldMapEntry:
    internal: str
    external: str
    direction: Direction = "pull"


@dataclass(frozen=True)
class DriftAlert:
    """Loud, actionable drift signal for ops / Integrations Studio."""

    severity: Literal["critical", "warning", "info"]
    kind: str
    message: str
    external_field: str | None = None
    internal_field: str | None = None
    candidate_external: str | None = None


def parse_field_mappings(raw: Any) -> tuple[FieldMapEntry, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("mappings must be a list")
    out: list[FieldMapEntry] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("mapping entry must be an object")
        internal = str(item.get("internal") or "").strip()
        external = str(item.get("external") or "").strip()
        direction = str(item.get("direction") or "pull").strip().lower()
        if not internal or not external:
            raise ValueError("mapping requires internal and external")
        if direction not in {"pull", "push", "bidirectional"}:
            raise ValueError("direction must be pull|push|bidirectional")
        out.append(
            FieldMapEntry(internal=internal, external=external, direction=direction)  # type: ignore[arg-type]
        )
    return tuple(out)


def mappings_to_json(
    entries: tuple[FieldMapEntry, ...] | list[FieldMapEntry],
) -> list[dict[str, str]]:
    return [
        {"internal": e.internal, "external": e.external, "direction": e.direction} for e in entries
    ]


def normalize_remote_schema(remote: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Accept fields_get()-like {name: meta} or {fields: {name: meta}}."""
    if remote is None:
        return {}
    if not isinstance(remote, Mapping):
        raise ValueError("remote schema must be an object")
    payload = remote.get("fields") if "fields" in remote else remote
    if not isinstance(payload, Mapping):
        raise ValueError("remote schema fields must be an object")
    out: dict[str, dict[str, Any]] = {}
    for name, meta in payload.items():
        key = str(name).strip()
        if not key:
            continue
        if isinstance(meta, Mapping):
            out[key] = dict(meta)
        else:
            out[key] = {"type": str(meta)}
    return out


def detect_field_drift(
    *,
    mappings: tuple[FieldMapEntry, ...] | list[FieldMapEntry],
    remote_schema: Mapping[str, Any] | None,
    baseline_fields: set[str] | frozenset[str] | None = None,
) -> list[DriftAlert]:
    """Diff mapped/baseline fields against a remote schema snapshot.

    Simulated rename: mapped external missing + exactly one new field vs baseline
    → critical ``possible_rename`` alert (loud).
    """
    remote = normalize_remote_schema(remote_schema)
    remote_names = set(remote.keys())
    mapped_externals = {m.external for m in mappings}
    baseline = set(baseline_fields) if baseline_fields is not None else set(mapped_externals)

    alerts: list[DriftAlert] = []
    missing_mapped = sorted(mapped_externals - remote_names)
    new_vs_baseline = sorted(remote_names - baseline)

    for ext in missing_mapped:
        internal = next((m.internal for m in mappings if m.external == ext), None)
        # Rename heuristic: one missing mapped field and one new remote field.
        if len(missing_mapped) == 1 and len(new_vs_baseline) == 1:
            candidate = new_vs_baseline[0]
            alerts.append(
                DriftAlert(
                    severity="critical",
                    kind="possible_rename",
                    message=(
                        f"DRIFT ALERT: mapped external field {ext!r} "
                        f"(internal {internal!r}) is MISSING from remote schema; "
                        f"possible RENAME to {candidate!r}. "
                        "Sync paused until mapping is updated."
                    ),
                    external_field=ext,
                    internal_field=internal,
                    candidate_external=candidate,
                )
            )
        else:
            alerts.append(
                DriftAlert(
                    severity="critical",
                    kind="missing_mapped_field",
                    message=(
                        f"DRIFT ALERT: mapped external field {ext!r} "
                        f"(internal {internal!r}) is MISSING from remote schema. "
                        "Fix FieldMappingConfig before sync continues."
                    ),
                    external_field=ext,
                    internal_field=internal,
                )
            )

    for ext in new_vs_baseline:
        if any(a.candidate_external == ext for a in alerts):
            continue
        alerts.append(
            DriftAlert(
                severity="warning",
                kind="new_unmapped_field",
                message=(
                    f"DRIFT NOTICE: remote field {ext!r} appeared and is not in "
                    "baseline/mapping — review FieldMappingConfig."
                ),
                external_field=ext,
            )
        )

    return alerts
