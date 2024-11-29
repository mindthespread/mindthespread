import pandas
import yfinance
from mindthespread.brokers.broker import OHLCBroker

class YahooFinanceBroker(OHLCBroker):
    def get_candles(self, symbol, freq, start, end):
        source = yfinance.Ticker(symbol)
        ret = source.history(start=start, end=end, interval=freq)
        ret.index = pandas.to_datetime(ret.index, utc=True)
        ret.columns = [c.lower() for c in ret.columns]
        ret.index.name = 'date'
        return ret

