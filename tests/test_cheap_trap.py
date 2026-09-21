import pytest
from backend.data.models import OptionQuote, OptionType, GreeksData
from backend.options.cheap_trap import evaluate_option_quality
from backend.utils.config import AppConfig

def test_cheap_option_trap_detector():
    config = AppConfig()
    spot = 22000.0

    # High quality ATM Call
    good_quote = OptionQuote(
        strike=22000.0,
        option_type=OptionType.CALL,
        expiry="2025-03-04",
        ltp=120.0,
        bid=119.0,
        ask=121.0,
        bid_qty=1000,
        ask_qty=1000,
        volume=50000,
        open_interest=100000,
        change_in_oi=2000,
        iv=0.15,
        greeks=GreeksData(delta=0.50, gamma=0.001, theta=-15.0, vega=10.0, implied_volatility=0.15)
    )
    score_good = evaluate_option_quality(good_quote, spot, config)
    assert score_good >= 70.0

    # Cheap Trap Deep OTM Call
    trap_quote = OptionQuote(
        strike=22800.0,
        option_type=OptionType.CALL,
        expiry="2025-03-04",
        ltp=8.0,
        bid=7.0,
        ask=9.0,
        bid_qty=50,
        ask_qty=50,
        volume=200,
        open_interest=5000,
        change_in_oi=100,
        iv=0.25,
        greeks=GreeksData(delta=0.05, gamma=0.0001, theta=-5.0, vega=2.0, implied_volatility=0.25)
    )
    score_trap = evaluate_option_quality(trap_quote, spot, config)
    assert score_trap < 50.0
    assert "Cheap option trap" in trap_quote.quality_reason or "Low delta" in trap_quote.quality_reason
