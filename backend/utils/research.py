from typing import Dict, Any, List
from backend.data.models import TradeSignal, OptionChain, MarketRegime, StrategyCandidate

def explain_signal_decision(signal: TradeSignal, rejected_candidates: List[StrategyCandidate]) -> Dict[str, Any]:
    """
    Research Mode: Answers 'Why did this signal trigger?' and 'Why were other strategies rejected?'.
    """
    explanations = {
        "selected_action": signal.action.value,
        "market_regime": signal.market_regime.regime.value,
        "regime_confidence": signal.market_regime.confidence,
        "reasons_for_selected_trade": signal.reasons_for_trade,
        "rejected_strategies": []
    }

    for candidate in rejected_candidates:
        explanations["rejected_strategies"].append({
            "strategy": candidate.name,
            "rejection_reason": candidate.rejection_reason or "Lower risk-adjusted expected value than top candidate"
        })

    return explanations
