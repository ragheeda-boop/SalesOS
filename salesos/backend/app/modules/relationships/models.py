"""Commercial Relationship Model — typed, evidence-backed relationship edges.

Bounded, tenant-scoped graph vocabulary for person<->person and
person<->company relationships. This is deliberately NOT a general knowledge
graph (Knowledge Graph Runtime stays OFFLINE per ADR-108) and does NOT depend
on Neo4j. Each edge records a lifecycle: observed_at (when the relationship
was observed), superseded_at (when it stopped being current), basis (how the
edge was established) and optional evidence + confidence.

The existing ``opportunity_contacts`` junction remains the bounded
stakeholder slice of an opportunity; this model is the general
relationship-graph store and does not replace it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Roll-up roles map onto these edge types via title keyword classification
# (see buying_committee.ROLE_KEYWORDS). The taxonomy is fixed and validated.
RELATIONSHIP_EDGE_TYPES: tuple[str, ...] = (
    "reports_to",
    "influences",
    "champion_for",
    "blocks",
    "introduced_by",
)

EDGE_TYPE_SET: frozenset[str] = frozenset(RELATIONSHIP_EDGE_TYPES)

ENDPOINT_TYPES: tuple[str, ...] = ("person", "company")
ENDPOINT_TYPE_SET: frozenset[str] = frozenset(ENDPOINT_TYPES)

# How the edge was established. `basis` is free text up to 64 chars for
# source-specific labels; these cover the models we ship.
KNOWN_BASES: tuple[str, ...] = (
    "source_assignment",
    "title_keyword",
    "org_structure",
    "email_domain_match",
    "manual",
    "inferred",
    "unknown",
)

MAX_ID_LENGTH = 36


class RelationshipError(ValueError):
    """Raised when a relationship edge fails validation."""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _require_uuid(value: str, field: str) -> str:
    text_val = str(value or "").strip()
    if not text_val:
        raise RelationshipError(f"{field} required")
    try:
        return str(uuid.UUID(text_val))
    except (ValueError, AttributeError) as exc:
        raise RelationshipError(f"{field} must be a valid uuid") from exc


def _require_short_id(value: str, field: str) -> str:
    text_val = str(value or "").strip()
    if not text_val:
        raise RelationshipError(f"{field} required")
    if len(text_val) > MAX_ID_LENGTH:
        raise RelationshipError(f"{field} exceeds {MAX_ID_LENGTH} characters")
    return text_val


@dataclass
class RelationshipEdge:
    """A typed, evidence-backed relationship edge scoped to one tenant."""

    id: str
    tenant_id: str
    edge_type: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    basis: str = "unknown"
    evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence: float | None = None
    observed_at: str | None = None
    superseded_at: str | None = None
    created_by: str = ""
    created_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "edge_type": self.edge_type,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "basis": self.basis,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "observed_at": self.observed_at,
            "superseded_at": self.superseded_at,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


def normalize_edge(
    *,
    tenant_id: str,
    edge_type: str,
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
    basis: str = "unknown",
    evidence: list[dict[str, Any]] | None = None,
    confidence: float | None = None,
    observed_at: str | None = None,
    created_by: str = "",
    edge_id: str | None = None,
) -> RelationshipEdge:
    """Validate edge fields and return a normalized RelationshipEdge.

    Validation rules:
    - ``edge_type`` must be in the fixed taxonomy
      (reports_to / influences / champion_for / blocks / introduced_by).
    - endpoint types must be person or company.
    - source and target ids are non-empty (<=36 chars).
    - source == target for the same type is rejected (self loop has no
      useful semantics for this vocabulary).
    - confidence must be None or in [0, 1].
    - evidence entries must be dicts.
    """
    tid = _require_uuid(tenant_id, "tenant_id")
    etype = str(edge_type or "").strip()
    if etype not in EDGE_TYPE_SET:
        raise RelationshipError(
            f"invalid edge_type '{etype}'; expected one of {sorted(RELATIONSHIP_EDGE_TYPES)}"
        )

    src_type = str(source_type or "").strip().lower()
    tgt_type = str(target_type or "").strip().lower()
    if src_type not in ENDPOINT_TYPE_SET:
        raise RelationshipError(f"invalid source_type '{src_type}'; expected person|company")
    if tgt_type not in ENDPOINT_TYPE_SET:
        raise RelationshipError(f"invalid target_type '{tgt_type}'; expected person|company")

    src_id = _require_short_id(source_id, "source_id")
    tgt_id = _require_short_id(target_id, "target_id")
    if src_type == tgt_type and src_id == tgt_id:
        raise RelationshipError("self loop rejected: source and target are identical")

    conf: float | None = None
    if confidence is not None:
        conf = float(confidence)
        if conf < 0.0 or conf > 1.0:
            raise RelationshipError("confidence must be within [0, 1]")

    ev: list[dict[str, Any]] = []
    for item in evidence or []:
        if not isinstance(item, dict):
            raise RelationshipError("evidence entries must be objects")
        ev.append(dict(item))

    basis_text = str(basis or "unknown").strip()[:64] or "unknown"

    return RelationshipEdge(
        id=(edge_id or "").strip() or uuid.uuid4().hex[:12],
        tenant_id=tid,
        edge_type=etype,
        source_type=src_type,
        source_id=src_id,
        target_type=tgt_type,
        target_id=tgt_id,
        basis=basis_text,
        evidence=ev,
        confidence=conf,
        observed_at=(observed_at or _now_iso()) if observed_at is not None else None,
        superseded_at=None,
        created_by=str(created_by or "").strip(),
        created_at=_now_iso(),
    )


def is_endpoint_type(value: str) -> bool:
    return str(value or "").strip().lower() in ENDPOINT_TYPE_SET


def known_basis(value: str) -> bool:
    return str(value or "").strip() in KNOWN_BASES