import math
from typing import Dict
from scipy.stats import norm

def calculate_iv_expected_move(spot: float, iv: float, days_to_expiry: float) -> float:
    """
    Expected Move = Spot * IV * sqrt(DTE / 365)
    """
    if days_to_expiry <= 0 or iv <= 0:
        return 0.0
    dte_years = days_to_expiry / 365.0
    expected_move = spot * iv * math.sqrt(dte_years)
    return round(expected_move, 2)

def calculate_atr_expected_move(atr: float, days_to_expiry: float) -> float:
    """
    ATR-based Expected Move over DTE
    """
    if days_to_expiry <= 0 or atr <= 0:
        return 0.0
    return round(atr * math.sqrt(max(1.0, days_to_expiry)), 2)

def calculate_expected_move_bounds(spot: float, iv: float, atr: float, days_to_expiry: float) -> Dict[str, float]:
    iv_move = calculate_iv_expected_move(spot, iv, days_to_expiry)
    atr_move = calculate_atr_expected_move(atr, days_to_expiry)

    # Blended expected move (weighted average)
    blended_move = round((0.7 * iv_move + 0.3 * atr_move) if atr > 0 else iv_move, 2)

    upper_bound = spot + blended_move
    lower_bound = spot - blended_move

    # Probabilities assuming normal distribution
    # Prob of touch boundary ~ 2 * Prob(X > bound) = 2 * (1 - N(1)) ~ 68.2% inside, 31.8% touch
    prob_touch = round(2.0 * (1.0 - norm.cdf(1.0)), 4)
    prob_above = round(1.0 - norm.cdf(1.0), 4)
    prob_below = round(norm.cdf(-1.0), 4)

    return {
        "spot": spot,
        "iv_expected_move": iv_move,
        "atr_expected_move": atr_move,
        "blended_expected_move": blended_move,
        "upper_boundary": upper_bound,
        "lower_boundary": lower_bound,
        "prob_touch_boundary": prob_touch,
        "prob_expiry_above_upper": prob_above,
        "prob_expiry_below_lower": prob_below
    }
