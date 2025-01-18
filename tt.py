from mindthespread.constants import sp500_symbols
from mindthespread.feedstore.engines.pandas import PandasFeedEngine
from mindthespread.feedstore.feeds.ohlc_feed import OHLCFeed

feedstore_engine = PandasFeedEngine('feeds/stocks_daily/')

start_time = '2000-01-01'
end_time = '2024-01-01'
symbols = sp500_symbols[:3]
freq = '1d'

feed_names = [f'{symbol}_{freq}' for symbol in symbols]
dfs = OHLCFeed.concatenate_feeds(feed_names=feed_names, feedstore_engine=feedstore_engine,
                                 start_time=start_time, end_time=end_time)


pass