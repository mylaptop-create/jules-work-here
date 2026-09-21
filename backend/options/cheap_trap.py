from backend.data.models import OptionQuote, OptionType
from backend.utils.config import AppConfig

def evaluate_option_quality(quote: OptionQuote, spot_price: float, config: AppConfig) -> float:
    """
    Cheap Option Trap Detector.
    Calculates Option Quality Score (0 - 100) and flags bad cheap options.
    Rejects deep OTM, ultra-low delta, illiquid, wide spread, or high theta decay options.
    """
    bid_ask_spread = quote.ask - quote.bid
    mid_price = (quote.bid + quote.ask) / 2.0 if (quote.bid + quote.ask) > 0 else quote.ltp

    if mid_price <= 0:
        quote.quality_score = 0.0
        quote.quality_reason = "Zero or negative premium"
        return 0.0

    spread_percent = (bid_ask_spread / mid_price) * 100.0 if mid_price > 0 else 100.0
    distance_pct = abs(quote.strike - spot_price) / spot_price * 100.0
    delta = abs(quote.greeks.delta)

    score = 100.0
    reasons = []

    # 1. Spread penalty
    if spread_percent > config.strategy.max_bid_ask_spread_percent:
        penalty = min(40.0, (spread_percent - config.strategy.max_bid_ask_spread_percent) * 5)
        score -= penalty
        reasons.append(f"Wide bid/ask spread ({round(spread_percent,1)}%)")

    # 2. Delta suitability penalty
    if delta < 0.15:
        score -= 40.0
        reasons.append(f"Ultra-low delta ({round(delta,2)}) - low probability of finishing ITM")
    elif delta < 0.30:
        score -= 20.0
        reasons.append(f"Low delta ({round(delta,2)})")

    # 3. Liquidity penalty (volume & bid/ask quantity)
    if quote.volume < 1000 or (quote.bid_qty + quote.ask_qty) < 200:
        score -= 30.0
        reasons.append("Insufficient liquidity/volume")

    # 4. Deep OTM distance penalty
    if distance_pct > 2.5:
        score -= 30.0
        reasons.append(f"Deep OTM ({round(distance_pct, 1)}% from spot)")

    # 5. Low premium "cheap option trap" penalty
    if mid_price < 15.0 and delta < 0.20:
        score -= 40.0
        reasons.append(f"Cheap option trap: ₹{mid_price} premium with low delta {round(delta,2)}")

    score = max(0.0, min(100.0, score))
    quote.quality_score = round(score, 1)
    quote.quality_reason = "; ".join(reasons) if reasons else "High quality option"

    return quote.quality_score
