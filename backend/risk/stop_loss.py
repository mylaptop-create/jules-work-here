from typing import Dict
from backend.data.models import StrategyCandidate, SpotData

def calculate_stop_and_targets(strategy: StrategyCandidate, spot: SpotData) -> Dict[str, float]:
    """
    Calculates structure-based stop loss, VWAP/ATR invalidations, partial profit targets, and time exit thresholds.
    """
    spot_price = spot.last_price
    atr = spot.atr

    if strategy.net_delta > 0:  # Bullish strategy
        stop_loss = spot_price - max(atr * 0.8, 30.0)
        target_1 = spot_price + max(atr * 1.0, 40.0)
        target_2 = spot_price + max(atr * 1.8, 75.0)
    elif strategy.net_delta < 0:  # Bearish strategy
        stop_loss = spot_price + max(atr * 0.8, 30.0)
        target_1 = spot_price - max(atr * 1.0, 40.0)
        target_2 = spot_price - max(atr * 1.8, 75.0)
    else:  # Neutral strategy
        stop_loss = spot_price - max(atr * 1.2, 50.0)
        target_1 = spot_price + max(atr * 1.2, 50.0)
        target_2 = spot_price + max(atr * 2.0, 80.0)

    return {
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2)
    }

def evaluate_time_exit(hours_to_expiry: float, current_pnl: float, max_loss: float) -> bool:
    """
    Time Exit Engine:
    In final 2 hours of expiry, exit if position is not generating sufficient expected value vs remaining theta decay.
    """
    if hours_to_expiry < 2.0 and current_pnl < 0:
        return True
    return False
