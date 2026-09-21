from backend.data.models import TradeSignal, ActionType

def format_trade_signal(signal: TradeSignal) -> str:
    if signal.action == ActionType.NO_TRADE or not signal.recommended_strategy:
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIFTY EXPIRY TRADE SIGNAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Market Regime:      {signal.market_regime.regime.value}
Direction:          {signal.direction}
Decision:           NO TRADE

Underlying:         NIFTY
Current NIFTY:      {signal.underlying_price}
Expiry:             {signal.expiry}
Time Remaining:     {signal.time_remaining}

REASON:
No statistically favorable trade setup exists under current risk/reward & quality criteria.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    strat = signal.recommended_strategy
    leg_str = "\n".join([f"• {leg.action.value} {leg.quantity}x {leg.strike} {leg.option_type.value} @ ₹{leg.entry_price}" for leg in strat.legs])
    reasons = "\n".join([f"{i+1}. {r}" for i, r in enumerate(signal.reasons_for_trade)])
    invalidations = "\n".join([f"{i+1}. {inv}" for i, inv in enumerate(signal.invalidation_conditions)])

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NIFTY EXPIRY TRADE SIGNAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Market Regime:      {signal.market_regime.regime.value}
Direction:          {signal.direction}
Strategy:           {strat.name}

Underlying:         NIFTY
Current NIFTY:      {signal.underlying_price}
Expiry:             {signal.expiry}
Time Remaining:     {signal.time_remaining}

LEGS:
{leg_str}

Entry Zone:         {signal.entry_zone}
Stop Loss:          ₹{signal.stop_loss}
Target 1:           ₹{signal.target_1}
Target 2:           ₹{signal.target_2}

Maximum Loss:       ₹{signal.max_loss}
Maximum Profit:     ₹{signal.max_profit}
Breakeven:          {signal.breakeven}

Probability of Profit: {int(signal.probability_of_profit * 100)}%
Expected Value:     ₹{signal.expected_value}
Risk/Reward:        1 : {signal.risk_reward_ratio}

Delta:              {strat.net_delta}
Gamma:              {strat.net_gamma}
Theta:              {strat.net_theta}
Vega:               {strat.net_vega}
Option Quality:     {strat.quality_score}/100

WHY THIS TRADE?
{reasons}

INVALIDATION:
{invalidations}

POSITION SIZE:
Recommended lots:   {signal.recommended_lots} lots

RISK:
₹{signal.risk_amount} ({signal.risk_percent_of_account}% of account)

SIGNAL QUALITY:
{signal.signal_quality_score} / 100

ACTION:
{signal.action.value}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
