from abc import abstractmethod
import pandas
from typing import List
import logging
import datetime
from mindthespread.brokers.broker import FeedBroker
from mindthespread.feedstore.engines.base import FeedStoreEngine


class Feed:
    def __init__(self, feed_name: str, feedstore_engine: FeedStoreEngine, feed_broker: FeedBroker = None):
        """
        Represents a feed's metadata and operations.

        :param feed_name: The name of the feed (e.g., 'EURUSD_1h').
        :param feedstore_engine: The feed engonline_manager_old.pyine responsible for fetching and saving the data (e.g., PandasFeedStoreEngine).
        :param feed_broker: optional. the broker to fetch the feed from.
        """
        self.feed_name = feed_name  # Feed name like "EURUSD_1h"
        self.feedstore_engine: FeedStoreEngine = feedstore_engine  # PandasFeedStoreEngine, SQLAlchemyFeedStoreEngine, etc.
        self.feed_broker = feed_broker
        self.data = None

    def load_feed(self):
        data = self.feedstore_engine.load_feed(self.feed_name)
        self.data = data
        return self

    def fetch_by_date_range(self,
                            start_time: datetime = None,
                            end_time: datetime = None):
        """
        Fetches the feed data from the feed engine for a specific time range.

        :param start_time: The start of the time range to fetch.
        :param end_time: The end of the time range to fetch.
        :return: A pandas DataFrame containing the feed data in the given range.
        """
        # Fetch feed data from the engine
        data = self.feedstore_engine.fetch_feed_by_date_range(self.feed_name, start_time, end_time)
        self.data = data
        return self


    def fetch_latest(self, n: int):
        data = self.feedstore_engine.fetch_latest(self.feed_name, n)
        self.data = data.iloc[-n:]
        return self

    def save(self, data: pandas.DataFrame):
        """
        Saves the feed data using the feed engine after validation.

        :param data: The feed data to be saved.
        """
        # Validate feed data before saving it
        # self.feed_type.validate_feed(data)
        # Save feed data to the engine
        self.feedstore_engine.save_feed(self.feed_name, data)


    @abstractmethod
    def sync_from_source(self, lookback_records: int) -> int:
        raise NotImplementedError()


    @classmethod
    def concatenate_feeds(cls, feed_names: List[str], feedstore_engine: FeedStoreEngine, start_time=None, end_time=None):
        feed_dfs = []
        for feed_name in feed_names:
            symbol_feed = cls(feed_name=feed_name, feedstore_engine=feedstore_engine)
            symbol_feed.fetch_by_date_range(start_time=start_time, end_time=end_time)

            if len(symbol_feed.data) == 0:
                logging.warning(f'no data found for feed: {feed_name}')
                continue

            df = symbol_feed.data
            logging.info(f'loaded feed:{feed_name}; start:{min(df.index)}; end:{max(df.index)}; records:{len(df)}')

            feed_dfs.append(symbol_feed.data)

        return feed_dfs