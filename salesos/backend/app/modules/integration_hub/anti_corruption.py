"""STORY-08-04 — Anti-Corruption Layer (`OdooTranslator` pattern).

Six internal responsibilities in one class (ARB §9), not six public classes:
Mapper → Validator → Transformer → Normalizer → ConflictResolver → Versioning.

Malformed input fails loudly at Validator (never silent null).
No DB / RLS / DEC-085. Not Production GO.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import unescape
from typing import Any, cast

from app.modules.integration_hub.field_mapping import FieldMapEntry, parse_field_mappings

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CR_RE = re.compile(r"^\d{10}$")
# Operational fields: external/source wins on conflict.
_DEFAULT_OPERATIONAL = frozenset(
    {"name", "email", "phone", "cr_number", "stage", "amount", "currency"}
)


class AclValidationError(ValueError):
    """Raised when Validator rejects a record — clear, non-silent failure."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


@dataclass(frozen=True)
class CanonicalRecord:
    """Output of the ACL pipeline (canonical side of the boundary)."""

    payload: dict[str, Any]
    source_updated_at: datetime | None
    sync_run_id: str
    meta: dict[str, Any] = field(default_factory=dict)


class OdooTranslator:
    """Single ACL class — six internal stages, one public ``translate`` entry."""

    def __init__(
        self,
        *,
        stage_map: Mapping[str, str] | None = None,
        operational_fields: frozenset[str] | None = None,
        salesos_authored_fields: frozenset[str] | None = None,
    ) -> None:
        self._stage_map = dict(stage_map or {})
        self._operational = operational_fields or _DEFAULT_OPERATIONAL
        self._salesos_authored = salesos_authored_fields or frozenset(
            {"risk_score", "ai_sentiment", "ai_score"}
        )

    def translate(
        self,
        raw: Mapping[str, Any],
        *,
        mappings: list[Mapping[str, Any]] | tuple[FieldMapEntry, ...] | list[FieldMapEntry],
        sync_run_id: str,
        source_updated_at: datetime | None = None,
        existing_canonical: Mapping[str, Any] | None = None,
    ) -> CanonicalRecord:
        """Run Mapper→…→Versioning. Validator failures raise ``AclValidationError``."""
        entries: tuple[FieldMapEntry, ...]
        if not mappings:
            entries = ()
        elif isinstance(mappings[0], FieldMapEntry):
            # isinstance narrows element 0 only; cast the homogeneous FieldMapEntry path.
            entries = cast(tuple[FieldMapEntry, ...], tuple(mappings))
        else:
            entries = parse_field_mappings(list(mappings))
        if not (sync_run_id or "").strip():
            raise ValueError("sync_run_id is required")
        mapped = self._map(raw, entries)
        self._validate(mapped, entries)
        transformed = self._transform(mapped)
        normalized = self._normalize(transformed)
        resolved = self._resolve_conflicts(normalized, existing_canonical)
        return self._version(
            resolved,
            source_updated_at=source_updated_at,
            sync_run_id=str(sync_run_id).strip(),
        )

    # --- six internal responsibilities (not public classes) -------------------

    def _map(self, raw: Mapping[str, Any], entries: tuple[FieldMapEntry, ...]) -> dict[str, Any]:
        """Mapper — FieldMappingConfig-driven external → internal projection."""
        if not isinstance(raw, Mapping):
            raise AclValidationError("raw record must be an object")
        out: dict[str, Any] = {}
        for entry in entries:
            if entry.direction in {"pull", "bidirectional"}:
                out[entry.internal] = raw.get(entry.external)
        return out

    def _validate(self, mapped: Mapping[str, Any], entries: tuple[FieldMapEntry, ...]) -> None:
        """Validator — required presence + business rules (loud failure)."""
        required = {e.internal for e in entries if e.direction in {"pull", "bidirectional"}}
        for key in sorted(required):
            val = mapped.get(key)
            if val is None or (isinstance(val, str) and not val.strip()):
                raise AclValidationError(
                    f"ACL Validator rejected record: required field {key!r} "
                    f"missing or empty (not silently nulled)",
                    field=key,
                )
        cr = mapped.get("cr_number")
        if cr is not None and str(cr).strip():
            digits = re.sub(r"\D", "", str(cr))
            if not _CR_RE.match(digits):
                raise AclValidationError(
                    f"ACL Validator rejected record: cr_number {cr!r} " "must be 10 digits",
                    field="cr_number",
                )
        amount = mapped.get("amount")
        if amount is not None:
            try:
                if float(amount) < 0:
                    raise AclValidationError(
                        "ACL Validator rejected record: amount must be >= 0",
                        field="amount",
                    )
            except (TypeError, ValueError) as exc:
                raise AclValidationError(
                    f"ACL Validator rejected record: amount {amount!r} not numeric",
                    field="amount",
                ) from exc

    def _transform(self, mapped: Mapping[str, Any]) -> dict[str, Any]:
        """Transformer — external enums → canonical enums (no passthrough stages)."""
        out = dict(mapped)
        stage = out.get("stage")
        if stage is not None and self._stage_map:
            key = str(stage).strip()
            out["stage"] = self._stage_map.get(key, key)
        return out

    def _normalize(self, data: Mapping[str, Any]) -> dict[str, Any]:
        """Normalizer — HTML strip, phone digits, currency → minor units."""
        out = dict(data)
        if isinstance(out.get("note"), str):
            text = unescape(out["note"])
            out["note"] = _HTML_TAG_RE.sub("", text).strip()
        if out.get("phone") is not None:
            out["phone"] = re.sub(r"\D", "", str(out["phone"]))
        if out.get("amount") is not None:
            # Store minor units (halalas/cents) as int when currency present.
            major = float(out["amount"])
            out["amount_minor"] = int(round(major * 100))
        if isinstance(out.get("name"), str):
            out["name"] = " ".join(out["name"].split())
        return out

    def _resolve_conflicts(
        self,
        incoming: Mapping[str, Any],
        existing: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """ConflictResolver — source wins operational; SalesOS wins AI fields."""
        if not existing:
            return dict(incoming)
        merged = dict(existing)
        for key, value in incoming.items():
            if key in self._salesos_authored:
                # Keep SalesOS-authored; never re-ingest AI echo from source.
                continue
            if key in self._operational or key not in existing:
                merged[key] = value
            # else: leave existing for non-operational unknowns
        return merged

    def _version(
        self,
        payload: Mapping[str, Any],
        *,
        source_updated_at: datetime | None,
        sync_run_id: str,
    ) -> CanonicalRecord:
        """Versioning — stamp source_updated_at + sync_run_id for debugability."""
        at = source_updated_at
        if at is not None and at.tzinfo is None:
            at = at.replace(tzinfo=UTC)
        return CanonicalRecord(
            payload=dict(payload),
            source_updated_at=at,
            sync_run_id=sync_run_id,
            meta={"acl": "OdooTranslator", "stages": 6},
        )
