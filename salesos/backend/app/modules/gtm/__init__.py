"""GTM Intelligence — CAP-095..101 + CAP-104. Not Production GO."""

from app.modules.gtm.enrichment import EnrichmentError, EnrichmentResult
from app.modules.gtm.icp import ICPError, ICPProfile
from app.modules.gtm.lead_discovery import (
    DiscoveredLead,
    LeadDiscoveryError,
    LeadDiscoveryQuery,
    LeadDiscoveryRun,
)
from app.modules.gtm.lookalike import LookalikeError, LookalikeModel
from app.modules.gtm.market_sizing import (
    GOVERNMENT_DATASET_SCALE_HINT,
    MarketSizingCriteria,
    MarketSizingError,
    MarketSizingSnapshot,
)
from app.modules.gtm.market_sizing_engine import (
    compute_tam_sam_som,
)
from app.modules.gtm.sequencing import SequenceDefinition, SequencingError
from app.modules.gtm.verification import VerificationError, VerificationResult
from app.modules.gtm.website_intelligence import (
    WebsiteIntelligenceError,
    WebsiteIntelligenceSnapshot,
)

__all__ = [
    "GOVERNMENT_DATASET_SCALE_HINT",
    "DiscoveredLead",
    "EnrichmentError",
    "EnrichmentResult",
    "ICPError",
    "ICPProfile",
    "LeadDiscoveryError",
    "LeadDiscoveryQuery",
    "LeadDiscoveryRun",
    "LookalikeError",
    "LookalikeModel",
    "MarketSizingCriteria",
    "MarketSizingError",
    "MarketSizingSnapshot",
    "SequenceDefinition",
    "SequencingError",
    "VerificationError",
    "VerificationResult",
    "WebsiteIntelligenceError",
    "WebsiteIntelligenceSnapshot",
    "compute_tam_sam_som",
]
