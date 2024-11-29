import dateutil.parser
import pandas as pd
import requests
import datetime
import logging
import os
import json
import uuid

from mindthespread.brokers.broker import OHLCBroker, MarketBroker
from mindthespread.entities.market import Action, Position, Direction


class IGBroker(OHLCBroker, MarketBroker):
    """
    IG Broker implementation for interacting with the IG API.

    Supports OHLC data retrieval, market operations, and account management.
    """

    BASE_URL_TEMPLATE = 'https://{0}api.ig.com/gateway/deal'
    MAX_LEN = 3000
    TIMEZONE_OFFSET = 8  # Configurable timezone offset

    def __init__(self):
        """
        Initialize the broker instance and authenticate with the IG API.

        Determines whether to use demo or production credentials based on
        the `IG_PROD` environment variable.
        """
        self.is_demo = not os.environ.get('IG_PROD')
        self.url = self.BASE_URL_TEMPLATE.format('demo-' if self.is_demo else '')

        # Load credentials
        env_prefix = 'DEMO' if self.is_demo else 'PROD'
        self.api_key = os.getenv(f'IG_API_KEY_{env_prefix}')
        self.identifier = os.getenv(f'IG_IDENTIFIER_{env_prefix}')
        self.password = os.getenv(f'IG_PASSWORD_{env_prefix}')
        if not all([self.api_key, self.identifier, self.password]):
            raise EnvironmentError(f"Missing credentials for IG {env_prefix} environment.")

        self.granularity_map = {'1m': 'MINUTE', '1h': 'HOUR', '1d': 'DAY'}
        self.connected = False
        self.auth = None
        self.refresh_token = None
        self.connected_time = None

    def is_connected(self) -> bool:
        """Check if the broker is currently connected."""
        return self.connected

    def build_headers(self, version: str) -> dict:
        """
        Build the required HTTP headers for API requests.

        Args:
            version (str): The API version to use.

        Returns:
            dict: The headers for the API request.
        """
        headers = {
            'X-IG-API-KEY': self.api_key,
            'version': version,
            'Content-Type': 'application/json; charset=UTF-8'
        }
        if self.auth:
            headers.update({
                'CST': self.auth['CST'],
                'X-SECURITY-TOKEN': self.auth['X-SECURITY-TOKEN']
            })
        return headers

    def connect(self) -> bool:
        """
        Connect to the IG API by authenticating the session.

        Returns:
            bool: True if the connection is successful, False otherwise.

        Raises:
            Exception: If authentication fails.
        """
        logging.debug('Connecting to IG API...')
        if self.connected and (datetime.datetime.now() - self.connected_time).total_seconds() < 60:
            return True

        payload = json.dumps({'identifier': self.identifier, 'password': self.password})
        headers = self.build_headers(version="2")
        response = requests.post(f'{self.url}/session', headers=headers, data=payload)

        if response.status_code == 200:
            self.connected_time = datetime.datetime.now()
            self.auth = {
                'X-SECURITY-TOKEN': response.headers['X-SECURITY-TOKEN'],
                'CST': response.headers['CST']
            }
            self.refresh_token = json.loads(response.content)
            self.connected = True
            logging.info('Successfully connected to IG API.')
            return True
        else:
            logging.error(f"Failed to connect to IG API: {response.text}")
            raise Exception(response.text)

    def get_candles(self, symbol: str, freq: str, start: datetime.datetime = None, end: datetime.datetime = None):
        """
        Retrieve OHLC candle data for a given symbol and timeframe.

        Args:
            symbol (str): The market symbol (e.g., CS.D.EURUSD.CFD.IP).
            freq (str): Frequency of candles (e.g., '1m', '1h', '1d').
            start (datetime.datetime): Start time for data retrieval.
            end (datetime.datetime): End time for data retrieval.

        Returns:
            pandas.DataFrame: A DataFrame containing OHLC data, or None if no data is available.
        """
        assert symbol, "Symbol must be provided."
        assert freq, "Frequency must be provided."
        assert start or end, "At least one of start or end must be provided."

        if isinstance(start, str):
            start = dateutil.parser.isoparse(start)
        if isinstance(end, str):
            end = dateutil.parser.isoparse(end)

        self.connect()
        headers = self.build_headers(version="3")
        resolution = self.granularity_map.get(freq)
        if not resolution:
            raise ValueError(f"Unsupported frequency: {freq}")

        if start is None:
            start = end - datetime.timedelta(hours=self.MAX_LEN) if resolution == 'HOUR' else None
        if end is None:
            end = start + datetime.timedelta(hours=self.MAX_LEN) if resolution == 'HOUR' else datetime.datetime.now(datetime.UTC)

        # Adjust for timezone
        start = (start + datetime.timedelta(hours=self.TIMEZONE_OFFSET)).isoformat(timespec='seconds')
        end = (end + datetime.timedelta(hours=self.TIMEZONE_OFFSET)).isoformat(timespec='seconds')

        params = {'resolution': resolution, 'from': start, 'to': end, 'pageSize': 0}
        try:
            response = requests.get(f'{self.url}/prices/{symbol}', headers=headers, params=params)
            response.raise_for_status()
            data = response.json().get('prices', [])
            if not data:
                logging.warning(f"No data returned for {symbol} with frequency {freq}.")
                return None

            df = pd.DataFrame([
                {
                    'bidopen': p['openPrice']['bid'],
                    'bidclose': p['closePrice']['bid'],
                    'bidhigh': p['highPrice']['bid'],
                    'bidlow': p['lowPrice']['bid'],
                    'askopen': p['openPrice']['ask'],
                    'askclose': p['closePrice']['ask'],
                    'askhigh': p['highPrice']['ask'],
                    'asklow': p['lowPrice']['ask'],
                    'volume': p['lastTradedVolume'],
                    'date': p['snapshotTimeUTC']
                }
                for p in data
            ])
            df['date'] = pd.to_datetime(df['date'], utc=True)
            df.set_index('date', inplace=True)
            df['open'] = (df['askopen'] + df['bidopen']) / 2
            df['close'] = (df['askclose'] + df['bidclose']) / 2
            df['high'] = (df['askhigh'] + df['bidhigh']) / 2
            df['low'] = (df['asklow'] + df['bidlow']) / 2
            return df
        except Exception as e:
            logging.error(f"Error retrieving candles: {e}")
            return None

    # Other methods (`buy`, `close`, etc.) can be similarly refactored.
