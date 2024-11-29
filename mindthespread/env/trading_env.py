from typing import Union

import pandas as pd
import random
import logging
import numpy as np
from gymnasium import spaces
from mindthespread.entities.agent import AgentResponse
from mindthespread.env import BaseEnv
from mindthespread.entities.market import Action, Position, Direction


class TradingEnv(BaseEnv):
    """
    Trading environment simulating the trading of a financial instrument
    using predefined actions (buy, sell, hold) and observing the market
    through bid and ask prices from a data feed.
    """

    def __init__(self, episode_window: int = None, batch_window: int = 1,
                 bid_col: str = 'bidclose', ask_col: str = 'askclose', symbol=None, pip=0.0001):
        """
        Initialize the Trading Environment.

        Args:
            episode_window (int): Maximum number of steps per episode.
            batch_window (int): Batch size used when resetting.
            bid_col (str): Column name for bid prices in the data feed.
            ask_col (str): Column name for ask prices in the data feed.
            symbol (str): Trading symbol.
        """
        self.symbol = symbol
        self.episode_window = episode_window
        self.batch_window = batch_window
        self.bid_col = bid_col
        self.ask_col = ask_col

        # Initialize state variables
        self.position = None
        self.curr_idx = None
        self.last_price = None
        self.obs = {}
        self.step_count = 0
        self.total_reward = 0
        self.closed_transactions = 0
        self.wins = 0
        self.step_reward = 0
        self.transaction_reward = 0
        self.pip = pip

        # Initialize data variables
        self.feed = None
        self.signals = None
        self.info = {}

        # Define the action space (BUY, SELL, HOLD, etc.)
        self.action_space = spaces.Discrete(len(Action))

        # Observation space (to be set later based on signals)
        self.observation_space = None

        # Tracking transactions and log returns
        self.transactions = pd.DataFrame(columns=['amount', 'price'])
        self.log_returns = pd.Series(dtype='float64')
        self.positions = pd.Series(dtype='float64')

    def set_ohlc_feed(self, feed_data: pd.DataFrame) -> None:
        """
        Set the market data feed for the environment.

        Args:
            feed_data (pd.DataFrame): DataFrame containing the feed with bid/ask prices.
        """
        assert feed_data is not None and not feed_data.empty, "Feed data must not be empty"

        # Generate trading signals and validate them
        # self.signals = self.calc_signals(feed_data).dropna()
        self.signals = self.calc_signals(feed_data)
        assert not self.signals.empty, "No valid signals generated"

        # Align feed with the available signals
        self.feed = feed_data.loc[self.signals.index]
        self.curr_idx = self.feed.index[0]  # Start at the first index

        # Initialize observation space based on the first set of signals
        if self.observation_space is None:
            self.set_obs_space(self.signals)

        # Calculate initial observation
        self.calc_obs()

    def calc_signals(self, feed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Abstract method to calculate trading signals from the feed data.

        Should be overridden by subclasses or user-defined implementations.
        """
        raise NotImplementedError("Method calc_signals not implemented")

    def close_position(self):
        """
        Close the current open trading position and update rewards and statistics.
        """
        if self.position:
            self.closed_transactions += 1
            self.total_reward += self.transaction_reward
            if self.transaction_reward > 0:
                self.wins += 1
            self.position = None
            self.transaction_reward = 0

    def enter_position(self, agent_resp: AgentResponse, entry_price: float):
        """
        Enter a new position based on the agent's action and entry price.

        Args:
            agent_resp (AgentResponse): Response object from the agent with action details.
            entry_price (float): Entry price for the trade.
        """
        direction = Direction.Long if agent_resp.action == Action.BUY else Direction.Short
        self.position = Position(direction=direction, qty=agent_resp.qty,
                                 stop_loss=agent_resp.stop_loss, entry_price=entry_price)

    def step(self, agent_resp: Union[int | AgentResponse]):
        """
        Execute a step in the environment given an agent's response.

        Args:
            agent_resp (int | AgentResponse): The agent's action or response.

        Returns:
            Tuple: (obs, reward, done, info)
        """
        if isinstance(agent_resp, int):
            agent_resp = AgentResponse(action=agent_resp)

        # Check that the current index is within the feed
        assert self.curr_idx in self.feed.index, f"Index {self.curr_idx} not in feed"

        # Extract bid and ask prices from the current feed record
        feed_record = self.feed.loc[self.curr_idx]
        bid_price = feed_record[self.bid_col]
        ask_price = feed_record[self.ask_col]

        # Update rewards based on the position and price changes
        self.update_position_rewards(bid_price, ask_price)

        # Determine the next action and if a stop-loss condition is met
        action, stop = self.get_action(agent_resp, bid_price, ask_price)

        # Check if the episode is done
        done = self.is_done()

        # Update environment information for rendering and debugging
        self.update_info(action, stop)

        # Advance to the next step if not done
        if not done:
            self.curr_idx = self.feed.index[self.feed.index.get_loc(self.curr_idx) + 1]
            self.step_count += 1

        # Update the observation
        self.calc_obs()

        return self.obs, self.step_reward, done, done, self.info

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        """
        Reset the environment to the initial state for a new episode.

        Args:
            seed (int): Optional random seed for reproducibility.
            options (dict): Additional options for resetting.

        Returns:
            Tuple: (obs, info)
        """
        if self.feed is None:
            self.curr_idx = None
        elif self.episode_window is not None:
            # Randomize start index based on episode window size
            start_idx = random.randint(0, len(self.feed) - self.episode_window)
            self.curr_idx = self.feed.index[start_idx]
        else:
            # Default to the first index
            self.curr_idx = self.feed.index[0]

        # Reset state variables
        self.position = None
        self.step_count = self.total_reward = self.closed_transactions = self.wins = self.step_reward = 0
        self.transaction_reward = 0
        self.calc_obs()

        return self.obs, self.info

    def set_obs_space(self, signals: pd.DataFrame):
        """
        Set the observation space based on the trading signals.

        Args:
            signals (pd.DataFrame): DataFrame of trading signals.
        """
        signals_desc = signals.describe()
        signals_obs_space = spaces.Box(low=signals_desc.loc['min'].values,
                                       high=signals_desc.loc['max'].values,
                                       dtype=np.float64)
        self.observation_space = spaces.Dict({
            "position": spaces.Discrete(len(Direction)),
            "signals": signals_obs_space
        })

    def calc_obs(self):
        """
        Calculate the current observation consisting of the position and signal values.
        """
        self.obs['position'] = Direction.Out.value if self.position is None else self.position.direction.value
        if self.curr_idx is not None and self.curr_idx in self.signals.index:
            self.obs['signals'] = self.signals.loc[self.curr_idx].values

    def update_position_rewards(self, bid_price: float, ask_price: float):
        """
        Update the rewards based on the current position and price changes.

        Args:
            bid_price (float): The current bid price.
            ask_price (float): The current ask price.
        """
        self.log_returns.at[self.curr_idx] = 0.0
        self.step_reward = 0
        if self.position:
            mul = self.position.qty / self.pip
            if self.position.direction == Direction.Long:
                self.transaction_reward = (bid_price - self.position.entry_price) * mul
                self.step_reward = self.calculate_step_reward(bid_price, self.last_price, mul)
                self.last_price = bid_price
            elif self.position.direction == Direction.Short:
                self.transaction_reward = (self.position.entry_price - ask_price) * mul
                self.step_reward = self.calculate_step_reward(self.last_price, ask_price, mul)
                self.last_price = ask_price

    def calculate_step_reward(self, current_price, previous_price, multiplier):
        """
        Calculate the step reward based on price differences.

        Args:
            current_price (float): The current price (bid or ask).
            previous_price (float): The previous price.
            multiplier (float): Multiplier based on position size.

        Returns:
            float: The calculated step reward.
        """
        if previous_price is not None and current_price is not None:
            log_return = np.log(current_price / previous_price)
            self.log_returns.at[self.curr_idx] = log_return
            return (current_price - previous_price) * multiplier
        return 0

    def get_action(self, agent_resp: AgentResponse, bid_price: float, ask_price: float):
        """
        Determine the next action and handle stop-loss conditions.

        Args:
            agent_resp (AgentResponse): The agent's response.
            bid_price (float): The current bid price.
            ask_price (float): The current ask price.

        Returns:
            Tuple: (action, stop)
        """
        stop = False
        action = agent_resp.action
        if self.position and self.position.stop_loss and self.transaction_reward < -self.position.stop_loss / self.pip:
            action = Action.CLOSE
            stop = True

        # Handle closing or contradictory actions based on the current position
        if action == Action.CLOSE or (
                action == Action.BUY and self.position and self.position.direction == Direction.Short) or \
                (action == Action.SELL and self.position and self.position.direction == Direction.Long):
            self.close_position()

        # Enter a new long position
        if action == Action.BUY and (not self.position or self.position.direction != Direction.Long):
            self.enter_position(agent_resp, entry_price=ask_price)

        # Enter a new short position
        if action == Action.SELL and (not self.position or self.position.direction != Direction.Short):
            self.enter_position(agent_resp, entry_price=bid_price)

        return action, stop

    def is_done(self):
        """
        Check if the episode is complete.

        Returns:
            bool: True if the episode is done, False otherwise.
        """
        return self.curr_idx == self.feed.index[-1] or \
            (self.episode_window is not None and self.step_count >= self.episode_window - 1)

    def update_info(self, action, stop):
        """
        Update the information dictionary with the latest step data.

        Args:
            action (Action): The action taken by the agent.
            stop (bool): Indicates if a stop-loss condition was met.
        """
        self.info = {
            'idx': str(self.curr_idx),
            'symbol': self.symbol,
            'action': action.name,
            'direction': None if not self.position else self.position.direction.name,
            'step_reward': round(self.step_reward, 2),
            'trans_reward': round(self.transaction_reward, 2),
            'closed_trans': self.closed_transactions,
            'total_reward': round(self.total_reward + self.transaction_reward, 2),
            'win_rate': 0 if not self.closed_transactions else round(self.wins / self.closed_transactions, 2),
            'qty': None if not self.position else self.position.qty,
            'stop': stop,
        }

    def render(self, mode="human"):
        """
        Render the environment for debugging or visualization.

        Args:
            mode (str): Rendering mode.
        """
        if self.info.get('action') and self.info['action'] != Action.HOLD.name or self.position:
            logging.warning(self.info)
        else:
            logging.info(self.info)

    def get_results(self):
        """
        Retrieve the results from the environment, including log returns, positions, and transactions.

        Returns:
            Tuple: (log_returns, positions, transactions)
        """
        return self.log_returns, self.positions, self.transactions