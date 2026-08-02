"""STORY-10-01 — Reserved system columns for CAP-082 collision checks.

Custom field keys must not shadow ORM / system columns on Company, Contact,
or Opportunity. No invented secrets. Not Production GO.
"""

from __future__ import annotations

from typing import Literal

ObjectKey = Literal["company", "contact", "opportunity"]

# Shared system keys always reserved across objects.
_COMMON_RESERVED: frozenset[str] = frozenset(
    {
        "id",
        "tenant_id",
        "created_at",
        "updated_at",
        "metadata",
        "extra_metadata",
        "custom_fields",
        "search_vector",
        "embedding_vector",
    }
)

RESERVED_COLUMNS: dict[ObjectKey, frozenset[str]] = {
    "company": _COMMON_RESERVED
    | frozenset(
        {
            "name_ar",
            "name_en",
            "cr_number",
            "cr_type",
            "status",
            "city",
            "region",
            "latitude",
            "longitude",
            "postal_code",
            "phone",
            "email",
            "website",
            "industry",
            "activity_description",
            "legal_form",
            "employee_count",
            "capital",
            "source_id",
        }
    ),
    "contact": _COMMON_RESERVED
    | frozenset(
        {
            "company_id",
            "name",
            "name_ar",
            "email",
            "phone",
            "mobile",
            "position",
            "position_ar",
            "department",
            "is_primary",
            "source",
            "confidence_score",
            "tags",
        }
    ),
    "opportunity": _COMMON_RESERVED
    | frozenset(
        {
            "company_id",
            "title",
            "stage",
            "estimated_value",
            "confidence",
            "win_probability",
            "source",
            "source_action_id",
            "buying_intent",
            "relationship_strength",
            "risk_level",
            "assignee_id",
            "expected_close_date",
            "stage_changed_at",
            "last_activity_at",
        }
    ),
}

SUPPORTED_OBJECT_KEYS: frozenset[str] = frozenset(RESERVED_COLUMNS.keys())


def reserved_for(object_key: str) -> frozenset[str]:
    key = (object_key or "").strip().lower()
    if key not in RESERVED_COLUMNS:
        raise ValueError(
            f"unsupported object_key {object_key!r}; expected company|contact|opportunity"
        )
    return RESERVED_COLUMNS[key]  # type: ignore[index]


def is_reserved(object_key: str, field_key: str) -> bool:
    return (field_key or "").strip().lower() in reserved_for(object_key)
