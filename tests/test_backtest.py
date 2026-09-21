import pytest
from backend.backtesting.engine import BacktestEngine
from backend.backtesting.monte_carlo import run_monte_carlo_simulation
from backend.utils.config import AppConfig

def test_backtest_and_monte_carlo():
    config = AppConfig()
    engine = BacktestEngine(config)

    prices = [22000.0, 22025.0, 21990.0, 22035.0, 22080.0, 22040.0, 22100.0]
    res = engine.run_backtest(prices, None)
    assert res["total_trades"] > 0
    assert "win_rate_percent" in res
    assert "max_drawdown_percent" in res

    mc = run_monte_carlo_simulation([500.0, -300.0, 800.0, -200.0], initial_capital=50000.0, num_simulations=100, num_trades=20)
    assert mc["num_simulations"] == 100
    assert mc["median_max_drawdown_percent"] >= 0.0
    assert 0.0 <= mc["risk_of_ruin_percent"] <= 100.0
