import numpy as np
from typing import List, Dict, Any

def run_monte_carlo_simulation(trade_pnls: List[float], initial_capital: float = 50000.0, num_simulations: int = 500, num_trades: int = 50) -> Dict[str, Any]:
    """
    Runs Monte Carlo simulation on historical trade PnLs to estimate drawdown distributions and risk of ruin.
    """
    if not trade_pnls:
        # Default distribution for synthetic testing
        trade_pnls = [500.0, -300.0, 700.0, -400.0, 300.0, -250.0]

    np.random.seed(42)
    pnls_array = np.array(trade_pnls)
    drawdowns = []
    ruin_count = 0

    for _ in range(num_simulations):
        sampled_pnls = np.random.choice(pnls_array, size=num_trades, replace=True)
        equity_curve = initial_capital + np.cumsum(sampled_pnls)

        # Check risk of ruin (losing > 30% of capital)
        if np.min(equity_curve) < initial_capital * 0.70:
            ruin_count += 1

        peak = np.maximum.accumulate(equity_curve)
        dd = (peak - equity_curve) / peak * 100.0
        drawdowns.append(np.max(dd))

    return {
        "num_simulations": num_simulations,
        "median_max_drawdown_percent": round(float(np.median(drawdowns)), 2),
        "percentile_95_max_drawdown_percent": round(float(np.percentile(drawdowns, 95)), 2),
        "risk_of_ruin_percent": round((ruin_count / num_simulations) * 100.0, 2)
    }
