
feed_stores = [
    '',
    'mts.feedstore.csv.CSVFeedStore',
    'mts.feedstore.mysql.MySQLFeedStore'
]

feeds_path = 'feeds'
sample_feed_stores = [
    {
        'name': 'Sample OHLC Feeds', 'feed_type': 'OHLC',
        'engine': 'mts.feedstore.csv.CSVFeedStore',
        'engine_params': {
            'base_path': f'{feeds_path}/OHLC',
            'feed_format': '{symbol}_{freq}.csv'
        }
    },
    {
        'name': 'Sample Interest Rates', 'feed_type': 'Interest Rates', 'engine': 'mts.feedstore.csv.CSVFeedStore',
        'engine_params': {}, 'path': f'{feeds_path}/Interest Rates', 'feed_format': 'DFF.csv'
    }
]
