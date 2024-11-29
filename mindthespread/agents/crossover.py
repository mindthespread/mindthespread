import pandas as pd
from mindthespread.agents.base import AgentBase, AgentResponse
from mindthespread.entities.market import Action, Direction
from mindthespread.ta import TA


class AgentCrossover(AgentBase):
    """
    A trading agent based on the crossover of two Simple Moving Averages (SMA).

    The agent generates buy/sell signals when the shorter SMA crosses above/below
    the longer SMA. It can also incorporate stop-loss logic.
    """

    def __init__(self, sma_long: int, sma_short: int, qty: int = 1, stop_loss: float = None):
        """
        Initialize the crossover agent with specified SMA periods and trading parameters.

        Args:
            sma_long (int): The period for the long simple moving average (SMA).
            sma_short (int): The period for the short simple moving average (SMA).
            qty (int): Quantity of assets to trade. Default is 1.
            stop_loss (float): Optional stop-loss threshold. Default is None.
        """

        self.qty = qty
        self.stop_loss = stop_loss

        # Initialize indicators for long and short SMAs
        indicators = [
            TA(indicator='sma', length=sma_long),
            TA(indicator='sma', length=sma_short)
        ]
        super().__init__(indicators=indicators)

    def act(self, curr_index: int, obs: dict) -> AgentResponse:
        """
        Make a trading decision based on the crossover of the SMA signals.

        Args:
            curr_index (int): The current index in the data feed.
            obs (dict): Current observation containing signals and position.

                obs structure:
                {
                    'signals': list of SMA values [long_sma, short_sma],
                    'position': current position (Direction.Long, Direction.Short, or None)
                }

        Returns:
            AgentResponse: The action decided by the agent, including the action type,
            quantity, and stop-loss if applicable.
        """
        # Extract signals from observation
        signals = obs.get('signals', [])
        if len(signals) < 2:
            raise ValueError("Expected at least two signals (long_sma, short_sma) in the observation.")

        long_sma, short_sma = signals

        # Handle cases where SMA values are NaN
        if pd.isna(long_sma) or pd.isna(short_sma):
            return AgentResponse(action=Action.HOLD)

        # Decision-making based on SMA crossover
        current_position = obs.get('position', None)
        if short_sma < long_sma and current_position != Direction.Long.value:
            return AgentResponse(action=Action.BUY, qty=self.qty, stop_loss=self.stop_loss)

        if short_sma > long_sma and current_position != Direction.Short.value:
            return AgentResponse(action=Action.SELL, qty=self.qty, stop_loss=self.stop_loss)

        # Default to holding position
        return AgentResponse(action=Action.HOLD)
