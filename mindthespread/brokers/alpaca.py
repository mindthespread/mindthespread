# import datetime
# import logging
# import os
#
# import alpaca.common.exceptions
# from alpaca.data import StockHistoricalDataClient, CryptoHistoricalDataClient
# from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
# from alpaca.data.timeframe import TimeFrame
# from alpaca.data.enums import Adjustment, CryptoFeed
# from alpaca.trading.client import TradingClient
# from alpaca.trading.requests import MarketOrderRequest
# from alpaca.trading.enums import OrderSide, TimeInForce, PositionSide, OrderStatus
# from mts.models import Action, Position, Direction
# from mts.broker import CandlesFeedBroker, MarketBroker
# import requests
#
#
# class AlpacaBroker(CandlesFeedBroker, MarketBroker):
#     def __init__(self):
#         super().__init__()
#         api_key = os.environ['ALPACA_API_KEY']
#         secret_key = os.environ['ALPACA_SECRET_KEY']
#         self.is_paper = True
#         self.stock_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
#         self.crypto_client = CryptoHistoricalDataClient(api_key=api_key, secret_key=secret_key)
#         self.trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=self.is_paper)
#
#     def enter_position(self, symbol: str, action: Action, qty: float):
#         side = None
#         if action == Action.BUY:
#             side = OrderSide.BUY
#         elif action == Action.SELL:
#             side = OrderSide.SELL
#         else:
#             raise Exception(f'invalid action {action}')
#
#         pos = None
#         try:
#             market_order_data = MarketOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.IOC)
#             market_order = self.trading_client.submit_order(order_data=market_order_data)
#
#             if market_order.status in [OrderStatus.NEW, OrderStatus.PENDING_NEW, OrderStatus.ACCEPTED]:
#                 entry_price = market_order.filled_avg_price
#                 direction = Direction.Long if action == Action.BUY else Direction.Short
#                 pos = Position(symbol=symbol, entry_price=entry_price, qty=qty, direction=direction)
#                 logging.info(f'symbol:{symbol} qty:{qty} action:{action.name} price:{entry_price} order submitted. status: {market_order.status}')
#             else:
#                 logging.warning(f'failed to enter position symbol:{symbol} status:{market_order.status}')
#         except alpaca.common.exceptions.APIError as ex:
#             logging.warning(ex)
#         finally:
#             return pos
#
#     def close_position(self, symbol: str):
#         try:
#             symbol = symbol.replace('/', '')
#             order = self.trading_client.close_position(symbol_or_asset_id=symbol)
#             if order.status == OrderStatus.ACCEPTED:
#                 logging.info(f'symbol {symbol}, position closed: {order}')
#                 return Position(symbol=symbol, direction=Direction.Out)
#             else:
#                 logging.warning(f'closing order failed symbol:{symbol}')
#         except Exception as ex:
#             logging.warning(ex)
#
#     def get_candles(self, symbol, freq, start: datetime.datetime, end: datetime.datetime, market='stocks'):
#         assert freq in (['T', 'min', 'H', 'D', 'W', 'M']), f'unknown freq {freq}'
#         timeframe = TimeFrame.Minute if freq in (['T', 'min']) \
#             else TimeFrame.Hour if freq == 'H' \
#             else TimeFrame.Day if freq == 'D' \
#             else TimeFrame.Week if freq == 'W' \
#             else TimeFrame.Month if freq == 'M' \
#             else None
#
#         if self.is_paper:
#             end = min(end, datetime.datetime.utcnow() - datetime.timedelta(minutes=30))
#
#         df = None
#         try:
#             if market == 'stocks':
#                 request_params = StockBarsRequest(symbol_or_symbols=[symbol], timeframe=timeframe, start=start, end=end,
#                                                   adjustment=Adjustment.ALL)
#                 res = self.stock_client.get_stock_bars(request_params)
#             elif market == 'crypto':
#                 request_params = CryptoBarsRequest(symbol_or_symbols=[symbol], timeframe=timeframe, start=start, end=end,
#                                                    feed='us')
#                 res = self.crypto_client.get_crypto_bars(request_params, feed='us')
#             else:
#                 raise Exception(f'unknown market {market}')
#
#             if len(res.data) > 0:
#                 df = res.df.reset_index().rename(columns={'timestamp': 'date'})
#                 df = df.set_index('date')
#             else:
#                 logging.warning(f'No data returned for symbol:{symbol}, freq:{freq}')
#         except requests.exceptions.ConnectionError as ex:
#             logging.error(ex)
#         finally:
#             return df
#
#     def get_position(self, symbol: str):
#         symbol = symbol.replace('/', '')
#         pos = Position(symbol=symbol)
#         try:
#             alpaca_pos = self.trading_client.get_open_position(symbol)
#             direction = Direction.Long if alpaca_pos.side == PositionSide.LONG else Direction.Short
#             qty = alpaca_pos.qty
#             pos = Position(symbol=symbol, entry_price=float(alpaca_pos.avg_entry_price),
#                            qty=float(qty), direction=direction)
#         except alpaca.common.exceptions.APIError as ex:
#             if ex.code != 40410000:  # not position does not exist
#                 logging.exception(ex)
#         except Exception as ex:
#             logging.error(ex)
#         finally:
#             return pos
