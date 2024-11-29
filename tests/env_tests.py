import unittest
import pandas as pd
from unittest.mock import MagicMock
from mindthespread.entities.agent import AgentResponse
from mindthespread.entities.market import Action, Direction
from mindthespread.env.trading_env import TradingEnv


class TestTradingEnv(unittest.TestCase):

    def setUp(self):
        """Set up the environment with mock data for testing."""
        # Create a sample feed for the tests
        data = {
            'bidclose': [1.1000, 1.1010, 1.1020, 1.1030, 1.1040],
            'askclose': [1.1005, 1.1015, 1.1025, 1.1035, 1.1045]
        }
        self.feed_data = pd.DataFrame(data, index=pd.date_range('2023-01-01', periods=5, freq='h'))

        # Initialize the environment
        self.env = TradingEnv(episode_window=5, batch_window=1, bid_col='bidclose', ask_col='askclose', symbol="EURUSD")

        # Mock the calc_signals method to return valid signals for testing
        self.env.calc_signals = MagicMock(return_value=self.feed_data)
        self.env.set_ohlc_feed(self.feed_data)

    def test_initial_state(self):
        """Test the initial state of the environment."""
        self.assertIsNone(self.env.position)
        self.assertEqual(self.env.total_reward, 0)
        self.assertEqual(self.env.closed_transactions, 0)
        self.assertIsNotNone(self.env.action_space)
        self.assertIsNotNone(self.env.observation_space)

    def test_enter_long_position(self):
        """Test entering a long position (BUY action)."""
        agent_resp = AgentResponse(action=Action.BUY, qty=1, stop_loss=0.001)
        obs, reward, done, truncated, info = self.env.step(agent_resp)

        self.assertIsNotNone(self.env.position)
        self.assertEqual(self.env.position.direction, Direction.Long)
        self.assertEqual(self.env.position.entry_price, 1.1005)
        self.assertFalse(done)

    def test_enter_short_position(self):
        """Test entering a short position (SELL action)."""
        agent_resp = AgentResponse(action=Action.SELL, qty=1, stop_loss=0.001)
        obs, reward, done, truncated, info = self.env.step(agent_resp)

        self.assertIsNotNone(self.env.position)
        self.assertEqual(self.env.position.direction, Direction.Short)
        self.assertEqual(self.env.position.entry_price, 1.1000)
        self.assertFalse(done)

    def test_close_position(self):
        """Test closing an open position."""
        # Enter a long position
        agent_resp = AgentResponse(action=Action.BUY, qty=1, stop_loss=0.001)
        self.env.step(agent_resp)
        self.assertIsNotNone(self.env.position)

        # Now close the position
        close_resp = AgentResponse(action=Action.CLOSE)
        obs, reward, done, truncated, info = self.env.step(close_resp)

        self.assertIsNone(self.env.position)
        self.assertEqual(self.env.closed_transactions, 1)
        self.assertFalse(done)

    def test_stop_loss(self):
        """Test stop-loss functionality during a step."""
        # Enter a long position with a stop-loss
        agent_resp = AgentResponse(action=Action.BUY, qty=1, stop_loss=0.001)
        self.env.step(agent_resp)

        # Simulate a step where the stop-loss is hit
        self.env.feed.loc[self.env.curr_idx, 'bidclose'] = 1.0990  # Price drops below stop-loss
        obs, reward, done, truncated, info = self.env.step(agent_resp)

        self.assertIsNone(self.env.position)
        self.assertEqual(info['action'], 'CLOSE')
        self.assertTrue(info['stop'])

    def test_step_rewards(self):
        """Test step reward calculation in long and short positions."""
        # Enter a long position
        agent_resp = AgentResponse(action=Action.BUY, qty=1, stop_loss=0.001)
        self.env.step(agent_resp)
        self.env.feed.loc[self.env.curr_idx, 'bidclose'] = 1.1010  # Price moves up
        obs, reward, done, truncated, info = self.env.step(agent_resp)

        self.assertGreater(self.env.transaction_reward, 0)
        self.assertFalse(done)

        # Close the position
        self.env.step(AgentResponse(action=Action.CLOSE))
        self.assertIsNone(self.env.position)

    def test_reset(self):
        """Test resetting the environment."""
        self.env.reset()
        self.assertIsNone(self.env.position)
        self.assertEqual(self.env.total_reward, 0)
        self.assertEqual(self.env.step_count, 0)
        self.assertIsNotNone(self.env.obs)




if __name__ == '__main__':
    unittest.main()
