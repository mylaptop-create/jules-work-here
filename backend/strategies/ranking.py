from typing import List, Optional
from backend.data.models import StrategyCandidate
from backend.utils.config import AppConfig

def rank_and_select_strategy(candidates: List[StrategyCandidate], config: AppConfig) -> Optional[StrategyCandidate]:
    """
    Ranks candidates using Risk-Adjusted Expected Value:
    EV_SCORE = Expected Value / Max Loss * POP * Quality Score
    Rejects strategies failing hard risk criteria.
    """
    valid = []
    for c in candidates:
        if c.required_capital > config.capital.account_capital:
            c.rejection_reason = "Exceeds available capital"
            continue
        if c.max_loss > config.capital.account_capital * (config.capital.max_risk_per_trade_percent / 100.0):
            c.rejection_reason = f"Max loss exceeds trade risk limit ({config.capital.max_risk_per_trade_percent}%)"
            continue
        if c.risk_reward_ratio < config.strategy.min_risk_reward:
            c.rejection_reason = f"Risk/Reward ratio {c.risk_reward_ratio} < min required {config.strategy.min_risk_reward}"
            continue
        if c.expected_value < config.strategy.min_expected_value:
            c.rejection_reason = f"Expected Value ₹{c.expected_value} < min required ₹{config.strategy.min_expected_value}"
            continue
        if c.probability_of_profit < config.strategy.min_probability_of_profit:
            c.rejection_reason = f"POP {c.probability_of_profit} < min required {config.strategy.min_probability_of_profit}"
            continue
        if c.quality_score < config.strategy.cheap_option_min_quality_score:
            c.rejection_reason = f"Option Quality Score {c.quality_score} < min required {config.strategy.cheap_option_min_quality_score}"
            continue

        valid.append(c)

    if not valid:
        return None

    # Sort by risk-adjusted expected score
    valid.sort(key=lambda c: (c.expected_value / max(1.0, c.max_loss)) * c.probability_of_profit * (c.quality_score / 100.0), reverse=True)
    return valid[0]
