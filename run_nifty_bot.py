#!/usr/bin/env python3
"""
NIFTY 50 Tuesday Expiry Options Analysis & Decision Support System
Zero External Dependencies (Pure Python Standard Library)
"""

import sys
import math
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any

# Pure math normal distribution functions using math.erf
def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

# Pure Black-Scholes & Greeks
def black_scholes(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    if T <= 0:
        return max(0.0, S - K) if option_type == "CE" else max(0.0, K - S)
    if sigma <= 0.0001:
        sigma = 0.0001
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == "CE":
        return max(0.0, S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2))
    else:
        return max(0.0, K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1))

def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict[str, float]:
    if T <= 0.0001 or sigma <= 0.0001:
        d = 1.0 if (option_type == "CE" and S > K) or (option_type == "PE" and S < K) else 0.0
        return {"delta": d, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "iv": sigma}

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    delta = norm_cdf(d1) if option_type == "CE" else norm_cdf(d1) - 1.0
    gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))

    term1 = -(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T))
    term2 = r * K * math.exp(-r * T) * norm_cdf(d2 if option_type == "CE" else -d2)
    theta = (term1 - term2 if option_type == "CE" else term1 + term2) / 365.0
    vega = (S * math.sqrt(T) * norm_pdf(d1)) / 100.0

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 4),
        "vega": round(vega, 4),
        "iv": round(sigma, 4)
    }

def solve_iv(price: float, S: float, K: float, T: float, r: float, option_type: str) -> float:
    low, high = 0.001, 3.0
    for _ in range(25):
        mid = (low + high) / 2.0
        p = black_scholes(S, K, T, r, mid, option_type)
        if abs(p - price) < 1e-3:
            return round(mid, 4)
        if p > price:
            high = mid
        else:
            low = mid
    return round((low + high) / 2.0, 4)

# Data Structures
@dataclass
class OptionQuote:
    strike: float
    option_type: str  # CE or PE
    ltp: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    iv: float
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    quality_score: float = 0.0
    quality_reason: str = ""

@dataclass
class MarketSnapshot:
    spot_price: float
    vwap: float
    atr: float
    rsi: float
    adx: float
    vix: float
    pcr: float
    days_to_expiry: float
    calls: Dict[float, OptionQuote]
    puts: Dict[float, OptionQuote]

def evaluate_cheap_option_trap(q: OptionQuote, spot: float) -> float:
    bid_ask_spread = q.ask - q.bid
    mid = (q.bid + q.ask) / 2.0 if (q.bid + q.ask) > 0 else q.ltp
    if mid <= 0:
        q.quality_score = 0.0
        q.quality_reason = "Zero premium"
        return 0.0

    spread_pct = (bid_ask_spread / mid) * 100.0 if mid > 0 else 100.0
    delta = abs(q.delta)
    score = 100.0
    reasons = []

    if spread_pct > 3.0:
        score -= min(40.0, (spread_pct - 3.0) * 5)
        reasons.append(f"Wide spread ({round(spread_pct, 1)}%)")
    if delta < 0.15:
        score -= 40.0
        reasons.append(f"Ultra-low delta ({round(delta, 2)})")
    if q.volume < 1000:
        score -= 30.0
        reasons.append("Low volume")
    if mid < 15.0 and delta < 0.20:
        score -= 40.0
        reasons.append(f"Cheap trap: ₹{mid} premium with low delta {round(delta, 2)}")

    score = max(0.0, min(100.0, score))
    q.quality_score = round(score, 1)
    q.quality_reason = "; ".join(reasons) if reasons else "High quality option"
    return q.quality_score

