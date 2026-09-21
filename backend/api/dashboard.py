from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from backend.data.models import SpotData, FuturesData, OptionChain, MarketRegime, TradeSignal

def render_dashboard(spot: SpotData, chain: OptionChain, regime: MarketRegime, signal: TradeSignal) -> str:
    console = Console(width=60)

    header = f"NIFTY: {spot.last_price} | EXPIRY: {chain.expiry_date} | DTE: {chain.time_to_expiry_hours}h | VIX: {spot.india_vix}"
    regime_info = f"REGIME: {regime.regime.value}\nCONFIDENCE: {regime.confidence}%\nRANGE: {round(regime.expected_range_lower,1)} - {round(regime.expected_range_upper,1)}"
    chain_info = f"PCR: {chain.pcr} | CALL RES: {spot.last_price + 100} | PUT SUPP: {spot.last_price - 100}"

    strat_name = signal.recommended_strategy.name if signal.recommended_strategy else "NO TRADE"
    strat_info = f"BEST STRATEGY: {strat_name}\nACTION: {signal.action.value}\nEV: ₹{signal.expected_value} | POP: {int(signal.probability_of_profit*100)}%"

    panel = Panel(
        f"{header}\n{'─'*50}\n{regime_info}\n{'─'*50}\n{chain_info}\n{'─'*50}\n{strat_info}",
        title="[bold cyan]NIFTY 50 TUESDAY EXPIRY BOT[/bold cyan]",
        border_style="green"
    )

    with console.capture() as capture:
        console.print(panel)
    return capture.get()
