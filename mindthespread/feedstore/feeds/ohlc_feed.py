import parse
import logging
import datetime
from mindthespread.brokers.broker import OHLCBroker
from mindthespread.feedstore.engines.base import FeedStoreEngine
from mindthespread.feedstore.feeds.feed import Feed

class OHLCFeed(Feed):
    def __init__(self,
                 feed_name: str,
                 feedstore_engine: FeedStoreEngine,
                 feed_broker: OHLCBroker = None,
                 feed_format="{symbol}_{freq}"):

        assert feed_broker is None or isinstance(feed_broker, OHLCBroker)
        super().__init__(feed_name, feedstore_engine, feed_broker)

        self.feed_broker = feed_broker
        self.feed_format = feed_format

        parse_result = parse.parse(self.feed_format, self.feed_name)
        self.symbol = parse_result.named['symbol']
        self.freq = parse_result.named['freq']

    def sync_from_source(self, lookback_records: int = 10, begining_of_time='2010-01-01'):
        self.fetch_latest(lookback_records)

        if self.data is None or len(self.data) == 0:
            start_time = begining_of_time
        else:
            start_time = self.data.index[0]

        new_feed = self.feed_broker.get_candles(start=start_time, end=datetime.datetime.now(datetime.UTC),
                                                symbol=self.symbol, freq=self.freq)
        if new_feed is None:
            logging.warning(f'pulling feed: {self.feed_name} retrieved no records')
            return 0

        self.feedstore_engine.upsert_feed(self.feed_name, new_feed)
        return len(new_feed)

    def load_feed(self):
        super().load_feed()
        self.data['symbol'] = self.symbol
        return self


    def fetch_by_date_range(self,
                            start_time: datetime = None,
                            end_time: datetime = None):
        super().fetch_by_date_range(start_time, end_time)
        self.data['symbol'] = self.symbol
        self.data.set_index('symbol', inplace=True, append=True)
        return self