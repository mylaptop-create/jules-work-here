import pytest
from datetime import datetime
from backend.data.models import SpotData, FuturesData, OptionChain, OptionQuote, OptionType, RegimeType
from backend.regime.classifier import classify_market_regime

def test_regime_classification():
    spot = SpotData(
        last_price=22050.0,
        open=21950.0,
        high=22100.0,
        low=21900.0,
        previous_close=21950.0,
        vwap=21980.0,
        atr=110.0,
        rsi=65.0,
        adx=32.0,
        india_vix=14.5
    )

    futures = FuturesData(
        last_price=22070.0,
        volume=50000,
        open_interest=1000000,
        basis=20.0
    )

    chain = OptionChain(
        spot_price=22050.0,
        expiry_date="2025-03-04",
        days_to_expiry=1.5,
        time_to_expiry_hours=36.0,
        pcr=1.3
    )

    regime = classify_market_regime(spot, futures, chain)
    assert regime.regime in [RegimeType.STRONG_BULLISH, RegimeType.WEAK_BULLISH, RegimeType.HIGH_VOL_BREAKOUT]
    assert regime.confidence > 50.0
    assert regime.expected_range_upper > 22050.0
    assert regime.expected_range_lower < 22050.0
