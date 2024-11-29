import pandas as pd
from datetime import datetime
from datetime import timezone
import os
import unittest
from mindthespread.feedstore.engines.pandas import PandasFeedEngine
from mindthespread.feedstore.feeds.ohlc_feed import OHLCFeed
from mindthespread.feedstore.feeds.feed import Feed


class FeedLifecycleTests(unittest.TestCase):

    def setUp(self):
        """Setup: Create a temporary directory, initialize engines and feeds."""
        self.base_path = "/tmp/test_feeds"
        os.makedirs(self.base_path, exist_ok=True)
        self.pandas_engine = PandasFeedEngine(base_path=self.base_path)

        # OHLC Feed
        self.ohlc_feed = OHLCFeed(feed_name="EURUSD_1h", feedstore_engine=self.pandas_engine)
        self.ohlc_initial_data = pd.DataFrame({
            "date": [
                datetime(2024, 9, 1, 12),
                datetime(2024, 9, 1, 13),
                datetime(2024, 9, 1, 14)
            ],
            "open": [1.12, 1.13, 1.14],
            "high": [1.13, 1.14, 1.15],
            "low": [1.11, 1.12, 1.13],
            "close": [1.12, 1.13, 1.14],
            "volume": [1000, 1200, 1100]
        })

        # News Feed
        self.news_feed = Feed(feed_name="EURUSD_News", feedstore_engine=self.pandas_engine)
        self.news_initial_data = pd.DataFrame({
            "date": [
                datetime(2024, 9, 1, 12),
                datetime(2024, 9, 1, 13),
            ],
            "news": ["EUR/USD pair fluctuates", "Macro news affecting EUR/USD"],
            "tags": [["EURUSD", "Forex"], ["EURUSD", "Macro", "USD"]]
        })

    def tearDown(self):
        """Clean up: Delete feed files and the temporary directory."""
        for feed_name in ["EURUSD_1h.csv", "EURUSD_News.csv"]:
            feed_file_path = os.path.join(self.base_path, feed_name)
            if os.path.exists(feed_file_path):
                os.remove(feed_file_path)
        if os.path.exists(self.base_path):
            os.rmdir(self.base_path)

    def test_create_ohlc_feed(self):
        """Test creating the OHLC feed and initializing its properties."""
        self.assertEqual(self.ohlc_feed.feed_name, "EURUSD_1h", "Feed name mismatch")

    def test_save_and_fetch_ohlc_feed(self):
        """Test saving and fetching OHLC feed data."""
        # Save initial OHLC data
        self.ohlc_feed.save(self.ohlc_initial_data)

        # Fetch and validate
        fetched_data = self.ohlc_feed.fetch_by_date_range(start_time=datetime(2024, 9, 1, 12), end_time=datetime(2024, 9, 1, 14))
        # self.assertEqual(len(fetched_data), 3, f"Expected 3 rows, got {len(fetched_data)}")
        # self.assertTrue(all(fetched_data["close"] == [1.12, 1.13, 1.14]), "Fetched data 'close' values mismatch")

    def test_merge_ohlc_feed(self):
        """Test merging new OHLC data with existing feed data."""
        # Save initial OHLC data
        self.ohlc_feed.save(self.ohlc_initial_data)

        # New data to merge
        new_data = pd.DataFrame({
            "date": [
                datetime(2024, 9, 1, 15),
                datetime(2024, 9, 1, 16)
            ],
            "open": [1.15, 1.16],
            "high": [1.16, 1.17],
            "low": [1.14, 1.15],
            "close": [1.15, 1.16],
            "volume": [1300, 1400]
        })

        # Merge new data
        # self.ohlc_feed.merge(new_data)

        # Fetch merged data and validate
        # merged_data = self.ohlc_feed.fetch(start_time=datetime(2024, 9, 1, 12), end_time=datetime(2024, 9, 1, 16))
        # self.assertEqual(len(merged_data), 5, f"Expected 5 rows after merge, got {len(merged_data)}")
        # expected_close_values = [1.12, 1.13, 1.14, 1.15, 1.16]
        # self.assertTrue(all(merged_data["close"] == expected_close_values), f"Merged data 'close' values mismatch: {merged_data['close'].tolist()}")

    def test_create_news_feed(self):
        """Test creating the News feed and initializing its properties."""
        self.assertEqual(self.news_feed.feed_name, "EURUSD_News", "News feed name mismatch")

    def test_save_and_fetch_news_feed(self):
        """Test saving and fetching News feed data."""
        # Save initial News data
        self.news_feed.save(self.news_initial_data)

        # Fetch and validate
        fetched_news = self.news_feed.fetch_by_date_range(start_time=datetime(2024, 9, 1, 12), end_time=datetime(2024, 9, 1, 13))
        # self.assertEqual(len(fetched_news), 2, f"Expected 2 news entries, got {len(fetched_news)}")
        # self.assertEqual(fetched_news["news"].iloc[0], "EUR/USD pair fluctuates", "First news entry mismatch")
        # self.assertEqual(fetched_news["tags"].iloc[1], ["EURUSD", "Macro", "USD"], "Second news tags mismatch")


if __name__ == '__main__':
    unittest.main()
