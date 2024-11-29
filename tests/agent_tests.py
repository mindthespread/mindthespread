import unittest
from datetime import datetime
import logging

from mindthespread.agents.rl import RLAgent
from mindthespread.feedstore.feeds.ohlc_feed import OHLCFeed
from mindthespread.feedstore.engines.pandas import PandasFeedEngine
from mindthespread.managers.offline_manager import backtest, rl_train
from mindthespread.tracking.mlflow import MLFlowWrapper
from mindthespread.agents.crossover import AgentCrossover
from mindthespread.ta import oscillators

beginning_of_times = '2000-01-01'
cutoff = '2024-01-01'
now = datetime.now()


class PrebuiltAgentsTests(unittest.TestCase):

    def setUp(self):
        # setup logging
        logging.basicConfig(level=logging.INFO)
        logging.info('setUp')

        # Initialize the Pandas feed engine and load the feed
        base_path = 'feeds/forex_hourly/'
        pandas_engine = PandasFeedEngine(base_path=base_path)
        self.EURUSD_feed = OHLCFeed(feed_name="CS.D.EURUSD.CFD.IP_1h", feedstore_engine=pandas_engine, feed_format="{symbol}_{freq}")
        self.GBPUSD_feed = OHLCFeed(feed_name="CS.D.GBPUSD.CFD.IP_1h", feedstore_engine=pandas_engine, feed_format="{symbol}_{freq}")

    def test_agent_crossover_backtest(self):
        logging.info('test_agent_crossover_backtest - start')
        with MLFlowWrapper(experiment_group="mindthespread_tests", log_steps=True) as tracker:
            # Initialize the agent
            agent = AgentCrossover(sma_long=50, sma_short=20)

            # fetch data
            self.EURUSD_feed.fetch_by_date_range(cutoff, now)
            self.assertIsNotNone(self.EURUSD_feed.data, 'data not fetched')

            # backtest
            backtest_results = backtest(agent, self.EURUSD_feed.data, tracker=tracker)
            self.assertTrue(isinstance(backtest_results, dict), "AgentCrossover backtest failed")

    def test_agent_rl_training_and_backtest(self):
        logging.info('test_agent_rl_training_and_backtest - start')
        with MLFlowWrapper("mindthespread_tests") as tracker:

            # RL Learn
            agent = RLAgent(rl_model_path='models/tests.rl.model', total_timesteps=500000, indicators=oscillators())
            learn_feed = self.EURUSD_feed.fetch_by_date_range(beginning_of_times, cutoff)
            rl_train(agent=agent, feed=learn_feed.data, tracker=tracker)

            # backtest
            agent.reset()
            self.EURUSD_feed.fetch_by_date_range(cutoff, now)
            test_feed_data = self.EURUSD_feed.data
            backtest_results = backtest(agent, test_feed_data, tracker=tracker)

            self.assertGreater(backtest_results['win_rate'], 0, 'Backtest win rate below threshold')


    def tearDown(self):
        logging.info('tearDown')


if __name__ == '__main__':
    unittest.main()
