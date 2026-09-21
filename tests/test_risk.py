import pytest
from backend.data.models import SpotData, StrategyCandidate, OptionLeg, OptionType, ActionType
from backend.risk.stop_loss import calculate_stop_and_targets, evaluate_time_exit
from backend.risk.risk_engine import RiskManager
from backend.utils.config import AppConfig

def test_risk_and_stop_loss():
    config = AppConfig()
    spot = SpotData(last_price=22000.0, open=21950.0, high=22050.0, low=21900.0, previous_close=21950.0, vwap=21980.0, atr=100.0, rsi=60.0, adx=30.0, india_vix=14.0)

    leg = OptionLeg(option_type=OptionType.CALL, strike=22000.0, action=ActionType.BUY, expiry="2025-03-04", quantity=25, entry_price=100.0)
    strategy = StrategyCandidate(
        name="ATM Long Call",
        legs=[leg],
        required_capital=2500.0,
        max_loss=500.0,
        max_profit=2000.0,
        breakeven=[22100.0],
        probability_of_profit=0.55,
        expected_value=600.0,
        risk_reward_ratio=4.0,
        net_delta=12.5, net_gamma=0.01, net_theta=-10.0, net_vega=5.0,
        estimated_fees=40.0, estimated_slippage=25.0, quality_score=80.0
    )

    exits = calculate_stop_and_targets(strategy, spot)
    assert exits["stop_loss"] < 22000.0
    assert exits["target_1"] > 22000.0

    rm = RiskManager(config)
    lots, risk, msg = rm.calculate_position_size(strategy)
    assert lots >= 1
    assert risk <= config.capital.account_capital * (config.capital.max_risk_per_trade_percent / 100.0)

    # Test circuit breaker on daily loss
    rm.update_daily_pnl(-2000.0)
    assert rm.trading_halted is True
    lots, risk, msg = rm.calculate_position_size(strategy)
    assert lots == 0
