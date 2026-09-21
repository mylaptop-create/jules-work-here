from typing import Tuple
from backend.data.models import StrategyCandidate
from backend.utils.config import AppConfig

class RiskManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.daily_pnl = 0.0
        self.open_positions_count = 0
        self.trading_halted = False

    def update_daily_pnl(self, pnl: float):
        self.daily_pnl += pnl
        max_daily_loss = self.config.capital.account_capital * (self.config.capital.max_daily_loss_percent / 100.0)
        if self.daily_pnl <= -max_daily_loss:
            self.trading_halted = True

    def calculate_position_size(self, strategy: StrategyCandidate) -> Tuple[int, float, str]:
        """
        Calculates position size in lots based on strict account risk limits.
        Enforces NO Martingale, NO revenge trading, NO averaging down.
        """
        if self.trading_halted:
            return 0, 0.0, "Trading halted due to daily loss limit hit"

        if self.open_positions_count >= self.config.capital.max_open_positions:
            return 0, 0.0, "Maximum open positions limit reached"

        max_risk_allowed = self.config.capital.account_capital * (self.config.capital.max_risk_per_trade_percent / 100.0)

        if strategy.max_loss <= 0:
            return 0, 0.0, "Invalid max loss"

        # Lot size calculation
        lots = int(max_risk_allowed // strategy.max_loss)
        if lots < 1:
            return 0, 0.0, f"Max risk per trade (₹{max_risk_allowed}) is smaller than single lot max loss (₹{strategy.max_loss})"

        total_required_capital = strategy.required_capital * lots
        if total_required_capital > self.config.capital.account_capital:
            lots = int(self.config.capital.account_capital // strategy.required_capital)

        actual_risk = strategy.max_loss * lots
        risk_percent = (actual_risk / self.config.capital.account_capital) * 100.0

        return max(1, lots), round(actual_risk, 2), f"Approved {lots} lot(s) risking ₹{actual_risk} ({round(risk_percent, 2)}% of capital)"
