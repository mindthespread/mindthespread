from abc import ABC, abstractmethod
from datetime import datetime
from typing import Union
import pandas as pd


class FeedStoreEngine(ABC):
    """
    Abstract base class for feed engines that handle fetching and saving feed data.

    Concrete engines such as `PandasFeedEngine` or `SQLAlchemyFeedEngine`
    should extend this class and implement the abstract methods.
    """

    @abstractmethod
    def load_feed(self, feed_name: str) -> pd.DataFrame:
        """
        Load the full feed data by its name.

        Args:
            feed_name (str): The name of the feed (e.g., "EURUSD_1h").

        Returns:
            pd.DataFrame: The complete feed data as a pandas DataFrame.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError(f"load_feed method must be implemented in {self.__class__.__name__}.")

    @abstractmethod
    def fetch_feed_by_date_range(self, feed_name: str, start_time: Union[datetime, str], end_time: Union[datetime, str]) -> pd.DataFrame:
        """
        Fetch feed data within a specified date range.

        Args:
            feed_name (str): The name of the feed (e.g., "EURUSD_1h").
            start_time (Union[datetime, str]): Start of the date range as a datetime object or ISO 8601 string.
            end_time (Union[datetime, str]): End of the date range as a datetime object or ISO 8601 string.

        Returns:
            pd.DataFrame: The feed data within the specified date range.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
            ValueError: If start_time or end_time are in an invalid format.
        """
        raise NotImplementedError(f"fetch_feed_by_date_range method must be implemented in {self.__class__.__name__}.")

    @abstractmethod
    def fetch_latest(self, feed_name: str, n: int) -> pd.DataFrame:
        """
        Fetch the latest `n` records from the feed.

        Args:
            feed_name (str): The name of the feed (e.g., "EURUSD_1h").
            n (int): The number of most recent records to fetch.

        Returns:
            pd.DataFrame: The latest `n` records from the feed.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError(f"fetch_latest method must be implemented in {self.__class__.__name__}.")

    @abstractmethod
    def save_feed(self, feed_name: str, data: pd.DataFrame) -> None:
        """
        Save the feed data to the storage engine.

        Args:
            feed_name (str): The name of the feed (e.g., "EURUSD_1h").
            data (pd.DataFrame): A pandas DataFrame containing the feed data to save.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError(f"save_feed method must be implemented in {self.__class__.__name__}.")

    def upsert_feed(self, feed_name: str, data: pd.DataFrame) -> None:
        """
        Update the feed if it exists; otherwise, insert a new feed.

        Default behavior combines existing and new data while removing duplicates.

        Args:
            feed_name (str): The name of the feed (e.g., "EURUSD_1h").
            data (pd.DataFrame): A pandas DataFrame containing the feed data to upsert.

        Returns:
            None
        """
        try:
            existing_data = self.load_feed(feed_name)
            if existing_data.empty:
                self.save_feed(feed_name, data)
            else:
                updated_data = pd.concat([existing_data, data]).drop_duplicates().sort_index()
                self.save_feed(feed_name, updated_data)
        except Exception as e:
            raise RuntimeError(f"Error during upsert_feed for {feed_name}: {e}")

    def _validate_time_format(self, time_input: Union[datetime, str]) -> datetime:
        """
        Validate and convert string times to datetime objects.

        Args:
            time_input (Union[datetime, str]): A datetime object or ISO 8601 string.

        Returns:
            datetime: A validated datetime object.

        Raises:
            ValueError: If the input cannot be converted to a valid datetime object.
        """
        if isinstance(time_input, datetime):
            return time_input
        try:
            return datetime.fromisoformat(time_input)
        except ValueError as e:
            raise ValueError(f"Invalid date format: {time_input}. Expected datetime object or ISO 8601 string. Error: {e}")

    def _validate_feed_data(self, data: pd.DataFrame, required_columns: list) -> None:
        """
        Validate feed data to ensure required columns are present.

        Args:
            data (pd.DataFrame): The feed data as a pandas DataFrame.
            required_columns (list): List of required column names.

        Raises:
            ValueError: If any required columns are missing.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Feed data must be a pandas DataFrame.")
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in feed data: {', '.join(missing_columns)}")
