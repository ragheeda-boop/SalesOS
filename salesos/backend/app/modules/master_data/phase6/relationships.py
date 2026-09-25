"""Phase 6 — Contact <-> company relationship evidence.

Contract: person↔company records carry status (INFERRED / VERIFIED), source,
observed_at, linking_basis, confidence/evidence, and both Global IDs.

Status rules (evidence-first, no fabrication):
  VERIFIED  — authoritative linkage: the source explicitly associates the
              person with the company (e.g. contact row Master Account ID
              resolved to a company Global ID), OR person.company_global_id is
              already set on the Global Person record by an authoritative path.
  INFERRED  — derived linkage: person email domain matches the company real
              domain, or the person is the sole owner/decision-maker of a
              company and no higher-evidence basis exists. Never auto-upgraded
              to VERIFIED without an authoritative source-backed association.

Linking bases:
  source_ma_assignment (VERIFIED)
  person_company_field   (VERIFIED)
  email_domain_match     (INFERRED)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RelationshipEvidence:
    person_global_id: str
    company_global_id: str
    relationship_type: str
    status: str            # VERIFIED / INFERRED
    linking_basis: str
    confidence: float
    evidence: dict
    source_id: str | None
    observed_at: str | None


def infer_relationship(
    *,
    person_global_id: str,
    company_global_id: str,
    relationship_type: str = "account",
    person_company_global_id: str | None = None,
    source_ma_assignment: bool = False,
    email_domain_match: bool = False,
    person_email_domain: str | None = None,
    company_domain: str | None = None,
    source_id: str | None = None,
    observed_at: str | None = None,
) -> RelationshipEvidence:
    """Build a contact→company relationship record with evidence classification.

    VERIFIED bases (authoritative): source_ma_assignment or the person is
    already assigned to this company (person_company_global_id == company).
    INFERRED bases: email_domain_match.
    """
    if source_ma_assignment or (
        person_company_global_id and person_company_global_id == company_global_id
    ):
        status, basis, confidence = "VERIFIED", (
            "person_company_field" if person_company_global_id else "source_ma_assignment"
        ), 0.95
    elif email_domain_match:
        status, basis, confidence = "INFERRED", "email_domain_match", 0.6
    else:
        status, basis, confidence = "INFERRED", "unknown", 0.3

    evidence = {
        "person_email_domain": person_email_domain,
        "company_domain": company_domain,
        "person_company_global_id": person_company_global_id,
        "source_ma_assignment": source_ma_assignment,
        "email_domain_match": email_domain_match,
    }
    return RelationshipEvidence(
        person_global_id=person_global_id,
        company_global_id=company_global_id,
        relationship_type=relationship_type,
        status=status,
        linking_basis=basis,
        confidence=confidence,
        evidence=evidence,
        source_id=source_id,
        observed_at=observed_at,
    )
