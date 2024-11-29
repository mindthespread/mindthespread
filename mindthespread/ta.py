import pandas
from abc import ABC
import numpy
import pandas_ta
from typing import List


class TABase(ABC):
    def __init__(self, indicator_name=None, **kwargs):
        self.indicator_name = indicator_name or self.__class__.__name__
        self.kwargs = kwargs

    def name(self):
        params = ", ".join(f"{key}={value}" for key, value in self.kwargs.items())
        return f"{self.indicator_name}({params})"

    # @abstractmethod
class ColIndicator(TABase):
    def __init__(self, col):
        self.col = col
        super()

    def value(self, feed: pandas.DataFrame):
        return feed[self.col]


class LagIndicator(TABase):
    def __init__(self, lag, close_col = 'close'):
        assert lag > 0, 'lag must be positive'
        self.lag = lag
        self.close_col = close_col
        super()

    def value(self, feed_df: pandas.DataFrame):
        ret = numpy.log(feed_df[self.close_col].shift(self.lag) / feed_df[self.close_col])
        ret.name = f'Lag-{self.lag}'
        return ret

class TA(TABase):
    def __init__(self, indicator, **kwargs):
        super().__init__(indicator, **kwargs)

        indicator_func = getattr(pandas_ta, indicator, None)
        if indicator_func is None:
            raise ValueError(f"Indicator {indicator} not found in pandas_ta")

    def value(self, feed: pandas.DataFrame):
        func = getattr(feed.ta, self.indicator_name)
        return func(**self.kwargs)

def oscillators():
    oscillators = [
        "adx",  # Ranges from 0 to 100
        "ao",  # Typically oscillates around 0
        "cci",  # Typically ranges between -100 and 100
        "cmo",  # Ranges from -100 to 100
        "macd",  # Oscillates around 0
        "mfi",  # Ranges from 0 to 100
        "rsi",  # Ranges from 0 to 100
        "stoch",  # Typically ranges from 0 to 100
        "stochrsi",  # Typically ranges from 0 to 100
        "tsi",  # Oscillates around 0
        "willr",  # Ranges from -100 to 0
        "roc",  # Oscillates around 0
        "uo",  # Ranges from 0 to 100
        "vwma",  # Volume-weighted, often oscillates around 0
    ]

    return [TA(ind) for ind in oscillators]
    # return [TA(ind) for ind in oscillators]

def candle_patterns():
    return [TA("cdl_pattern", name="all")]
    # return [TA("cdl_pattern", name="all")]


def apply_indicators(ohlc_df: pandas.DataFrame, indicators: List[TA]):
    ret = pandas.DataFrame(index=ohlc_df.index)
    for ind in indicators:
        ind_signals = ind.value(ohlc_df)
        new_index = [i for i in ind_signals.index if i not in ohlc_df.index]
        assert len(new_index) == 0, '??'

        if isinstance(ind_signals, pandas.Series):
            ret[ind_signals.name] = ind_signals
        elif isinstance(ind_signals, pandas.DataFrame):
            # signals = signals.merge(ind_signals, left_index=True, right_index=True)
            ret = ret.merge(ind_signals, left_index=True, right_index=True, how='outer')
            pass
        else:
            # todo: handle other types here
            pass

    return ret
