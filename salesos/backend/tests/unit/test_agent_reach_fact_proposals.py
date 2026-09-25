"""Conservative Agent Reach to Fact Review bridge policy tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.modules.agent_reach.fact_proposals import (
    _evidence_company_matches_company,
    _evidence_supports_proposed_value,
    _fact_evidence_from_agent_row,
    _idempotency_token,
    _public_https_source_url,
)
from app.modules.company.models import Company
from app.modules.facts.service import FactPolicyRejected
from domains.commercial.evidence.contracts.models import ConfidenceLevel, EvidenceKind

TENANT = uuid.UUID("76285a27-7fea-44a5-8ca1-71cdbbbdd006")
COMPANY = uuid.UUID("dd93c8a7-6262-4b9c-a9b9-06bbab67933c")
EVIDENCE = uuid.UUID("23f4f0fa-1542-4d32-aa4e-082183217c8b")
EXPECTED_EVIDENCE_CONFIDENCE = 0.4
COLLECTED_AT = datetime(2026, 9, 21, 12, tzinfo=UTC)


def agent_row(**overrides):
    row = {
        "id": str(EVIDENCE),
        "channel": "web",
        "source_url": "https://www.example.com/about?utm_source=probe#team",
        "title": "Company overview",
        "summary": "The page lists the business address in Riyadh.",
        "collected_at": COLLECTED_AT,
    }
    row.update(overrides)
    return row


def test_agent_reach_source_always_becomes_a_cited_claim_without_raw_payload():
    evidence = _fact_evidence_from_agent_row(agent_row())

    assert evidence.evidence_kind is EvidenceKind.CITED_CLAIM
    assert evidence.confidence_level is ConfidenceLevel.UNKNOWN
    assert evidence.confidence == EXPECTED_EVIDENCE_CONFIDENCE
    assert evidence.source.source_domain == "agent_reach"
    assert evidence.source.source_type == "public_web_web"
    assert evidence.source.source_name == "www.example.com"
    assert evidence.data["source_url"] == "https://www.example.com/about"
    assert "raw_data" not in evidence.data
    assert "Riyadh" in evidence.description


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/company",
        "https://localhost/company",
        "https://company.local/company",
        "https://user:pass@example.com/company",
        "https://127.0.0.1/company",
        "https://10.0.0.3/company",
        "https://127.1/company",
        "https://2130706433/company",
        "https://0x7f000001/company",
        "https://example..com/company",
        "https://-example.com/company",
        "https://example.com-/company",
        "https://example.home.arpa/company",
        "https://example.com:444/company",
        "https://example.com/company with spaces",
    ],
)
def test_agent_reach_source_url_rejects_nonpublic_or_unsafe_urls(url):
    with pytest.raises(FactPolicyRejected):
        _public_https_source_url(url)


def test_agent_reach_source_url_strips_query_and_fragment():
    safe_url, host = _public_https_source_url("https://Example.com:443/company?token=secret#team")
    assert safe_url == "https://example.com/company"
    assert host == "example.com"


def test_agent_reach_source_url_normalizes_internationalized_domain():
    safe_url, host = _public_https_source_url("https://münich.example.com/company")
    assert safe_url == "https://xn--mnich-kva.example.com/company"
    assert host == "xn--mnich-kva.example.com"


@pytest.mark.parametrize(
    "overrides",
    [
        {"id": "not-a-uuid"},
        {"channel": ""},
        {"channel": "untrusted-channel"},
        {"channel": "google_maps"},
        {"collected_at": datetime(2026, 9, 21)},
    ],
)
def test_invalid_persisted_agent_reach_metadata_is_rejected(overrides):
    with pytest.raises(FactPolicyRejected):
        _fact_evidence_from_agent_row(agent_row(**overrides))


def test_fact_proposal_idempotency_is_deterministic_and_scoped_to_value_and_evidence():
    first = _idempotency_token(
        tenant_id=TENANT,
        company_id=COMPANY,
        field_name="city",
        proposed_value="Riyadh",
        evidence_id=EVIDENCE,
    )
    assert first == _idempotency_token(
        tenant_id=TENANT,
        company_id=COMPANY,
        field_name="city",
        proposed_value="Riyadh",
        evidence_id=EVIDENCE,
    )
    assert first != _idempotency_token(
        tenant_id=TENANT,
        company_id=COMPANY,
        field_name="city",
        proposed_value="Jeddah",
        evidence_id=EVIDENCE,
    )
    assert first != _idempotency_token(
        tenant_id=TENANT,
        company_id=COMPANY,
        field_name="city",
        proposed_value="Riyadh",
        evidence_id=uuid.uuid4(),
    )
    with pytest.raises(FactPolicyRejected, match="finite JSON"):
        _idempotency_token(
            tenant_id=TENANT,
            company_id=COMPANY,
            field_name="city",
            proposed_value=float("nan"),
            evidence_id=EVIDENCE,
        )


def test_agent_reach_company_link_requires_exact_normalized_name_match():
    company = Company(
        tenant_id=TENANT,
        name_ar="شركة الاختبار",
        name_en="Example Company",
    )
    assert _evidence_company_matches_company(
        {"company_name": "  EXAMPLE   COMPANY "}, company
    )
    assert _evidence_company_matches_company({"company_name": "شركة الاختبار"}, company)
    assert not _evidence_company_matches_company({"company_name": "Similar Example Co"}, company)


def test_proposed_value_must_appear_as_a_whole_phrase_in_captured_evidence():
    row = agent_row(title="Riyadh office", summary="The company lists its address in Riyadh.")

    assert _evidence_supports_proposed_value(row, "RIYADH")
    assert _evidence_supports_proposed_value(row, "Riyadh office")
    assert not _evidence_supports_proposed_value(row, "Riya")
    assert not _evidence_supports_proposed_value(row, "Jeddah")
    assert not _evidence_supports_proposed_value(row, 42)
    assert not _evidence_supports_proposed_value(row, "x" * 513)
