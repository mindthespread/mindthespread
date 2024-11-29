from abc import ABC, abstractmethod
import pandas
from typing import List
from mindthespread.env import BaseEnv
from mindthespread.entities.agent import AgentResponse
from mindthespread.ta import TA, apply_indicators

class AgentBase(ABC):
    def __init__(self, indicators: List[TA], min_records_needed=500):
        self.env: BaseEnv = None
        self.cols = self.dtype = None
        self.indicators = indicators
        self.min_records_needed = min_records_needed

    def reset(self):
        if self.env:
            self.env.reset()

    def set_env(self, env: BaseEnv):
        self.env = env
        self.env.calc_signals = self.calc_signals

    def calc_signals(self, feed: pandas.DataFrame) -> pandas.DataFrame:
        signals = apply_indicators(feed, self.indicators)
        assert signals is not None, "No Signals returned"
        self.cols = signals.columns
        self.dtype = signals.dtypes
        return signals

    @abstractmethod
    def act(self, curr_idx, obs) -> AgentResponse:
        raise NotImplementedError