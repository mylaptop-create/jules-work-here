import pytest
from backend.data.models import OptionChain, OptionQuote, OptionType, GreeksData
from backend.strategies.strategy_engine import generate_candidate_strategies
from backend.utils.config import AppConfig

def test_strategy_engine():
    config = AppConfig()
    chain = OptionChain(
        spot_price=22000.0,
        expiry_date="2025-03-04",
        days_to_expiry=2.0,
        time_to_expiry_hours=48.0,
        calls={
            22000.0: OptionQuote(strike=22000.0, option_type=OptionType.CALL, expiry="2025-03-04", ltp=100.0, bid=99.0, ask=101.0, bid_qty=500, ask_qty=500, volume=10000, open_interest=50000, change_in_oi=1000, iv=0.15, greeks=GreeksData(delta=0.50, gamma=0.001, theta=-10.0, vega=5.0, implied_volatility=0.15)),
            22100.0: OptionQuote(strike=22100.0, option_type=OptionType.CALL, expiry="2025-03-04", ltp=50.0, bid=49.0, ask=51.0, bid_qty=500, ask_qty=500, volume=8000, open_interest=40000, change_in_oi=800, iv=0.15, greeks=GreeksData(delta=0.35, gamma=0.0008, theta=-8.0, vega=4.0, implied_volatility=0.15))
        },
        puts={
            22000.0: OptionQuote(strike=22000.0, option_type=OptionType.PUT, expiry="2025-03-04", ltp=90.0, bid=89.0, ask=91.0, bid_qty=500, ask_qty=500, volume=12000, open_interest=80000, change_in_oi=2000, iv=0.16, greeks=GreeksData(delta=-0.48, gamma=0.001, theta=-9.0, vega=5.0, implied_volatility=0.16)),
            21900.0: OptionQuote(strike=21900.0, option_type=OptionType.PUT, expiry="2025-03-04", ltp=45.0, bid=44.0, ask=46.0, bid_qty=500, ask_qty=500, volume=10000, open_interest=60000, change_in_oi=1500, iv=0.16, greeks=GreeksData(delta=-0.32, gamma=0.0008, theta=-7.0, vega=4.0, implied_volatility=0.16))
        }
    )

    candidates = generate_candidate_strategies(chain, capital=50000.0, config=config)
    assert len(candidates) > 0
    names = [c.name for c in candidates]
    assert "ATM Long Call" in names or "Bull Call Spread" in names

    for c in candidates:
        assert c.required_capital <= 50000.0
        assert c.max_loss > 0
        assert len(c.legs) >= 1
