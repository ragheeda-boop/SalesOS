"""Deterministic evidence scoring and fact decision policy (ADR-0113)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..contracts.models import EvidenceBand, EvidenceItem, EvidenceKind

EVIDENCE_WEIGHTS: dict[EvidenceKind, float] = {
    EvidenceKind.OFFICIAL_REGISTRY: 0.98,
    EvidenceKind.CR_NUMBER_EXACT_MATCH: 0.95,
    EvidenceKind.LICENSE_VERIFIED: 0.90,
    EvidenceKind.ENTITY_RESOLUTION_MERGE: 0.85,
    EvidenceKind.CRM_EMAIL_SIGNATURE: 0.80,
    EvidenceKind.CRM_MEETING_ATTENDANCE: 0.70,
    EvidenceKind.CRM_SYSTEM_RECORD: 0.55,
    EvidenceKind.GOVERNMENT_SOURCE: 0.65,
    EvidenceKind.CITED_CLAIM: 0.40,
    EvidenceKind.NAME_MATCH_ONLY: 0.35,
    EvidenceKind.EMPLOYER_MATCH_ONLY: 0.20,
    EvidenceKind.CONTRADICTION: 0.00,
}

PRIMARY_EVIDENCE_KINDS = frozenset(
    {
        EvidenceKind.OFFICIAL_REGISTRY,
        EvidenceKind.CR_NUMBER_EXACT_MATCH,
        EvidenceKind.LICENSE_VERIFIED,
        EvidenceKind.ENTITY_RESOLUTION_MERGE,
        EvidenceKind.CRM_EMAIL_SIGNATURE,
        EvidenceKind.CRM_MEETING_ATTENDANCE,
        EvidenceKind.GOVERNMENT_SOURCE,
    }
)
MAX_EVIDENCE_SCORE = 0.99
CONTRADICTION_SCORE_CAP = 0.45
VERIFIED_THRESHOLD = 0.85
PROBABLE_THRESHOLD = 0.55
DISCARD_THRESHOLD = 0.30

# ADR-0114's field classification is the final write-safety gate. Keep this
# allowlist explicit so a newly added/renamed field cannot become writable just
# because it has strong evidence. Identity fields are never agent-written.
PROTECTED_FACT_FIELDS = frozenset(
    {
        "id",
        "tenant_id",
        "created_at",
        "updated_at",
        "is_golden_record",
        "parent_company_id",
        "source_ids",
        "embedding",
    }
)
REVIEW_ONLY_FACT_FIELDS = frozenset({"cr_number"})
AGENT_UPDATABLE_FACT_FIELDS = frozenset(
    {
        "city",
        "region",
        "industry",
        "website",
        "employees_count",
        "annual_revenue",
        "activity_description",
        "legal_form",
        "latitude",
        "longitude",
        "phone",
        "email",
        "address",
        "capital",
        "incorporation_date",
        "confidence_score",
    }
)


@dataclass(frozen=True)
class EvidenceScore:
    score: float
    uncapped_score: float
    contradiction_present: bool
    primary_source_count: int
    evidence_count: int


@dataclass(frozen=True)
class FactDecision:
    band: EvidenceBand
    store: bool
    auto_apply: bool
    approval_required: bool
    reason: str


def _source_key(item: EvidenceItem) -> str:
    source = item.source
    if source.source_id:
        return source.source_id
    # Without a stable source ID, keep separate records separate. Guessing that
    # provider/name text identifies the same source can erase independent proof.
    return f"unkeyed:{item.id}"


def score_evidence(items: Iterable[EvidenceItem]) -> EvidenceScore:
    """Combine classified evidence strengths; item confidence is informational.

    Applies the ADR-0113 noisy-OR formula and caps any contradictory bundle at
    0.45. Repeated evidence from the same source and kind counts once.
    """
    unique: dict[tuple[str, EvidenceKind], EvidenceItem] = {}
    for item in items:
        if item.evidence_kind is None:
            continue
        key = (_source_key(item), item.evidence_kind)
        unique.setdefault(key, item)

    selected = list(unique.values())
    remaining = 1.0
    for item in selected:
        remaining *= 1.0 - EVIDENCE_WEIGHTS[item.evidence_kind]
    raw_score = 1.0 - remaining if selected else 0.0
    contradiction = any(
        item.evidence_kind == EvidenceKind.CONTRADICTION for item in selected
    )
    capped_score = min(raw_score, MAX_EVIDENCE_SCORE)
    score = min(capped_score, CONTRADICTION_SCORE_CAP) if contradiction else capped_score
    primary_sources = {
        _source_key(item)
        for item in selected
        if item.evidence_kind in PRIMARY_EVIDENCE_KINDS
    }
    return EvidenceScore(
        score=round(score, 3),
        uncapped_score=round(raw_score, 3),
        contradiction_present=contradiction,
        primary_source_count=len(primary_sources),
        evidence_count=len(selected),
    )


def decide_fact(field_name: str, evidence: Iterable[EvidenceItem]) -> FactDecision:
    """Apply ADR-0113 scoring behind ADR-0114's fail-closed field boundary.

    Unclassified evidence cannot support a new canonical fact decision. It
    remains available in its evidence/insight record, but does not create an
    auto-applied or proposed canonical fact through this policy. This prevents
    a typed subset from masking legacy evidence with unknown provenance.
    Strong evidence for identity fields can be retained as a proposal for a
    human; ADR-0114 still forbids agent application of those fields.
    """
    if field_name in PROTECTED_FACT_FIELDS:
        return FactDecision(
            EvidenceBand.DISCARD,
            False,
            False,
            False,
            "agent_write_prohibited_for_identity_field",
        )

    items = list(evidence)
    if any(item.evidence_kind is None for item in items):
        return FactDecision(
            EvidenceBand.DISCARD,
            False,
            False,
            False,
            "unclassified_evidence_not_eligible_for_fact_decision",
        )

    score = score_evidence(items)
    if score.score < DISCARD_THRESHOLD:
        return FactDecision(EvidenceBand.DISCARD, False, False, False, "below_0.30")

    min_sources_for_verified = 2 if field_name == "industry" else 1
    always_proposed = field_name in {"employees_count", "description"}
    verified = (
        score.score >= VERIFIED_THRESHOLD
        and score.primary_source_count >= min_sources_for_verified
    )
    if verified:
        if (
            always_proposed
            or field_name in REVIEW_ONLY_FACT_FIELDS
            or field_name not in AGENT_UPDATABLE_FACT_FIELDS
        ):
            return FactDecision(
                EvidenceBand.VERIFIED,
                True,
                False,
                True,
                (
                    "field_requires_proposal_review"
                    if always_proposed
                    else (
                        "identity_field_requires_human_review"
                        if field_name in REVIEW_ONLY_FACT_FIELDS
                        else "field_not_allowlisted_for_auto_apply"
                    )
                ),
            )
        return FactDecision(EvidenceBand.VERIFIED, True, True, False, "verified_primary_evidence")
    band = EvidenceBand.PROBABLE if score.score >= PROBABLE_THRESHOLD else EvidenceBand.POSSIBLE
    return FactDecision(band, True, False, True, "approval_required")
