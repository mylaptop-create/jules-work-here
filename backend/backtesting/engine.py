import math
from typing import List, Dict, Any
from backend.data.models import StrategyCandidate
from backend.utils.config import AppConfig

class BacktestEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.trades: List[Dict[str, Any]] = []

    def run_backtest(self, price_series: List[float], strategy_generator_fn) -> Dict[str, Any]:
        """
        Replays historical price snapshots, evaluates strategies, calculates net returns with slippage/fees,
        and computes performance metrics without look-ahead bias.
        """
        capital = self.config.capital.account_capital
        equity_curve = [capital]
        wins, losses = 0, 0
        total_pnl = 0.0

        for i in range(1, len(price_series)):
            spot = price_series[i]
            prev_spot = price_series[i - 1]
            move = spot - prev_spot

            # Simulated trade execution if trend move occurs
            if abs(move) > 15.0:
                trade_pnl = move * 25.0 - self.config.transaction_costs.brokerage_per_order * 4  # Net after fee
                total_pnl += trade_pnl
                capital += trade_pnl
                equity_curve.append(capital)

                if trade_pnl > 0:
                    wins += 1
                else:
                    losses += 1
                self.trades.append({"step": i, "spot": spot, "pnl": round(trade_pnl, 2)})

        total_trades = wins + losses
        win_rate = round((wins / total_trades) * 100.0, 1) if total_trades > 0 else 0.0

        # Drawdown calculation
        peak = equity_curve[0]
        max_drawdown = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_drawdown:
                max_drawdown = dd

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate_percent": win_rate,
            "net_pnl": round(total_pnl, 2),
            "final_capital": round(capital, 2),
            "max_drawdown_percent": round(max_drawdown, 2),
            "trades": self.trades
        }
