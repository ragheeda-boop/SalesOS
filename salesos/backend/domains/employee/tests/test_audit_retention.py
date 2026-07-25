"""Unit tests for EmployeeAuditLogger and GDPR retention policy."""

import pytest
from datetime import datetime, timezone, timedelta

from domains.employee.retention import (
    PII_FIELDS,
    NON_PII_FIELDS,
    RETENTION_DAYS_SOFT_DELETED,
    RETENTION_DAYS_INACTIVE,
    is_eligible_for_purge,
    mask_pii_field,
)


class TestMaskPIIField:
    def test_mask_phone(self):
        assert mask_pii_field("phone", "+966555123456") == "****3456"
        assert mask_pii_field("phone", "1234") == "****"
        assert mask_pii_field("phone", None) == "****"

    def test_mask_email(self):
        result = mask_pii_field("email", "ahmed@company.com")
        assert "****" in result
        assert "@company.com" in result
        assert result.startswith("ah")

    def test_no_mask_non_pii(self):
        assert mask_pii_field("role", "manager") == "manager"
        assert mask_pii_field("department", "Sales") == "Sales"


class TestIsEligibleForPurge:
    def test_not_eligible_if_not_deleted(self):
        assert is_eligible_for_purge(None) is False

    def test_not_eligible_within_retention(self):
        recent = datetime.now(timezone.utc) - timedelta(days=10)
        assert is_eligible_for_purge(recent) is False

    def test_eligible_after_retention(self):
        old = datetime.now(timezone.utc) - timedelta(days=40)
        assert is_eligible_for_purge(old) is True

    def test_eligible_exactly_at_boundary(self):
        boundary = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS_SOFT_DELETED)
        assert is_eligible_for_purge(boundary) is True


class TestPIIFields:
    def test_sensitive_fields_defined(self):
        assert "email" in PII_FIELDS
        assert "phone" in PII_FIELDS
        assert PII_FIELDS["phone"] == "sensitive"
        assert PII_FIELDS["password_hash"] == "sensitive_never_exposed"

    def test_non_pii_fields_defined(self):
        assert "role" in NON_PII_FIELDS
        assert "department" in NON_PII_FIELDS
        assert "tenant_id" in NON_PII_FIELDS
