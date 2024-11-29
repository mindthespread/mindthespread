# import logging
# import argparse
# from datetime import datetime, timedelta
# from mindthespread.managers.data_manager import DataManager
#
#
# def main():
#     parser = argparse.ArgumentParser(prog='Mind The Spread Data Sync')
#     parser.add_argument('-broker', default='mts.brokers.ig.IGBroker')
#     parser.add_argument('-store', default='mts.featurestore.csv.Csv')
#     parser.add_argument('-symbol', default="CS.D.NEOUSD.CFD.IP")
#     parser.add_argument('-freq', default="1h")
#     parser.add_argument('-start', default=datetime.utcnow()-timedelta(days=365))
#
#     args = parser.parse_args()
#     data_mgr = DataManager(broker_cls=args.broker, store_cls=args.store)
#     data_mgr.sync(symbol=args.symbol, freq=args.freq, start=args.start, end=args.end)
#
#
# if __name__ == '__main__':
#     main()
