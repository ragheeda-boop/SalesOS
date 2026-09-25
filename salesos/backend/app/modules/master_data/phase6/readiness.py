"""Phase 6 — Sales-readiness recalculation (corrected, versioned).

DI sales-ready definitions (RECALCULATION_SPEC / BUCKET_RECONCILIATION):

  SALES_READY          = identity in (GOVERNMENT_ANCHORED, STRONG_MULTI_SOURCE)
                         AND (has_email OR has_phone)
  SALES_READY_WITH_REVIEW = identity in (GOVERNMENT_ANCHORED, STRONG_MULTI_SOURCE,
                         DETERMINISTIC_SINGLE_SOURCE) AND (has_email OR has_phone
                         OR has_domain), not already SALES_READY.
  ENRICHMENT_REQUIRED  = has real identity but no contact channel.
  IDENTITY_REVIEW_REQUIRED = identity state requires human review (P0/field-conflict).
  INSUFFICIENT_DATA    = no verifiable identity (NO_VERIFIABLE_IDENTITY).

Deterministic. The pipeline persists each recomputation as a VERSIONED row in
md_sales_readiness_history (never silently overwriting the previous).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.master_data.phase6.classification import IdentityState, SalesReadiness


@dataclass
class ReadinessResult:
    sales_readiness: SalesReadiness
    identity_state: IdentityState
    basis: dict = field(default_factory=dict)


def recompute_sales_readiness(
    *,
    identity_state: IdentityState | str,
    has_contactable_email: bool,
    has_phone: bool,
    has_real_domain: bool,
) -> ReadinessResult:
    """Recompute sales readiness from a corrected identity state + channels."""
    state = identity_state if isinstance(identity_state, IdentityState) else IdentityState(identity_state)
    has_channel = has_contactable_email or has_phone

    if state == IdentityState.CONFLICTING_IDENTITY:
        readiness = SalesReadiness.IDENTITY_REVIEW_REQUIRED
    elif state == IdentityState.NO_VERIFIABLE_IDENTITY:
        readiness = SalesReadiness.INSUFFICIENT_DATA
    elif state in (IdentityState.GOVERNMENT_ANCHORED, IdentityState.STRONG_MULTI_SOURCE):
        readiness = SalesReadiness.SALES_READY if has_channel else SalesReadiness.ENRICHMENT_REQUIRED
    elif state == IdentityState.DETERMINISTIC_SINGLE_SOURCE:
        if has_channel or has_real_domain:
            readiness = SalesReadiness.SALES_READY_WITH_REVIEW if has_channel else SalesReadiness.ENRICHMENT_REQUIRED
        else:
            readiness = SalesReadiness.ENRICHMENT_REQUIRED
    elif state == IdentityState.REVIEW_REQUIRED:
        readiness = SalesReadiness.ENRICHMENT_REQUIRED
    else:  # WEAK_IDENTITY
        readiness = SalesReadiness.ENRICHMENT_REQUIRED

    basis = {
        "identity_state": state.value,
        "has_contactable_email": has_contactable_email,
        "has_phone": has_phone,
        "has_real_domain": has_real_domain,
    }
    return ReadinessResult(readiness, state, basis)
