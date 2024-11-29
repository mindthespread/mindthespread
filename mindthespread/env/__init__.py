import gymnasium
from abc import ABC, abstractmethod
import pandas


class BaseEnv(gymnasium.Env, ABC):

    @abstractmethod
    def set_ohlc_feed(self, ohlc_data: pandas.DataFrame) -> None:
        raise NotImplementedError

    @abstractmethod
    def calc_signals(self, feed_data: pandas.DataFrame) -> pandas.DataFrame:
        raise NotImplementedError