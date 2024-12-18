import os
import pandas as pd
from datetime import datetime
from typing import Union
import logging

from mindthespread.feedstore.engines.base import FeedStoreEngine


class PandasFeedEngine(FeedStoreEngine):
    """
    Concrete implementation of FeedStoreEngine that handles CSV files using pandas.
    """

    def __init__(self, base_path: str, params = None):
        """
        Initialize the PandasFeedEngine with a base path for storing the feed files.

        :param base_path: The directory where feed files are stored.
        """
        self.base_path = base_path
        self.params = params or {}
        os.makedirs(self.base_path, exist_ok=True)
        logging.info(f"PandasFeedEngine initialized with base path: {self.base_path}")

    def _get_file_path(self, feed_name: str) -> str:
        """
        Construct the full file path for the given feed name.

        :param feed_name: The name of the feed.
        :return: Full path to the feed file.
        """
        return os.path.join(self.base_path, f"{feed_name}.csv")

    def load_feed(self, feed_name: str) -> pd.DataFrame:
        """
        Load the full feed data from a CSV file.

        :param feed_name: The name of the feed.
        :return: A pandas DataFrame with the feed data.
        """
        file_path = self._get_file_path(feed_name)

        if not os.path.exists(file_path):
            logging.warning(f"Feed file not found for '{feed_name}' at {file_path}. Returning empty DataFrame.")
            return pd.DataFrame()  # Returning an empty DataFrame if the file doesn't exist

        data = pd.read_csv(file_path, **self.params)

        if 'date' not in data.columns:
            raise ValueError(f"The feed '{feed_name}' is missing a 'date' column.")

        if 'time' in data.columns:
            data['date'] = data['date'] + ' ' + data['time']

        # Ensure the 'date' column is properly parsed
        data['date'] = pd.to_datetime(data['date'], utc=True)
        data.set_index('date', inplace=True)
        data.sort_index(inplace=True)

        assert len(data.index) == len(data.index.drop_duplicates()), 'duplicate indexes found'

        logging.debug(f"Loaded feed '{feed_name}' with {len(data)} records.")
        return data

    def fetch_feed_by_date_range(self, feed_name: str, start_time: Union[datetime, str],
                                 end_time: Union[datetime, str]) -> pd.DataFrame:
        """
        Load a feed from a CSV file and filter it by the given time range.

        :param feed_name: The name of the feed to load.
        :param start_time: Start of the time range (datetime or ISO 8601 string).
        :param end_time: End of the time range (datetime or ISO 8601 string).
        :return: Filtered feed data as a pandas DataFrame.
        """
        data = self.load_feed(feed_name)
        if data.empty:
            return data  # Return empty DataFrame if no data exists

        # Convert strings to datetime if needed
        start_time = pd.to_datetime(start_time, utc=True)
        end_time = pd.to_datetime(end_time, utc=True)

        cond = pd.Series([True] * len(data), index=data.index)
        if start_time:
            cond &= (data.index >= start_time)

        if end_time:
            cond &= (data.index < end_time)

        filtered_data = data[cond]
        logging.debug(f"Fetched {len(filtered_data)} records for feed '{feed_name}' between {start_time} and {end_time}.")
        return filtered_data

    def fetch_latest(self, feed_name: str, n: int):
        data = self.load_feed(feed_name)
        return data.iloc[-n:]

    def save_feed(self, feed_name: str, data: pd.DataFrame):
        """
        Save a feed to a CSV file.

        :param feed_name: The name of the feed.
        :param data: DataFrame to save.
        """
        if 'date' not in data.columns and data.index.name != 'date':
            raise ValueError(
                f"DataFrame must contain a 'date' column or have a DateTime index to save feed '{feed_name}'.")

        file_path = self._get_file_path(feed_name)
        data.to_csv(file_path, index=True)
        logging.debug(f"Saved feed '{feed_name}' with {len(data)} records to {file_path}.")

    def upsert_feed(self, feed_name: str, new_df: pd.DataFrame) -> bool:
        """
        Upsert new feed data, updating existing data and adding any new records.

        :param feed_name: The name of the feed.
        :param new_df: New data to upsert into the existing feed.
        :return: True if successful, False otherwise.
        """
        if new_df.empty:
            logging.warning(f"No data provided for upserting feed '{feed_name}'.")
            return False

        if 'date' not in new_df.columns and new_df.index.name != 'date':
            raise ValueError(
                f"New data must contain a 'date' column or have a DateTime index to upsert feed '{feed_name}'.")

        # Load existing data
        existing_df = self.load_feed(feed_name)

        # Combine the old and new data, avoiding duplicates
        existing_df.update(new_df)

        # Find new rows to append (ensure non-empty before concatenation)
        new_rows = new_df[~new_df.index.isin(existing_df.index)]

        if not new_rows.empty:
            existing_df = pd.concat([existing_df, new_rows])


        # Save the combined data
        self.save_feed(feed_name, existing_df.drop_duplicates())
        logging.info(f"Upserted feed '{feed_name}' with {len(new_df)} new records.")
        return True
