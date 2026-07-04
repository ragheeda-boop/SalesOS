"""Tests for SearchSpecification, FieldSpecification, AndSpecification, OrSpecification, SpecificationBuilder."""

from dataclasses import dataclass

from domains.search.engine.specifications import (
    AndSpecification,
    FieldSpecification,
    OrSpecification,
    SearchCondition,
    SpecificationBuilder,
)


@dataclass
class FakeItem:
    name_ar: str = ""
    name_en: str = ""
    status: str = "active"
    city: str = ""
    cr_number: str = ""
    confidence_score: float = 0.0


def test_field_specification_eq():
    spec = FieldSpecification(field="status", operator="eq", value="active")
    assert spec.is_satisfied_by(FakeItem(status="active"))
    assert not spec.is_satisfied_by(FakeItem(status="inactive"))


def test_field_specification_neq():
    spec = FieldSpecification(field="status", operator="neq", value="inactive")
    assert spec.is_satisfied_by(FakeItem(status="active"))
    assert not spec.is_satisfied_by(FakeItem(status="inactive"))


def test_field_specification_contains_arabic():
    spec = FieldSpecification(field="name_ar", operator="contains", value="شركة")
    assert spec.is_satisfied_by(FakeItem(name_ar="شركة الأمل"))
    assert not spec.is_satisfied_by(FakeItem(name_ar="مؤسسة السلام"))


def test_field_specification_startswith():
    spec = FieldSpecification(field="city", operator="startswith", value="ال")
    assert spec.is_satisfied_by(FakeItem(city="الرياض"))
    assert not spec.is_satisfied_by(FakeItem(city="جدة"))


def test_field_specification_in():
    spec = FieldSpecification(field="status", operator="in", value=["active", "pending"])
    assert spec.is_satisfied_by(FakeItem(status="active"))
    assert not spec.is_satisfied_by(FakeItem(status="suspended"))


def test_field_specification_gte():
    spec = FieldSpecification(field="confidence_score", operator="gte", value=0.5)
    assert spec.is_satisfied_by(FakeItem(confidence_score=0.8))
    assert not spec.is_satisfied_by(FakeItem(confidence_score=0.3))


def test_field_specification_lte():
    spec = FieldSpecification(field="confidence_score", operator="lte", value=0.5)
    assert spec.is_satisfied_by(FakeItem(confidence_score=0.3))
    assert not spec.is_satisfied_by(FakeItem(confidence_score=0.8))


def test_and_specification_all_true():
    spec = AndSpecification(specs=[
        FieldSpecification(field="status", operator="eq", value="active"),
        FieldSpecification(field="city", operator="contains", value="الرياض"),
    ])
    assert spec.is_satisfied_by(FakeItem(status="active", city="الرياض"))
    assert not spec.is_satisfied_by(FakeItem(status="active", city="جدة"))


def test_or_specification_any_true():
    spec = OrSpecification(specs=[
        FieldSpecification(field="status", operator="eq", value="active"),
        FieldSpecification(field="status", operator="eq", value="pending"),
    ])
    assert spec.is_satisfied_by(FakeItem(status="active"))
    assert spec.is_satisfied_by(FakeItem(status="pending"))
    assert not spec.is_satisfied_by(FakeItem(status="suspended"))


def test_specification_builder_simple():
    spec = SpecificationBuilder.from_filters({"status": "active"})
    assert isinstance(spec, FieldSpecification)
    assert spec.is_satisfied_by(FakeItem(status="active"))


def test_specification_builder_and():
    spec = SpecificationBuilder.from_filters({"status": "active", "city": "الرياض"})
    assert isinstance(spec, AndSpecification)
    assert len(spec.specs) == 2


def test_specification_builder_with_ops():
    spec = SpecificationBuilder.from_filters({"confidence_score": {"gte": 0.5}})
    assert isinstance(spec, FieldSpecification)
    assert spec.operator == "gte"


def test_specification_builder_empty():
    spec = SpecificationBuilder.from_filters({})
    assert isinstance(spec, AndSpecification)
    assert len(spec.specs) == 0


def test_search_condition():
    c = SearchCondition(field="status", operator="eq", value="active")
    assert c.field == "status"
    assert c.operator == "eq"
    assert c.value == "active"
