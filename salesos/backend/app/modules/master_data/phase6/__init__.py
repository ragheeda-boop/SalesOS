"""Phase 6 — Data Improvement/Enrichment platform (SalesOS Master Data)."""

from app.modules.master_data.phase6.classification import (
    IdentityResult,
    IdentityState,
    SalesReadiness,
    classify_corrected,
    evaluate_source_field_agreement,
    is_generic_domain,
    is_real_domain,
)
from app.modules.master_data.phase6.canonical import (
    CanonicalCandidate,
    select_canonical,
    selection_reason_for,
)
from app.modules.master_data.phase6.industry import (
    IndustryResult,
    normalize_industry,
)
from app.modules.master_data.phase6.quality import (
    QualityResult,
    score_quality,
)
from app.modules.master_data.phase6.readiness import (
    ReadinessResult,
    recompute_sales_readiness,
)
from app.modules.master_data.phase6.relationships import (
    RelationshipEvidence,
    infer_relationship,
)

__all__ = [
    "IdentityResult",
    "IdentityState",
    "SalesReadiness",
    "classify_corrected",
    "evaluate_source_field_agreement",
    "is_generic_domain",
    "is_real_domain",
    "CanonicalCandidate",
    "select_canonical",
    "selection_reason_for",
    "IndustryResult",
    "normalize_industry",
    "QualityResult",
    "score_quality",
    "ReadinessResult",
    "recompute_sales_readiness",
    "RelationshipEvidence",
    "infer_relationship",
]
