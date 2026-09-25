from datetime import date
from decimal import Decimal

import pytest

from app.modules.gtm.market_methodology import MarketEstimate, validate_market_stack


def _estimate(metric: str, amount: str) -> MarketEstimate:
    return MarketEstimate(metric, Decimal(amount), "SAR", "official-statistics", date(2026, 9, 22), "top-down")


def test_market_stack_requires_provenance_and_monotonicity():
    result = validate_market_stack([_estimate("TAM", "100"), _estimate("SAM", "50"), _estimate("SOM", "10")])
    assert result["valid"] is True
    with pytest.raises(ValueError, match="source"):
        MarketEstimate("TAM", Decimal("1"), "SAR", "", date.today(), "top-down")


def test_market_stack_rejects_inverted_layers():
    result = validate_market_stack([_estimate("TAM", "10"), _estimate("SAM", "50"), _estimate("SOM", "1")])
    assert result["valid"] is False
    assert result["monotonic"] is False
