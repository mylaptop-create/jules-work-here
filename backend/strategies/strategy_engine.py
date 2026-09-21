from typing import List, Optional
from backend.data.models import OptionChain, OptionType, ActionType, OptionLeg, StrategyCandidate
from backend.options.cheap_trap import evaluate_option_quality
from backend.utils.config import AppConfig

def generate_candidate_strategies(chain: OptionChain, capital: float, config: AppConfig) -> List[StrategyCandidate]:
    candidates = []
    spot = chain.spot_price
    lot = config.lot_size.nifty

    # Evaluate options quality first
    for q in list(chain.calls.values()) + list(chain.puts.values()):
        evaluate_option_quality(q, spot, config)

    # Find ATM & OTM strikes
    atm_strike = min(chain.calls.keys(), key=lambda k: abs(k - spot)) if chain.calls else spot
    call_strikes = sorted([k for k in chain.calls.keys() if k >= atm_strike])
    put_strikes = sorted([k for k in chain.puts.keys() if k <= atm_strike], reverse=True)

    # 1. Directional ATM Call Buying
    if atm_strike in chain.calls:
        cq = chain.calls[atm_strike]
        req_cap = cq.ask * lot
        if req_cap <= capital and cq.quality_score >= config.strategy.cheap_option_min_quality_score:
            leg = OptionLeg(
                option_type=OptionType.CALL, strike=atm_strike, action=ActionType.BUY,
                expiry=chain.expiry_date, quantity=lot, entry_price=cq.ask,
                delta=cq.greeks.delta, gamma=cq.greeks.gamma, theta=cq.greeks.theta, vega=cq.greeks.vega
            )
            max_loss = round(cq.ask * lot + config.transaction_costs.brokerage_per_order * 2, 2)
            pop = round(max(0.1, min(0.9, cq.greeks.delta)), 2)
            expected_move_profit = (spot * 0.01) * cq.greeks.delta * lot
            ev = round((pop * expected_move_profit) - ((1 - pop) * max_loss), 2)
            rr = round(expected_move_profit / max(1.0, max_loss), 2)

            candidates.append(StrategyCandidate(
                name="ATM Long Call",
                legs=[leg],
                required_capital=round(req_cap, 2),
                max_loss=max_loss,
                max_profit=float('inf'),
                breakeven=[round(atm_strike + cq.ask, 2)],
                probability_of_profit=pop,
                expected_value=ev,
                risk_reward_ratio=rr,
                net_delta=round(cq.greeks.delta * lot, 2),
                net_gamma=round(cq.greeks.gamma * lot, 4),
                net_theta=round(cq.greeks.theta * lot, 2),
                net_vega=round(cq.greeks.vega * lot, 2),
                estimated_fees=round(config.transaction_costs.brokerage_per_order * 2, 2),
                estimated_slippage=round(config.strategy.max_slippage_points * lot, 2),
                quality_score=cq.quality_score
            ))

    # 2. Defined Risk Bull Call Spread
    if len(call_strikes) >= 2:
        k1, k2 = call_strikes[0], call_strikes[1]
        c1, c2 = chain.calls[k1], chain.calls[k2]
        net_debit = c1.ask - c2.bid
        req_cap = net_debit * lot
        if net_debit > 0 and req_cap <= capital:
            max_loss = round(net_debit * lot + config.transaction_costs.brokerage_per_order * 4, 2)
            max_profit = round((k2 - k1 - net_debit) * lot - config.transaction_costs.brokerage_per_order * 4, 2)
            if max_loss > 0 and max_profit > 0:
                pop = round(max(0.2, min(0.8, c1.greeks.delta - 0.1)), 2)
                ev = round((pop * max_profit) - ((1 - pop) * max_loss), 2)
                rr = round(max_profit / max_loss, 2)

                leg1 = OptionLeg(option_type=OptionType.CALL, strike=k1, action=ActionType.BUY, expiry=chain.expiry_date, quantity=lot, entry_price=c1.ask, delta=c1.greeks.delta, gamma=c1.greeks.gamma, theta=c1.greeks.theta, vega=c1.greeks.vega)
                leg2 = OptionLeg(option_type=OptionType.CALL, strike=k2, action=ActionType.SELL, expiry=chain.expiry_date, quantity=lot, entry_price=c2.bid, delta=-c2.greeks.delta, gamma=-c2.greeks.gamma, theta=-c2.greeks.theta, vega=-c2.greeks.vega)

                candidates.append(StrategyCandidate(
                    name="Bull Call Spread",
                    legs=[leg1, leg2],
                    required_capital=round(req_cap, 2),
                    max_loss=max_loss,
                    max_profit=max_profit,
                    breakeven=[round(k1 + net_debit, 2)],
                    probability_of_profit=pop,
                    expected_value=ev,
                    risk_reward_ratio=rr,
                    net_delta=round((c1.greeks.delta - c2.greeks.delta) * lot, 2),
                    net_gamma=round((c1.greeks.gamma - c2.greeks.gamma) * lot, 4),
                    net_theta=round((c1.greeks.theta - c2.greeks.theta) * lot, 2),
                    net_vega=round((c1.greeks.vega - c2.greeks.vega) * lot, 2),
                    estimated_fees=round(config.transaction_costs.brokerage_per_order * 4, 2),
                    estimated_slippage=round(config.strategy.max_slippage_points * lot * 2, 2),
                    quality_score=round((c1.quality_score + c2.quality_score) / 2.0, 1)
                ))

    # 3. Defined Risk Bear Put Spread
    if len(put_strikes) >= 2:
        k1, k2 = put_strikes[0], put_strikes[1]  # k1 higher (ATM), k2 lower (OTM)
        p1, p2 = chain.puts[k1], chain.puts[k2]
        net_debit = p1.ask - p2.bid
        req_cap = net_debit * lot
        if net_debit > 0 and req_cap <= capital:
            max_loss = round(net_debit * lot + config.transaction_costs.brokerage_per_order * 4, 2)
            max_profit = round((k1 - k2 - net_debit) * lot - config.transaction_costs.brokerage_per_order * 4, 2)
            if max_loss > 0 and max_profit > 0:
                pop = round(max(0.2, min(0.8, abs(p1.greeks.delta) - 0.1)), 2)
                ev = round((pop * max_profit) - ((1 - pop) * max_loss), 2)
                rr = round(max_profit / max_loss, 2)

                leg1 = OptionLeg(option_type=OptionType.PUT, strike=k1, action=ActionType.BUY, expiry=chain.expiry_date, quantity=lot, entry_price=p1.ask, delta=p1.greeks.delta, gamma=p1.greeks.gamma, theta=p1.greeks.theta, vega=p1.greeks.vega)
                leg2 = OptionLeg(option_type=OptionType.PUT, strike=k2, action=ActionType.SELL, expiry=chain.expiry_date, quantity=lot, entry_price=p2.bid, delta=-p2.greeks.delta, gamma=-p2.greeks.gamma, theta=-p2.greeks.theta, vega=-p2.greeks.vega)

                candidates.append(StrategyCandidate(
                    name="Bear Put Spread",
                    legs=[leg1, leg2],
                    required_capital=round(req_cap, 2),
                    max_loss=max_loss,
                    max_profit=max_profit,
                    breakeven=[round(k1 - net_debit, 2)],
                    probability_of_profit=pop,
                    expected_value=ev,
                    risk_reward_ratio=rr,
                    net_delta=round((p1.greeks.delta - p2.greeks.delta) * lot, 2),
                    net_gamma=round((p1.greeks.gamma - p2.greeks.gamma) * lot, 4),
                    net_theta=round((p1.greeks.theta - p2.greeks.theta) * lot, 2),
                    net_vega=round((p1.greeks.vega - p2.greeks.vega) * lot, 2),
                    estimated_fees=round(config.transaction_costs.brokerage_per_order * 4, 2),
                    estimated_slippage=round(config.strategy.max_slippage_points * lot * 2, 2),
                    quality_score=round((p1.quality_score + p2.quality_score) / 2.0, 1)
                ))

    return candidates
