# import logging
# import pandas as pd
# import os
# import datetime
# from sshtunnel import SSHTunnelForwarder
# from sqlalchemy import create_engine, text
# from sqlalchemy.types import VARCHAR
# from sqlalchemy.engine import Engine
# from mindthespread.feedstore.engines.base import FeedStoreEngine
#
#
# class SQLAlchemyFeedEngine(FeedStoreEngine):
#     def __init__(self):
#         self.ssh_tunnel = None
#         self.db_type = os.environ.get('db_type', 'mysql')  # Support for MySQL, SQLite, etc.
#         self.db_host = os.environ.get(f'{self.db_type}_host', 'localhost')
#         self.db_user = os.environ.get(f'{self.db_type}_user', '')
#         self.db_password = os.environ.get(f'{self.db_type}_password', '')
#         self.db_name = os.environ.get(f'{self.db_type}_db', 'mtsdb')
#         self.db_port = int(os.environ.get(f'{self.db_type}_port', 3306 if self.db_type == 'mysql' else 5432))
#
#         self.ssh_enabled = 'ssh_address' in os.environ
#
#         # SSH tunneling if required
#         if self.ssh_enabled:
#             self.ssh_host = os.environ['ssh_address']
#             self.ssh_username = os.environ['ssh_username']
#             self.ssh_password = os.environ['ssh_password']
#             self._create_ssh_tunnel()
#
#         # Constructing the database URL based on the selected engine
#         self.url = self._build_db_url()
#
#     def _create_ssh_tunnel(self):
#         """
#         Create an SSH tunnel if needed to access the database.
#         """
#         self.ssh_tunnel = SSHTunnelForwarder(
#             ssh_address_or_host=self.ssh_host,
#             ssh_username=self.ssh_username,
#             ssh_password=self.ssh_password,
#             remote_bind_address=(self.db_host, self.db_port)
#         )
#         self.ssh_tunnel.start()
#         self.db_host = '127.0.0.1'  # Overwrite host for tunnel
#         self.db_port = self.ssh_tunnel.local_bind_port
#         logging.info("SSH Tunnel created to access the database.")
#
#     def _build_db_url(self) -> str:
#         """
#         Build the SQLAlchemy engine URL based on environment variables.
#         """
#         if self.db_type == 'mysql':
#             return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
#         elif self.db_type == 'sqlite':
#             return f"sqlite:///{self.db_name}.db"
#         # Add more engines as needed, like PostgreSQL, etc.
#         else:
#             raise ValueError(f"Unsupported database type: {self.db_type}")
#
#     def _get_engine(self) -> Engine:
#         """
#         Create and return an SQLAlchemy engine.
#         """
#         return create_engine(self.url)
#
#     def _save_feed(self, symbol: str, freq: str, data: pd.DataFrame):
#         """
#         Save feed data into the database, creating or updating as necessary.
#         """
#         symbol = symbol.replace('/', '')
#         engine = self._get_engine()
#         table_name = f'{symbol}_{freq}'
#         dtype = {'date': VARCHAR(20)}
#
#         with engine.begin() as conn:
#             table_exists_query = text(
#                 f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table_name}'"
#             )
#             table_exists = conn.execute(table_exists_query).scalar()
#
#             if table_exists == 0:
#                 # Create new table
#                 data.to_sql(table_name, con=conn, if_exists='replace', dtype=dtype, index=False)
#             else:
#                 # Upsert logic
#                 tmp_table = f'tmp_{table_name}'
#                 data.to_sql(tmp_table, con=conn, if_exists='replace', dtype=dtype, index=False)
#
#                 # Remove duplicates from main table before inserting
#                 conn.execute(text(f"DELETE FROM {table_name} WHERE date IN (SELECT date FROM {tmp_table})"))
#                 conn.execute(text(f"INSERT INTO {table_name} SELECT * FROM {tmp_table}"))
#                 conn.execute(text(f"DROP TABLE {tmp_table}"))
#
#         logging.info(f"Feed saved: {symbol} at {freq} with {len(data)} records")
#
#     def _load_feed(self, symbol: str, freq: str, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
#         """
#         Load feed data for a symbol and frequency between the given time range.
#         """
#         symbol = symbol.replace('/', '')
#         start_str = start.isoformat()
#         end_str = end.isoformat()
#         engine = self._get_engine()
#
#         query = text(f"SELECT * FROM `{symbol}_{freq}` WHERE date >= :start AND date <= :end")
#         try:
#             with engine.connect() as conn:
#                 df = pd.read_sql(query, conn, params={'start': start_str, 'end': end_str})
#                 df.set_index('date', inplace=True)
#                 return df
#         except Exception as e:
#             logging.error(f"Error loading feed {symbol}_{freq}: {e}")
#             return pd.DataFrame()
#
#     def list_feeds(self) -> pd.DataFrame:
#         """
#         List all the available feeds in the database.
#         """
#         query = "SHOW TABLES"
#         engine = self._get_engine()
#         try:
#             with engine.connect() as conn:
#                 tables = pd.read_sql(query, conn)
#                 return tables
#         except Exception as e:
#             logging.error(f"Error listing feeds: {e}")
#             return pd.DataFrame()
#
#     def close(self):
#         """
#         Close the SSH tunnel if used.
#         """
#         if self.ssh_tunnel:
#             self.ssh_tunnel.stop()
#             logging.info("SSH Tunnel closed.")
