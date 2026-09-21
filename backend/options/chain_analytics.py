from typing import Dict, Tuple
from backend.data.models import OptionChain, OptionType, OptionQuote

def calculate_pcr(chain: OptionChain) -> float:
    total_call_oi = sum(q.open_interest for q in chain.calls.values())
    total_put_oi = sum(q.open_interest for q in chain.puts.values())
    if total_call_oi == 0:
        return 1.0
    return round(total_put_oi / total_call_oi, 2)

def calculate_max_pain(chain: OptionChain) -> float:
    """
    Max Pain calculation: Finds strike with minimum total loss for option buyers.
    Note: Used only as secondary metric.
    """
    strikes = sorted(list(set(list(chain.calls.keys()) + list(chain.puts.keys()))))
    if not strikes:
        return chain.spot_price

    min_loss = float('inf')
    max_pain_strike = chain.spot_price

    for expiry_strike in strikes:
        total_loss = 0.0
        # Loss from calls
        for k, q in chain.calls.items():
            if expiry_strike > k:
                total_loss += (expiry_strike - k) * q.open_interest
        # Loss from puts
        for k, q in chain.puts.items():
            if expiry_strike < k:
                total_loss += (k - expiry_strike) * q.open_interest

        if total_loss < min_loss:
            min_loss = total_loss
            max_pain_strike = expiry_strike

    return max_pain_strike

def find_key_oi_levels(chain: OptionChain) -> Tuple[float, float]:
    """
    Finds Call Resistance (max call OI strike) and Put Support (max put OI strike).
    """
    max_call_oi_strike = chain.spot_price
    max_call_oi = -1
    for k, q in chain.calls.items():
        if q.open_interest > max_call_oi:
            max_call_oi = q.open_interest
            max_call_oi_strike = k

    max_put_oi_strike = chain.spot_price
    max_put_oi = -1
    for k, q in chain.puts.items():
        if q.open_interest > max_put_oi:
            max_put_oi = q.open_interest
            max_put_oi_strike = k

    return max_call_oi_strike, max_put_oi_strike

def calculate_iv_skew(chain: OptionChain) -> float:
    """
    Calculates Put IV - Call IV at OTM strikes relative to spot.
    """
    spot = chain.spot_price
    otm_call_strike = min(chain.calls.keys(), key=lambda k: abs(k - (spot * 1.01))) if chain.calls else spot
    otm_put_strike = min(chain.puts.keys(), key=lambda k: abs(k - (spot * 0.99))) if chain.puts else spot

    call_iv = chain.calls[otm_call_strike].iv if otm_call_strike in chain.calls else 0.15
    put_iv = chain.puts[otm_put_strike].iv if otm_put_strike in chain.puts else 0.15

    return round(put_iv - call_iv, 4)
