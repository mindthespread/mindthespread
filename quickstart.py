from mindthespread.agents.crossover import AgentCrossover
from mindthespread.brokers.yahoo import YahooFinanceBroker
from mindthespread.managers.offline_manager import backtest
from mindthespread.tracking.mlflow import MLFlowWrapper
from mindthespread.feedstore.engines.pandas import PandasFeedEngine
from mindthespread.feedstore.feeds.ohlc_feed import OHLCFeed

base_path = 'feeds/stocks_daily/'
pandas_engine = PandasFeedEngine(base_path=base_path)
feed_broker = YahooFinanceBroker()

MSFT_feed = OHLCFeed(feed_name="MSFT_1d",
                     feedstore_engine=pandas_engine,
                     feed_broker=feed_broker,
                     feed_format="{symbol}_{freq}")

MSFT_feed.sync_from_source()

MSFT_feed.fetch_latest(1000)

agent = AgentCrossover(sma_long=50, sma_short=20)

with MLFlowWrapper(experiment_group="mindthespread_tests", log_steps=True) as tracker:
    backtest_results = backtest(agent, MSFT_feed.data, tracker=tracker)

