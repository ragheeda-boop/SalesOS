"""Unit tests for Phase 6 contact relationships module."""

import pytest

from app.modules.master_data.phase6.relationships import (
    RelationshipEvidence,
    infer_relationship,
)


class TestInferRelationship:
    """Test person↔company relationship evidence inference.

    Actual behavior:
    - VERIFIED with source_ma_assignment or person_company_field: confidence 0.95
    - INFERRED with email_domain_match: confidence 0.6
    - INFERRED with no evidence: confidence 0.3, linking_basis "unknown"
    """

    def test_verified_source_ma_assignment(self):
        res = infer_relationship(
            person_global_id="person-1",
            company_global_id="company-1",
            relationship_type="contact",
            source_ma_assignment=True,
            email_domain_match=False,
            person_email_domain="user@gmail.com",
            company_domain="company.com",
            source_id="muhide_contacts",
            observed_at="2024-01-01T00:00:00Z",
        )
        assert isinstance(res, RelationshipEvidence)
        assert res.status == "VERIFIED"
        assert res.linking_basis == "source_ma_assignment"
        assert res.confidence == 0.95
        assert res.person_global_id == "person-1"
        assert res.company_global_id == "company-1"
        assert res.relationship_type == "contact"

    def test_verified_person_company_field(self):
        res = infer_relationship(
            person_global_id="person-1",
            company_global_id="company-1",
            relationship_type="contact",
            source_ma_assignment=False,
            email_domain_match=False,
            person_company_global_id="company-1",
            person_email_domain="user@gmail.com",
            company_domain="company.com",
            source_id="muhide_contacts",
            observed_at="2024-01-01T00:00:00Z",
        )
        assert res.status == "VERIFIED"
        assert res.linking_basis == "person_company_field"
        assert res.confidence == 0.95

    def test_inferred_email_domain_match(self):
        res = infer_relationship(
            person_global_id="person-1",
            company_global_id="company-1",
            relationship_type="contact",
            source_ma_assignment=False,
            email_domain_match=True,
            person_email_domain="user@company.com",
            company_domain="company.com",
            source_id="muhide_contacts",
            observed_at="2024-01-01T00:00:00Z",
        )
        assert res.status == "INFERRED"
        assert res.linking_basis == "email_domain_match"
        assert res.confidence == 0.6

    def test_inferred_no_evidence(self):
        res = infer_relationship(
            person_global_id="person-1",
            company_global_id="company-1",
            relationship_type="contact",
            source_ma_assignment=False,
            email_domain_match=False,
            person_email_domain="user@gmail.com",
            company_domain="company.com",
            source_id="muhide_contacts",
            observed_at="2024-01-01T00:00:00Z",
        )
        assert res.status == "INFERRED"
        assert res.linking_basis == "unknown"
        assert res.confidence == 0.3

    def test_evidence_structure(self):
        res = infer_relationship(
            person_global_id="person-1",
            company_global_id="company-1",
            relationship_type="contact",
            source_ma_assignment=True,
            email_domain_match=True,
            person_email_domain="user@company.com",
            company_domain="company.com",
            source_id="muhide_contacts",
            observed_at="2024-01-01T00:00:00Z",
        )
        ev = res.evidence
        assert "source_ma_assignment" in ev
        assert "email_domain_match" in ev
        assert "person_email_domain" in ev
        assert "company_domain" in ev
        assert ev["source_ma_assignment"] is True
        assert ev["email_domain_match"] is True

    def test_confidence_ordering(self):
        """VERIFIED (0.95) > INFERRED email (0.6) > INFERRED none (0.3)."""
        verified = infer_relationship(
            person_global_id="p", company_global_id="c", relationship_type="contact",
            source_ma_assignment=True, email_domain_match=False,
            source_id="s", observed_at="2024-01-01"
        )
        inferred_email = infer_relationship(
            person_global_id="p", company_global_id="c", relationship_type="contact",
            source_ma_assignment=False, email_domain_match=True,
            source_id="s", observed_at="2024-01-01"
        )
        inferred_none = infer_relationship(
            person_global_id="p", company_global_id="c", relationship_type="contact",
            source_ma_assignment=False, email_domain_match=False,
            source_id="s", observed_at="2024-01-01"
        )
        assert verified.confidence == 0.95
        assert inferred_email.confidence == 0.6
        assert inferred_none.confidence == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])