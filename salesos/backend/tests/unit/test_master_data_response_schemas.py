"""Regression tests for UUID-backed Master Data response serialization."""

from datetime import UTC, datetime
from uuid import uuid4

from app.modules.master_data.schemas import GlobalCompanyResponse, GlobalPersonResponse


def test_global_company_response_accepts_database_uuid_and_serializes_as_string():
    company_id = uuid4()
    now = datetime(2026, 9, 20, tzinfo=UTC)

    response = GlobalCompanyResponse(
        id=company_id,
        slug="global-company",
        canonical_name="Example Company",
        canonical_name_ar=None,
        cr_number=None,
        vat_number=None,
        unified_national_number=None,
        status="active",
        created_at=now,
        updated_at=None,
    )

    assert response.id == company_id
    assert response.model_dump(mode="json")["id"] == str(company_id)


def test_global_person_response_accepts_uuid_person_and_company_ids():
    person_id = uuid4()
    company_id = uuid4()
    now = datetime(2026, 9, 20, tzinfo=UTC)

    response = GlobalPersonResponse(
        id=person_id,
        slug="global-person",
        canonical_name="Example Person",
        email=None,
        phone=None,
        company_global_id=company_id,
        job_title=None,
        status="active",
        created_at=now,
        updated_at=None,
    )

    serialized = response.model_dump(mode="json")
    assert serialized["id"] == str(person_id)
    assert serialized["company_global_id"] == str(company_id)


def test_registry_number_kind_distinguishes_unified_number_from_cr():
    from app.modules.master_data.schemas import registry_number_kind

    assert registry_number_kind("7041460564") == "UNIFIED_NATIONAL_NUMBER"
    assert registry_number_kind("1010123456") == "COMMERCIAL_REGISTRATION"
    assert registry_number_kind("\u202d4030123456\u202c") == "COMMERCIAL_REGISTRATION"
    assert registry_number_kind("2230") == "UNKNOWN"
    assert registry_number_kind(None) is None