def classify_regime(snap: MarketSnapshot) -> Dict[str, Any]:
    price, vwap, adx, rsi, vix, pcr = snap.spot_price, snap.vwap, snap.adx, snap.rsi, snap.vix, snap.pcr
    expected_move = snap.spot_price * (vix / 100.0) * math.sqrt(max(0.01, snap.days_to_expiry / 365.0))

    if snap.days_to_expiry < 0.5 and vix < 12.0 and adx < 20:
        return {"regime": "Expiry Pinning", "confidence": 85.0, "lower": price - expected_move, "upper": price + expected_move}
    if vix > 22.0 or adx > 30:
        reg = "High-Volatility Breakout" if vix > 22.0 else ("Strong Bullish Trend" if price > vwap else "Strong Bearish Trend")
        return {"regime": reg, "confidence": 80.0, "lower": price - expected_move, "upper": price + expected_move}
    if adx > 22:
        reg = "Weak Bullish Trend" if price > vwap else "Weak Bearish Trend"
        return {"regime": reg, "confidence": 75.0, "lower": price - expected_move, "upper": price + expected_move}
    return {"regime": "Range-bound", "confidence": 65.0, "lower": price - expected_move, "upper": price + expected_move}

def generate_decision(snap: MarketSnapshot, capital: float = 50000.0, max_risk_pct: float = 1.5) -> Dict[str, Any]:
    lot_size = 25
    spot = snap.spot_price
    regime = classify_regime(snap)

    # Calculate Greeks & Quality Scores
    for k, q in snap.calls.items():
        g = calculate_greeks(spot, k, snap.days_to_expiry / 365.0, 0.07, q.iv, "CE")
        q.delta, q.gamma, q.theta, q.vega = g["delta"], g["gamma"], g["theta"], g["vega"]
        evaluate_cheap_option_trap(q, spot)

    for k, q in snap.puts.items():
        g = calculate_greeks(spot, k, snap.days_to_expiry / 365.0, 0.07, q.iv, "PE")
        q.delta, q.gamma, q.theta, q.vega = g["delta"], g["gamma"], g["theta"], g["vega"]
        evaluate_cheap_option_trap(q, spot)

    # Search strategy candidates
    atm_strike = min(snap.calls.keys(), key=lambda k: abs(k - spot)) if snap.calls else spot
    candidates = []

    # ATM Bull Call Spread
    call_strikes = sorted([k for k in snap.calls.keys() if k >= atm_strike])
    if len(call_strikes) >= 2:
        k1, k2 = call_strikes[0], call_strikes[1]
        c1, c2 = snap.calls[k1], snap.calls[k2]
        net_debit = c1.ask - c2.bid
        max_loss = net_debit * lot_size + 40.0  # Fees
        max_profit = (k2 - k1 - net_debit) * lot_size - 40.0
        if net_debit > 0 and max_profit > 0:
            pop = max(0.2, min(0.8, c1.delta - 0.1))
            ev = (pop * max_profit) - ((1.0 - pop) * max_loss)
            rr = max_profit / max(1.0, max_loss)
            if ev > 50.0 and rr >= 1.5 and (c1.quality_score + c2.quality_score) / 2.0 >= 60.0:
                candidates.append({
                    "name": "Bull Call Spread",
                    "legs": [f"BUY 1x {k1} CE @ ₹{c1.ask}", f"SELL 1x {k2} CE @ ₹{c2.bid}"],
                    "req_capital": net_debit * lot_size,
                    "max_loss": round(max_loss, 2),
                    "max_profit": round(max_profit, 2),
                    "breakeven": round(k1 + net_debit, 2),
                    "pop": round(pop, 2),
                    "ev": round(ev, 2),
                    "rr": round(rr, 2),
                    "delta": round((c1.delta - c2.delta) * lot_size, 2),
                    "quality": round((c1.quality_score + c2.quality_score) / 2.0, 1)
                })

    max_allowed_risk = capital * (max_risk_pct / 100.0)
    valid_candidates = [c for c in candidates if c["max_loss"] <= max_allowed_risk]

    if not valid_candidates or "Bullish" not in regime["regime"]:
        return {
            "action": "NO TRADE",
            "regime": regime["regime"],
            "confidence": regime["confidence"],
            "spot": spot,
            "expiry": "Tuesday Expiry",
            "time_remaining": f"{int(snap.days_to_expiry * 24)}h",
            "reason": "No statistically favorable trade setup met risk/reward and quality criteria."
        }

    valid_candidates.sort(key=lambda c: (c["ev"] / c["max_loss"]) * c["pop"], reverse=True)
    best = valid_candidates[0]
    lots = max(1, int(max_allowed_risk // best["max_loss"]))

    return {
        "action": "BUY",
        "regime": regime["regime"],
        "confidence": regime["confidence"],
        "strategy": best["name"],
        "legs": best["legs"],
        "spot": spot,
        "expiry": "Tuesday Expiry",
        "time_remaining": f"{int(snap.days_to_expiry * 24)}h",
        "entry_zone": f"{spot - 10} - {spot + 10}",
        "stop_loss": spot - round(snap.atr * 0.8, 2),
        "target_1": spot + round(snap.atr * 1.0, 2),
        "target_2": spot + round(snap.atr * 1.8, 2),
        "max_loss": best["max_loss"] * lots,
        "max_profit": best["max_profit"] * lots,
        "breakeven": best["breakeven"],
        "pop": best["pop"],
        "ev": best["ev"] * lots,
        "rr": best["rr"],
        "delta": best["delta"] * lots,
        "lots": lots,
        "risk_amount": best["max_loss"] * lots,
        "risk_pct": round((best["max_loss"] * lots / capital) * 100.0, 2),
        "quality_score": best["quality"]
    }

def format_signal(dec: Dict[str, Any]) -> str:
    if dec["action"] == "NO TRADE":
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIFTY EXPIRY TRADE SIGNAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Market Regime:      {dec['regime']} ({dec['confidence']}%)
Direction:          NEUTRAL
Decision:           NO TRADE

Underlying:         NIFTY 50
Current NIFTY:      {dec['spot']}
Expiry:             {dec['expiry']}
Time Remaining:     {dec['time_remaining']}

REASON:
{dec['reason']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    legs_formatted = "\n".join([f"• {leg}" for leg in dec["legs"]])
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIFTY EXPIRY TRADE SIGNAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Market Regime:      {dec['regime']} ({dec['confidence']}%)
Direction:          BULLISH
Strategy:           {dec['strategy']}

Underlying:         NIFTY 50
Current NIFTY:      {dec['spot']}
Expiry:             {dec['expiry']}
Time Remaining:     {dec['time_remaining']}

LEGS:
{legs_formatted}

Entry Zone:         {dec['entry_zone']}
Stop Loss:          ₹{dec['stop_loss']}
Target 1:           ₹{dec['target_1']}
Target 2:           ₹{dec['target_2']}

Maximum Loss:       ₹{dec['max_loss']}
Maximum Profit:     ₹{dec['max_profit']}
Breakeven:          {dec['breakeven']}

Probability of Profit: {int(dec['pop'] * 100)}%
Expected Value:     ₹{dec['ev']}
Risk/Reward:        1 : {dec['rr']}

Delta:              {dec['delta']}
Signal Quality:     {dec['quality_score']} / 100

POSITION SIZE:
Recommended lots:   {dec['lots']} lots
Account Risk:       ₹{dec['risk_amount']} ({dec['risk_pct']}% of capital)

ACTION:
{dec['action']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def create_demo_snapshot() -> MarketSnapshot:
    spot = 22000.0
    return MarketSnapshot(
        spot_price=spot, vwap=21960.0, atr=110.0, rsi=64.0, adx=32.0, vix=14.5, pcr=1.35, days_to_expiry=1.5,
        calls={
            22000.0: OptionQuote(strike=22000.0, option_type="CE", ltp=100.0, bid=99.0, ask=101.0, volume=50000, open_interest=80000, iv=0.15),
            22100.0: OptionQuote(strike=22100.0, option_type="CE", ltp=50.0, bid=49.0, ask=51.0, volume=40000, open_interest=60000, iv=0.15)
        },
        puts={
            22000.0: OptionQuote(strike=22000.0, option_type="PE", ltp=90.0, bid=89.0, ask=91.0, volume=40000, open_interest=70000, iv=0.16),
            21900.0: OptionQuote(strike=21900.0, option_type="PE", ltp=45.0, bid=44.0, ask=46.0, volume=35000, open_interest=50000, iv=0.16)
        }
    )

if __name__ == "__main__":
    demo_snap = create_demo_snapshot()
    decision = generate_decision(demo_snap, capital=50000.0, max_risk_pct=1.5)
    print(format_signal(decision))
