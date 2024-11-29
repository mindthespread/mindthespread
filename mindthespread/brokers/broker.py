from abc import ABC, abstractmethod
from mindthespread.entities.market import Action, Position


class FeedBroker(ABC):
    pass


class OHLCBroker(FeedBroker):
    @abstractmethod
    def get_candles(self, symbol, freq, start, end):
        raise Exception('Function not impl')


class MarketBroker:
    @abstractmethod
    def enter_position(self, symbol: str, action: Action, qty: float):
        raise Exception('Function not impl')

    @abstractmethod
    def close_position(self, position: Position):
        raise Exception('function not impl')

    @abstractmethod
    def get_position(self, symbol):
        raise Exception('function not impl')

    @abstractmethod
    def connect(self) -> bool:
        raise Exception('function not impl')
