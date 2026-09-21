from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.data.models import OptionChain, SpotData, FuturesData, StrategyCandidate

class BrokerBase(ABC):
    @abstractmethod
    def get_spot_data(self, symbol: str = "NIFTY") -> SpotData:
        pass

    @abstractmethod
    def get_futures_data(self, symbol: str = "NIFTY_FUT") -> FuturesData:
        pass

    @abstractmethod
    def get_option_chain(self, symbol: str = "NIFTY") -> OptionChain:
        pass

    @abstractmethod
    def execute_strategy(self, strategy: StrategyCandidate, lots: int) -> Dict[str, Any]:
        pass
