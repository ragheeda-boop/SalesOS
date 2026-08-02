"""STORY-09-05 — OBJ-020 TaskCaseExtension Value Object (not Aggregate).

Attached 0..1 to Task; validated per case_type JSON Schema.
No independent identity. No invented secrets. Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from jsonschema import Draft202012Validator

CaseType = Literal["financing", "insurance", "generic"]

CASE_TYPES: frozenset[str] = frozenset({"financing", "insurance", "generic"})

# Per ARB §3 — studio fields drive classification (CI/certify names, not secrets).
FINANCING_FIELDS = (
    "x_studio_financing_amount_requested",
    "x_studio_approved_financing_amount",
    "x_studio_unified_agreement_status",
)
INSURANCE_FIELDS = (
    "x_studio_coverage_value",
    "x_studio_policy_provider",
)

_FINANCING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "financing_amount_requested": {"type": ["number", "null"], "minimum": 0},
        "approved_financing_amount": {"type": ["number", "null"], "minimum": 0},
        "unified_agreement_status": {"type": ["string", "null"], "maxLength": 120},
    },
    "required": [],
}

_INSURANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "coverage_value": {"type": ["number", "null"], "minimum": 0},
        "policy_provider": {"type": ["string", "null"], "maxLength": 200},
    },
    "required": [],
}

_GENERIC_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "note": {"type": ["string", "null"], "maxLength": 2000},
    },
    "required": [],
}

CASE_TYPE_SCHEMAS: dict[str, dict[str, Any]] = {
    "financing": _FINANCING_SCHEMA,
    "insurance": _INSURANCE_SCHEMA,
    "generic": _GENERIC_SCHEMA,
}


class TaskCaseExtensionValidationError(ValueError):
    """Raised when VO payload fails per-case_type JSON Schema."""

    def __init__(self, message: str, *, case_type: str | None = None) -> None:
        self.case_type = case_type
        super().__init__(message)


@dataclass(frozen=True)
class TaskCaseExtension:
    """Value Object on Task — no independent id / aggregate root."""

    case_type: CaseType
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        validate_case_extension(self.case_type, self.payload)

    def to_dict(self) -> dict[str, Any]:
        return {"case_type": self.case_type, "payload": dict(self.payload)}


def validate_case_extension(case_type: str, payload: dict[str, Any]) -> None:
    if case_type not in CASE_TYPE_SCHEMAS:
        raise TaskCaseExtensionValidationError(
            f"unknown case_type {case_type!r}",
            case_type=case_type,
        )
    if not isinstance(payload, dict):
        raise TaskCaseExtensionValidationError(
            "payload must be an object",
            case_type=case_type,
        )
    validator = Draft202012Validator(CASE_TYPE_SCHEMAS[case_type])
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        err = errors[0]
        path = ".".join(str(p) for p in err.path) or "(root)"
        raise TaskCaseExtensionValidationError(
            f"TaskCaseExtension JSON Schema rejected {case_type!r} " f"at {path}: {err.message}",
            case_type=case_type,
        )


def _num(value: Any) -> float | None:
    if value is None or value is False or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _str(value: Any) -> str | None:
    if value is None or value is False:
        return None
    text = str(value).strip()
    return text or None


def _populated(raw: dict[str, Any], fields: tuple[str, ...]) -> bool:
    for key in fields:
        val = raw.get(key)
        if val is None or val is False or val == "":
            continue
        return True
    return False


def classify_case_type(raw: dict[str, Any]) -> CaseType | None:
    """Infer financing/insurance/generic from Odoo studio field population."""
    has_fin = _populated(raw, FINANCING_FIELDS)
    has_ins = _populated(raw, INSURANCE_FIELDS)
    if has_fin and not has_ins:
        return "financing"
    if has_ins and not has_fin:
        return "insurance"
    if has_fin and has_ins:
        # Prefer financing when both present (Muhide underwriting-first).
        return "financing"
    # Generic only when task is explicitly tagged; else no extension.
    if raw.get("x_studio_case_type") == "generic" or raw.get("case_type") == "generic":
        return "generic"
    return None


def build_task_case_extension(raw: dict[str, Any]) -> TaskCaseExtension | None:
    """Build VO from Odoo project.task row; None if no case fields."""
    case_type = classify_case_type(raw)
    if case_type is None:
        return None
    if case_type == "financing":
        payload = {
            "financing_amount_requested": _num(raw.get("x_studio_financing_amount_requested")),
            "approved_financing_amount": _num(raw.get("x_studio_approved_financing_amount")),
            "unified_agreement_status": _str(raw.get("x_studio_unified_agreement_status")),
        }
    elif case_type == "insurance":
        payload = {
            "coverage_value": _num(raw.get("x_studio_coverage_value")),
            "policy_provider": _str(raw.get("x_studio_policy_provider")),
        }
    else:
        payload = {"note": _str(raw.get("description") or raw.get("name"))}
    return TaskCaseExtension(case_type=case_type, payload=payload)
