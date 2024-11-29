import logging
from datetime import datetime
from typing import Union

import pandas as pd
from google.cloud import firestore
from mindthespread.feedstore.engines.base import FeedStoreEngine


class FirestoreFeedEngine(FeedStoreEngine):
    """
    Concrete implementation of FeedStoreEngine that handles feeds using Firestore.
    Each feed (symbol+frequency) is stored in its own collection.
    """

    def __init__(self, project_id: str, database: str):
        """
        Initialize the FirestoreFeedEngine.

        :param project_id: Google Cloud project ID.
        :param database: Firestore database (e.g., 'default').
        """
        self.client = firestore.Client(project=project_id, database=database)
        logging.info(f"FirestoreFeedEngine initialized with project '{project_id}' and database '{database}'.")

    def _get_collection_ref(self, feed_name: str):
        """
        Get a reference to the Firestore collection for a specific feed.

        :param feed_name: The name of the feed (symbol+frequency).
        :return: A Firestore collection reference.
        """
        return self.client.collection(feed_name)

    def load_feed(self, feed_name: str) -> pd.DataFrame:
        """
        Load the full feed data from a Firestore collection.

        :param feed_name: The name of the feed.
        :return: A pandas DataFrame with the feed data.
        """
        collection_ref = self._get_collection_ref(feed_name)
        docs = collection_ref.stream()

        data = [doc.to_dict() for doc in docs]
        if not data:
            logging.warning(f"No data found for feed '{feed_name}'. Returning empty DataFrame.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        if 'date' not in df.columns:
            raise ValueError(f"The feed '{feed_name}' is missing a 'date' column.")

        df['date'] = pd.to_datetime(df['date'], utc=True)
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        logging.debug(f"Loaded feed '{feed_name}' with {len(df)} records.")
        return df

    def fetch_feed_by_date_range(self, feed_name: str, start_time: Union[datetime, str], end_time: Union[datetime, str]) -> pd.DataFrame:
        """
        Load a feed and filter it by the given time range.

        :param feed_name: The name of the feed.
        :param start_time: Start of the time range (datetime or ISO 8601 string).
        :param end_time: End of the time range (datetime or ISO 8601 string).
        :return: Filtered feed data as a pandas DataFrame.
        """
        data = self.load_feed(feed_name)
        if data.empty:
            return data

        start_time = pd.to_datetime(start_time, utc=True)
        end_time = pd.to_datetime(end_time, utc=True)

        filtered_data = data[(data.index >= start_time) & (data.index < end_time)]
        logging.debug(f"Fetched {len(filtered_data)} records for feed '{feed_name}' between {start_time} and {end_time}.")
        return filtered_data

    def fetch_latest(self, feed_name: str, n: int) -> pd.DataFrame:
        """
        Fetch the latest `n` records from a Firestore collection.

        :param feed_name: The name of the feed (symbol+frequency).
        :param n: The number of latest records to fetch.
        :return: A pandas DataFrame with the latest `n` records.
        """
        collection_ref = self._get_collection_ref(feed_name)

        # Query Firestore to fetch the latest `n` records, ordered by the 'date' field
        query = (
            collection_ref.order_by("date", direction=firestore.Query.DESCENDING)
            .limit(n)
            .stream()
        )

        data = [doc.to_dict() for doc in query]

        if not data:
            logging.warning(f"No data found for feed '{feed_name}'. Returning empty DataFrame.")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(data)
        if 'date' not in df.columns:
            raise ValueError(f"The feed '{feed_name}' is missing a 'date' column.")

        df['date'] = pd.to_datetime(df['date'], utc=True)
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)  # Ensure the records are in ascending order
        logging.debug(f"Fetched the latest {n} records for feed '{feed_name}'.")
        return df

    def save_feed(self, feed_name: str, data: pd.DataFrame):
        """
        Save a feed to a Firestore collection.

        :param feed_name: The name of the feed (symbol+frequency).
        :param data: DataFrame to save.
        """
        if 'date' not in data.columns and data.index.name != 'date':
            raise ValueError(f"DataFrame must contain a 'date' column or have a DateTime index to save feed '{feed_name}'.")

        if data.index.name == 'date':
            data.reset_index(inplace=True)

        collection_ref = self._get_collection_ref(feed_name)
        batch = self.client.batch()

        # Write data to Firestore collection
        for _, row in data.iterrows():
            doc_id = row['date'].isoformat()  # Use ISO 8601 date as document ID
            batch.set(collection_ref.document(doc_id), row.to_dict())

        batch.commit()
        logging.debug(f"Saved feed '{feed_name}' with {len(data)} records to Firestore.")

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

        # Ensure 'date' is part of the DataFrame and properly formatted
        if new_df.index.name == 'date':
            new_df.reset_index(inplace=True)

        collection_ref = self._get_collection_ref(feed_name)
        batch = self.client.batch()

        # Upsert each row individually
        for _, row in new_df.iterrows():
            doc_id = row['date'].isoformat()  # Use ISO 8601 date as document ID
            batch.set(collection_ref.document(doc_id), row.to_dict())

        # Commit the batch upserts
        batch.commit()
        logging.info(f"Upserted {len(new_df)} records for feed '{feed_name}'.")
        return True

