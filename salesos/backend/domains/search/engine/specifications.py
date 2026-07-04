from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchCondition:
    field: str
    operator: str
    value: Any


class SearchSpecification(ABC):

    @abstractmethod
    def to_condition(self) -> SearchCondition | None: ...

    @abstractmethod
    def is_satisfied_by(self, item: Any) -> bool: ...


@dataclass
class FieldSpecification(SearchSpecification):

    field: str
    operator: str
    value: Any

    def to_condition(self) -> SearchCondition:
        return SearchCondition(field=self.field, operator=self.operator, value=self.value)

    def is_satisfied_by(self, item: Any) -> bool:
        actual = getattr(item, self.field, None)
        if self.operator == "eq":
            return actual == self.value
        if self.operator == "neq":
            return actual != self.value
        if self.operator == "contains":
            return actual is not None and self.value.lower() in str(actual).lower()
        if self.operator == "startswith":
            return actual is not None and str(actual).lower().startswith(self.value.lower())
        if self.operator == "in":
            return actual in (self.value or [])
        if self.operator == "gte":
            return actual is not None and actual >= self.value
        if self.operator == "lte":
            return actual is not None and actual <= self.value
        return False


@dataclass
class AndSpecification(SearchSpecification):

    specs: list[SearchSpecification] = field(default_factory=list)

    def to_condition(self) -> SearchCondition | None:
        return None

    def is_satisfied_by(self, item: Any) -> bool:
        return all(s.is_satisfied_by(item) for s in self.specs)


@dataclass
class OrSpecification(SearchSpecification):

    specs: list[SearchSpecification] = field(default_factory=list)

    def to_condition(self) -> SearchCondition | None:
        return None

    def is_satisfied_by(self, item: Any) -> bool:
        return any(s.is_satisfied_by(item) for s in self.specs)


class SpecificationBuilder:

    ALLOWED_OPS = {"eq", "neq", "gt", "gte", "lt", "lte", "in", "contains", "startswith", "endswith"}

    @staticmethod
    def from_filters(filters: dict[str, Any]) -> SearchSpecification:
        specs: list[SearchSpecification] = []
        for field, value in filters.items():
            if isinstance(value, dict):
                for op, val in value.items():
                    if op in SpecificationBuilder.ALLOWED_OPS:
                        specs.append(FieldSpecification(field=field, operator=op, value=val))
            else:
                specs.append(FieldSpecification(field=field, operator="eq", value=value))
        if not specs:
            return AndSpecification()
        if len(specs) == 1:
            return specs[0]
        return AndSpecification(specs=specs)
