from datetime import timedelta
from typing import Union

from mindthespread.entities.market import Action


class AgentResponse:
    def __init__(self, action: Union[Action | int], qty: float = 1, stop_loss: float = None, stop_loss_cooldown: timedelta = None, pred = None):
        self.action = action if isinstance(action, Action) else Action(action)
        self.qty = qty
        self.stop_loss = stop_loss
        self.stop_loss_cooldown = stop_loss_cooldown
        self.pred = pred
