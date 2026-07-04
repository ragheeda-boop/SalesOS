"""Metadata Engine — dynamic entity description system.

Every entity in the system can declare metadata that controls how it is
displayed, validated, searched, embedded, and permissioned without code
changes. This is the foundation of the Internal Developer Platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FieldType(Enum):
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RELATION = "relation"
    JSON = "json"
    VECTOR = "vector"


class UiWidget(Enum):
    TEXT_INPUT = "text_input"
    TEXTAREA = "textarea"
    NUMBER_INPUT = "number_input"
    DATE_PICKER = "date_picker"
    DROPDOWN = "dropdown"
    MULTI_SELECT = "multi_select"
    CHECKBOX = "checkbox"
    TOGGLE = "toggle"
    RADIO = "radio"
    RICH_TEXT = "rich_text"
    FILE_UPLOAD = "file_upload"
    LOCATION_PICKER = "location_picker"
    AUTOCOMPLETE = "autocomplete"


@dataclass
class FieldMetadata:
    """Complete metadata for a single entity field."""

    name: str
    label: str
    label_ar: str
    field_type: FieldType
    required: bool = False
    unique: bool = False
    read_only: bool = False
    searchable: bool = False
    sortable: bool = False
    filterable: bool = False
    embeddable: bool = False
    scorable: bool = False
    translatable: bool = False
    default_value: Any = None
    widget: UiWidget | None = None
    validators: list[str] = field(default_factory=list)
    options: list[str] | None = None
    placeholder: str = ""
    placeholder_ar: str = ""
    help_text: str = ""
    help_text_ar: str = ""
    order: int = 0
    group: str = "default"
    group_ar: str = "عام"
    permissions: dict[str, str] = field(default_factory=dict)


@dataclass
class EntityMetadata:
    """Complete metadata for an entity type."""

    module: str
    entity: str
    label: str
    label_ar: str
    label_plural: str
    label_plural_ar: str
    description: str
    description_ar: str
    fields: dict[str, FieldMetadata] = field(default_factory=dict)
    default_sort_field: str = "created_at"
    default_sort_order: str = "desc"
    page_size_default: int = 20
    audit_enabled: bool = True
    search_enabled: bool = True
    embedding_enabled: bool = False
    cache_ttl: int = 300
    permissions: dict[str, str] = field(default_factory=dict)


class MetadataRegistry:
    """Central registry for all entity metadata definitions."""

    _entities: dict[str, EntityMetadata] = {}

    @classmethod
    def register(cls, meta: EntityMetadata) -> None:
        key = f"{meta.module}.{meta.entity}"
        cls._entities[key] = meta

    @classmethod
    def get(cls, module: str, entity: str) -> EntityMetadata | None:
        return cls._entities.get(f"{module}.{entity}")

    @classmethod
    def get_by_module(cls, module: str) -> list[EntityMetadata]:
        return [v for k, v in cls._entities.items() if k.startswith(f"{module}.")]

    @classmethod
    def all(cls) -> dict[str, EntityMetadata]:
        return dict(cls._entities)
