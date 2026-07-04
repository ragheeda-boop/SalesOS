"""Base Data Contract — defines the interface all source contracts must implement."""

import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator


class BaseSourceContract(ABC, BaseModel):
    """Abstract base for all government source data contracts.

    Each source contract inherits from this and defines:
      - source_slug: unique identifier (e.g., 'balady')
      - priority: source priority used by ER (100 = highest)
      - Canonical fields: name_ar, cr_number, city, status, etc.
    """

    source_slug: ClassVar[str] = ""
    priority: ClassVar[int] = 0

    cr_number: str
    name_ar: str | None = None
    name_en: str | None = None
    city: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="allow")

    @abstractmethod
    def to_canonical(self) -> dict[str, Any]:
        ...

    @field_validator("cr_number")
    @classmethod
    def validate_cr_number(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v)
        if not cleaned.isdigit() or len(cleaned) < 5:
            raise ValueError(f"Invalid CR number: {v}")
        return cleaned
