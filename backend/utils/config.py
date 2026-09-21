import os
import yaml
from pydantic import BaseModel, Field
from typing import Optional

class CapitalConfig(BaseModel):
    account_capital: float = 50000.0
    max_risk_per_trade_percent: float = 1.5
    max_daily_loss_percent: float = 3.0
    max_weekly_loss_percent: float = 6.0
    max_open_positions: int = 2
    capital_mode: str = "MODE_B"

class StrategyConfig(BaseModel):
    min_signal_score: float = 70.0
    min_risk_reward: float = 1.5
    min_expected_value: float = 100.0
    min_probability_of_profit: float = 0.50
    max_bid_ask_spread_percent: float = 3.0
    max_slippage_points: float = 5.0
    cheap_option_min_quality_score: float = 60.0

class LotSizeConfig(BaseModel):
    nifty: int = 25

class CostConfig(BaseModel):
    brokerage_per_order: float = 20.0
    stt_sell_percent: float = 0.0625
    exchange_charges_percent: float = 0.053
    gst_percent: float = 18.0
    sebi_charges_percent: float = 0.0001
    stamp_duty_buy_percent: float = 0.003

class AppConfig(BaseModel):
    name: str = "NIFTY 50 Tuesday Expiry Options Bot"
    version: str = "1.0.0"
    environment: str = "paper_trading"
    capital: CapitalConfig = Field(default_factory=CapitalConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    lot_size: LotSizeConfig = Field(default_factory=LotSizeConfig)
    transaction_costs: CostConfig = Field(default_factory=CostConfig)

def load_config(config_path: Optional[str] = None) -> AppConfig:
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "../../configs/default_config.yaml")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
            return AppConfig(**data)
    return AppConfig()
