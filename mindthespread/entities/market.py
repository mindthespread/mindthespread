from enum import Enum


class Action(Enum):
    BUY = 0
    SELL = 1
    HOLD = 2
    CLOSE = 3


class Direction(Enum):
    Short = 0
    Out = 1
    Long = 2


class Position:
    def __init__(self, symbol: str = None, entry_price: float = None, qty: float = None,
                 direction: Direction = Direction.Out, stop_loss: float = None, position_id=None):
        self.symbol = symbol
        self.entry_price = entry_price
        self.qty = abs(qty) if qty is not None else None
        self.direction = direction
        self.stop_loss = stop_loss
        self.position_id = position_id


class Order:
    def __init__(self, action: Action, qty: float, stop_loss: int, trailing_stop: int):
        self.action = action
        self.qty = qty
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop

