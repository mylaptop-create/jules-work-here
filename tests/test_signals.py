import pytest
from backend.data.models import SpotData, FuturesData, OptionChain, MarketRegime, RegimeType, StrategyCandidate, OptionLeg, OptionType, ActionType
from backend.signals.generator import calculate_signal_scores, generate_trade_signal_action
from backend.strategies.ranking import rank_and_select_strategy
from backend.utils.config import AppConfig

def test_signals_and_ranking():
    config = AppConfig()
    spot = SpotData(last_price=22050.0, open=21950.0, high=22100.0, low=21900.0, previous_close=21950.0, vwap=21980.0, atr=110.0, rsi=65.0, adx=32.0, india_vix=14.5)
    futures = FuturesData(last_price=22070.0, volume=50000, open_interest=1000000, basis=20.0)
    chain = OptionChain(spot_price=22050.0, expiry_date="2025-03-04", days_to_expiry=1.5, time_to_expiry_hours=36.0, pcr=1.3)
    regime = MarketRegime(regime=RegimeType.STRONG_BULLISH, confidence=80.0, trend_strength="STRONG", volatility_state="NORMAL", expected_range_lower=21900.0, expected_range_upper=22200.0)

    scores = calculate_signal_scores(spot, futures, chain, regime)
    assert scores["TREND_SCORE"] > 50.0

    action, direction, score = generate_trade_signal_action(scores, regime, config)
    assert action in [ActionType.BUY, ActionType.NO_TRADE]

    leg1 = OptionLeg(option_type=OptionType.CALL, strike=22000.0, action=ActionType.BUY, expiry="2025-03-04", quantity=25, entry_price=100.0)
    leg2 = OptionLeg(option_type=OptionType.CALL, strike=22100.0, action=ActionType.SELL, expiry="2025-03-04", quantity=25, entry_price=50.0)

    candidate = StrategyCandidate(
        name="Bull Call Spread",
        legs=[leg1, leg2],
        required_capital=1250.0,
        max_loss=500.0,
        max_profit=2000.0,
        breakeven=[22050.0],
        probability_of_profit=0.60,
        expected_value=1000.0,
        risk_reward_ratio=4.0,
        net_delta=10.0, net_gamma=0.01, net_theta=-5.0, net_vega=2.0,
        estimated_fees=80.0, estimated_slippage=50.0, quality_score=85.0
    )

    best = rank_and_select_strategy([candidate], config)
    assert best is not None
    assert best.name == "Bull Call Spread"
