from backend.data.models import SpotData, FuturesData, OptionChain, MarketRegime, RegimeType
from backend.volatility.expected_move import calculate_expected_move_bounds

def classify_market_regime(spot: SpotData, futures: FuturesData, chain: OptionChain) -> MarketRegime:
    """
    Classifies market regime using multi-signal consensus:
    - Spot vs VWAP
    - ADX & RSI
    - VIX level
    - Futures basis & OI
    - Call/Put OI concentration
    """
    price = spot.last_price
    vwap = spot.vwap
    adx = spot.adx
    rsi = spot.rsi
    vix = spot.india_vix
    pcr = chain.pcr

    bounds = calculate_expected_move_bounds(price, vix / 100.0, spot.atr, max(chain.days_to_expiry, 0.1))

    bullish_signals = 0
    bearish_signals = 0
    neutral_signals = 0

    # 1. VWAP check
    if price > vwap * 1.002:
        bullish_signals += 2
    elif price < vwap * 0.998:
        bearish_signals += 2
    else:
        neutral_signals += 2

    # 2. RSI check
    if rsi > 60:
        bullish_signals += 1
    elif rsi < 40:
        bearish_signals += 1
    else:
        neutral_signals += 1

    # 3. PCR check
    if pcr > 1.2:
        bullish_signals += 1
    elif pcr < 0.8:
        bearish_signals += 1
    else:
        neutral_signals += 1

    # 4. Futures basis check
    if futures.basis > 10:
        bullish_signals += 1
    elif futures.basis < -10:
        bearish_signals += 1
    else:
        neutral_signals += 1

    total_score = bullish_signals + bearish_signals + neutral_signals

    # Expiry pinning check
    if chain.days_to_expiry < 0.5 and vix < 12.0 and adx < 20:
        return MarketRegime(
            regime=RegimeType.EXPIRY_PINNING,
            confidence=85.0,
            trend_strength="WEAK",
            volatility_state="LOW_COMPRESSION",
            expected_range_lower=bounds["lower_boundary"],
            expected_range_upper=bounds["upper_boundary"]
        )

    # High volatility breakout
    if vix > 22.0 or (adx > 30 and (bullish_signals >= 4 or bearish_signals >= 4)):
        reg = RegimeType.HIGH_VOL_BREAKOUT
        trend = "STRONG BULLISH" if bullish_signals > bearish_signals else "STRONG BEARISH"
        conf = min(95.0, 50.0 + adx)
        return MarketRegime(
            regime=reg,
            confidence=round(conf, 1),
            trend_strength=trend,
            volatility_state="HIGH_VOLATILITY",
            expected_range_lower=bounds["lower_boundary"],
            expected_range_upper=bounds["upper_boundary"]
        )

    # Trend vs Range bound
    if adx > 25:
        if bullish_signals >= 3 and bullish_signals > bearish_signals:
            reg = RegimeType.STRONG_BULLISH if adx > 35 else RegimeType.WEAK_BULLISH
            conf = min(90.0, 40.0 + bullish_signals * 10)
            trend = "STRONG" if adx > 35 else "WEAK"
            return MarketRegime(
                regime=reg,
                confidence=round(conf, 1),
                trend_strength=trend,
                volatility_state="NORMAL",
                expected_range_lower=bounds["lower_boundary"],
                expected_range_upper=bounds["upper_boundary"]
            )
        elif bearish_signals >= 3 and bearish_signals > bullish_signals:
            reg = RegimeType.STRONG_BEARISH if adx > 35 else RegimeType.WEAK_BEARISH
            conf = min(90.0, 40.0 + bearish_signals * 10)
            trend = "STRONG" if adx > 35 else "WEAK"
            return MarketRegime(
                regime=reg,
                confidence=round(conf, 1),
                trend_strength=trend,
                volatility_state="NORMAL",
                expected_range_lower=bounds["lower_boundary"],
                expected_range_upper=bounds["upper_boundary"]
            )

    # Low Volatility Compression / Range-bound
    if vix < 13.0 and adx < 20:
        return MarketRegime(
            regime=RegimeType.LOW_VOL_COMPRESSION,
            confidence=75.0,
            trend_strength="NEUTRAL",
            volatility_state="LOW_COMPRESSION",
            expected_range_lower=bounds["lower_boundary"],
            expected_range_upper=bounds["upper_boundary"]
        )

    return MarketRegime(
        regime=RegimeType.RANGE_BOUND,
        confidence=65.0,
        trend_strength="NEUTRAL",
        volatility_state="NORMAL",
        expected_range_lower=bounds["lower_boundary"],
        expected_range_upper=bounds["upper_boundary"]
    )
