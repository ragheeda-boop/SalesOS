"""GTM Intelligence — CAP-095 ICP + CAP-096 Market Sizing + CAP-097 Lead Discovery.

Not Production GO.
"""

from app.modules.gtm.icp import ICPError, ICPProfile
from app.modules.gtm.lead_discovery import (
    DiscoveredLead,
    LeadDiscoveryError,
    LeadDiscoveryQuery,
    LeadDiscoveryRun,
)
from app.modules.gtm.market_sizing import (
    GOVERNMENT_DATASET_SCALE_HINT,
    MarketSizingCriteria,
    MarketSizingError,
    MarketSizingSnapshot,
)
from app.modules.gtm.market_sizing_engine import (
    compute_tam_sam_som,
)

__all__ = [
    "GOVERNMENT_DATASET_SCALE_HINT",
    "DiscoveredLead",
    "ICPError",
    "ICPProfile",
    "LeadDiscoveryError",
    "LeadDiscoveryQuery",
    "LeadDiscoveryRun",
    "MarketSizingCriteria",
    "MarketSizingError",
    "MarketSizingSnapshot",
    "compute_tam_sam_som",
]
