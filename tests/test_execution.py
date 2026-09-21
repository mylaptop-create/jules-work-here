import pytest
from backend.execution.paper_trading import PaperTradingBroker
from backend.execution.safety import ExecutionSafetyEngine
from backend.data.models import StrategyCandidate, OptionLeg, OptionType, ActionType
from backend.utils.config import AppConfig

def test_execution_modules():
    config = AppConfig()
    broker = PaperTradingBroker(config)
    safety = ExecutionSafetyEngine()

    spot = broker.get_spot_data()
    assert spot.last_price == 22000.0

    valid, err = safety.validate_data_freshness(spot)
    assert valid is True
    assert err is None

    leg = OptionLeg(option_type=OptionType.CALL, strike=22000.0, action=ActionType.BUY, expiry="2025-03-04", quantity=25, entry_price=100.0)
    strategy = StrategyCandidate(
        name="ATM Long Call", legs=[leg], required_capital=2500.0, max_loss=500.0, max_profit=2000.0,
        breakeven=[22100.0], probability_of_profit=0.55, expected_value=600.0, risk_reward_ratio=4.0,
        net_delta=12.5, net_gamma=0.01, net_theta=-10.0, net_vega=5.0, estimated_fees=40.0, estimated_slippage=25.0, quality_score=80.0
    )

    res = broker.execute_strategy(strategy, lots=1)
    assert res["status"] == "FILLED_PAPER"
    assert len(res["executed_legs"]) == 1

    # Test kill switch
    safety.activate_kill_switch("Emergency test")
    valid, err = safety.validate_data_freshness(spot)
    assert valid is False
    assert "Kill switch" in err
