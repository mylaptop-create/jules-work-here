from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class OptionType(str, Enum):
    CALL = "CE"
    PUT = "PE"

class CapitalMode(str, Enum):
    MODE_A = "MODE_A"  # Very Low Capital
    MODE_B = "MODE_B"  # Low Capital
    MODE_C = "MODE_C"  # Medium Capital
    MODE_D = "MODE_D"  # Advanced Capital

class RegimeType(str, Enum):
    STRONG_BULLISH = "Strong Bullish Trend"
    WEAK_BULLISH = "Weak Bullish Trend"
    STRONG_BEARISH = "Strong Bearish Trend"
    WEAK_BEARISH = "Weak Bearish Trend"
    RANGE_BOUND = "Range-bound"
    HIGH_VOL_BREAKOUT = "High-volatility Breakout"
    LOW_VOL_COMPRESSION = "Low-volatility Compression"
    FAILED_BREAKOUT = "Failed Breakout"
    EXPIRY_PINNING = "Expiry Pinning / Compression"
    UNCLEAR = "Unclear / Abnormal Conditions"

class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    NO_TRADE = "NO TRADE"

class SpotData(BaseModel):
    symbol: str = "NIFTY"
    timestamp: datetime = Field(default_factory=datetime.now)
    last_price: float
    open: float
    high: float
    low: float
    previous_close: float
    vwap: float
    atr: float
    rsi: float
    adx: float
    india_vix: float

class FuturesData(BaseModel):
    symbol: str = "NIFTY_FUT"
    timestamp: datetime = Field(default_factory=datetime.now)
    last_price: float
    volume: int
    open_interest: int
    basis: float  # Futures - Spot

class GreeksData(BaseModel):
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    implied_volatility: float = 0.0

class OptionQuote(BaseModel):
    strike: float
    option_type: OptionType
    expiry: str
    ltp: float
    bid: float
    ask: float
    bid_qty: int
    ask_qty: int
    volume: int
    open_interest: int
    change_in_oi: int
    iv: float
    greeks: GreeksData = Field(default_factory=GreeksData)
    intrinsic_value: float = 0.0
    extrinsic_value: float = 0.0
    quality_score: float = 0.0
    quality_reason: Optional[str] = None

class OptionChain(BaseModel):
    symbol: str = "NIFTY"
    spot_price: float
    expiry_date: str
    days_to_expiry: float
    time_to_expiry_hours: float
    pcr: float = 1.0
    max_pain: float = 0.0
    iv_skew: float = 0.0
    call_oi_concentration: float = 0.0
    put_oi_concentration: float = 0.0
    calls: Dict[float, OptionQuote] = Field(default_factory=dict)
    puts: Dict[float, OptionQuote] = Field(default_factory=dict)

class MarketRegime(BaseModel):
    regime: RegimeType = RegimeType.UNCLEAR
    confidence: float = 0.0  # 0 to 100
    trend_strength: str = "NEUTRAL"
    volatility_state: str = "NORMAL"
    expected_range_lower: float
    expected_range_upper: float

class OptionLeg(BaseModel):
    option_type: OptionType
    strike: float
    action: ActionType  # BUY or SELL
    expiry: str
    quantity: int
    entry_price: float
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

class StrategyCandidate(BaseModel):
    name: str
    legs: List[OptionLeg]
    required_capital: float
    max_loss: float
    max_profit: float
    breakeven: List[float]
    probability_of_profit: float
    expected_value: float
    risk_reward_ratio: float
    net_delta: float
    net_gamma: float
    net_theta: float
    net_vega: float
    estimated_fees: float
    estimated_slippage: float
    quality_score: float = 0.0
    rejection_reason: Optional[str] = None

class TradeSignal(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    action: ActionType
    market_regime: MarketRegime
    direction: str
    recommended_strategy: Optional[StrategyCandidate] = None
    underlying_price: float
    expiry: str
    time_remaining: str
    entry_zone: str = "N/A"
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    max_loss: float = 0.0
    max_profit: float = 0.0
    breakeven: str = "N/A"
    probability_of_profit: float = 0.0
    expected_value: float = 0.0
    risk_reward_ratio: float = 0.0
    signal_quality_score: float = 0.0
    reasons_for_trade: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    recommended_lots: int = 0
    risk_amount: float = 0.0
    risk_percent_of_account: float = 0.0
