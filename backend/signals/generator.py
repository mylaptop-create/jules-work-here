from typing import Dict, List, Tuple
from backend.data.models import SpotData, FuturesData, OptionChain, MarketRegime, ActionType, TradeSignal
from backend.utils.config import AppConfig

def calculate_signal_scores(spot: SpotData, futures: FuturesData, chain: OptionChain, regime: MarketRegime) -> Dict[str, float]:
    scores = {}

    # Trend Score (0-100)
    if spot.last_price > spot.vwap:
        scores["TREND_SCORE"] = min(100.0, 50.0 + (spot.last_price - spot.vwap) / spot.atr * 25.0)
    else:
        scores["TREND_SCORE"] = max(0.0, 50.0 - (spot.vwap - spot.last_price) / spot.atr * 25.0)

    # Momentum Score (0-100 based on RSI & ADX)
    scores["MOMENTUM_SCORE"] = min(100.0, max(0.0, spot.rsi * 0.7 + spot.adx * 0.3))

    # Options Flow & OI Score
    pcr_score = min(100.0, chain.pcr * 50.0)
    scores["OI_STRUCTURE_SCORE"] = pcr_score
    scores["OPTIONS_FLOW_SCORE"] = pcr_score

    # Volatility Score
    scores["VOLATILITY_SCORE"] = max(0.0, min(100.0, 100.0 - (spot.india_vix - 10.0) * 4.0))

    # Liquidity Score
    scores["LIQUIDITY_SCORE"] = 85.0
    scores["EXPIRY_SCORE"] = 80.0 if chain.days_to_expiry >= 0.5 else 50.0
    scores["RISK_REWARD_SCORE"] = 75.0

    return scores

def generate_trade_signal_action(scores: Dict[str, float], regime: MarketRegime, config: AppConfig) -> Tuple[ActionType, str, float]:
    trend = scores["TREND_SCORE"]
    mom = scores["MOMENTUM_SCORE"]
    oi = scores["OI_STRUCTURE_SCORE"]

    overall_score = round((trend * 0.3 + mom * 0.2 + oi * 0.2 + scores["LIQUIDITY_SCORE"] * 0.15 + scores["EXPIRY_SCORE"] * 0.15), 1)

    if overall_score < config.strategy.min_signal_score or regime.confidence < 60.0:
        return ActionType.NO_TRADE, "NEUTRAL", overall_score

    if trend > 65.0 and mom > 55.0 and oi > 50.0:
        return ActionType.BUY, "BULLISH", overall_score
    elif trend < 35.0 and mom < 45.0 and oi < 50.0:
        return ActionType.BUY, "BEARISH", overall_score
    else:
        return ActionType.NO_TRADE, "NEUTRAL", overall_score
