import uuid
from datetime import datetime
from typing import Dict, Any, List
from backend.execution.broker_base import BrokerBase
from backend.data.models import SpotData, FuturesData, OptionChain, OptionQuote, OptionType, StrategyCandidate, ActionType, GreeksData
from backend.utils.config import AppConfig

class PaperTradingBroker(BrokerBase):
    def __init__(self, config: AppConfig):
        self.config = config
        self.orders: List[Dict[str, Any]] = []

    def get_spot_data(self, symbol: str = "NIFTY") -> SpotData:
        return SpotData(
            symbol=symbol,
            timestamp=datetime.now(),
            last_price=22000.0,
            open=21950.0,
            high=22050.0,
            low=21900.0,
            previous_close=21950.0,
            vwap=21980.0,
            atr=100.0,
            rsi=62.0,
            adx=28.0,
            india_vix=14.0
        )

    def get_futures_data(self, symbol: str = "NIFTY_FUT") -> FuturesData:
        return FuturesData(
            symbol=symbol,
            timestamp=datetime.now(),
            last_price=22020.0,
            volume=45000,
            open_interest=950000,
            basis=20.0
        )

    def get_option_chain(self, symbol: str = "NIFTY") -> OptionChain:
        spot = 22000.0
        return OptionChain(
            symbol=symbol,
            spot_price=spot,
            expiry_date="2025-03-04",
            days_to_expiry=1.5,
            time_to_expiry_hours=36.0,
            pcr=1.25,
            calls={
                22000.0: OptionQuote(strike=22000.0, option_type=OptionType.CALL, expiry="2025-03-04", ltp=100.0, bid=99.0, ask=101.0, bid_qty=500, ask_qty=500, volume=10000, open_interest=50000, change_in_oi=1000, iv=0.15, greeks=GreeksData(delta=0.50, gamma=0.001, theta=-10.0, vega=5.0, implied_volatility=0.15)),
                22100.0: OptionQuote(strike=22100.0, option_type=OptionType.CALL, expiry="2025-03-04", ltp=50.0, bid=49.0, ask=51.0, bid_qty=500, ask_qty=500, volume=8000, open_interest=40000, change_in_oi=800, iv=0.15, greeks=GreeksData(delta=0.35, gamma=0.0008, theta=-8.0, vega=4.0, implied_volatility=0.15))
            },
            puts={
                22000.0: OptionQuote(strike=22000.0, option_type=OptionType.PUT, expiry="2025-03-04", ltp=90.0, bid=89.0, ask=91.0, bid_qty=500, ask_qty=500, volume=12000, open_interest=80000, change_in_oi=2000, iv=0.16, greeks=GreeksData(delta=-0.48, gamma=0.001, theta=-9.0, vega=5.0, implied_volatility=0.16)),
                21900.0: OptionQuote(strike=21900.0, option_type=OptionType.PUT, expiry="2025-03-04", ltp=45.0, bid=44.0, ask=46.0, bid_qty=500, ask_qty=500, volume=10000, open_interest=60000, change_in_oi=1500, iv=0.16, greeks=GreeksData(delta=-0.32, gamma=0.0008, theta=-7.0, vega=4.0, implied_volatility=0.16))
            }
        )

    def execute_strategy(self, strategy: StrategyCandidate, lots: int) -> Dict[str, Any]:
        order_id = str(uuid.uuid4())[:8]
        executed_legs = []

        for leg in strategy.legs:
            slippage = self.config.strategy.max_slippage_points if leg.action == ActionType.BUY else -self.config.strategy.max_slippage_points
            fill_price = leg.entry_price + slippage
            executed_legs.append({
                "strike": leg.strike,
                "option_type": leg.option_type,
                "action": leg.action,
                "fill_price": fill_price,
                "quantity": leg.quantity * lots
            })

        record = {
            "order_id": order_id,
            "timestamp": datetime.now(),
            "strategy": strategy.name,
            "lots": lots,
            "executed_legs": executed_legs,
            "status": "FILLED_PAPER"
        }
        self.orders.append(record)
        return record
