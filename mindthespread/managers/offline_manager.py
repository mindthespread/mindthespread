import datetime
import logging
# import matplotlib
import pandas

from mindthespread.agents.base import AgentBase
from mindthespread.agents.rl import RLAgent
from mindthespread.env.trading_env import TradingEnv
from mindthespread.tracking.base import TrackingBase


# matplotlib.use('Agg')
now = datetime.datetime.utcnow().isoformat(timespec='hours')
logging.basicConfig(level=logging.INFO)


def backtest(agent: AgentBase, feed_data: pandas.DataFrame, symbol: str = None, tracker: TrackingBase = None,
             bid_col='close', ask_close='close', pip=1):

    assert feed_data is not None and len(feed_data) > 0, 'Feed data must not be empty'

    logging.info(f'Backtesting, agent {str(agent.__class__)}')

    env = TradingEnv(bid_col=bid_col, ask_col=ask_close, pip=pip)
    agent.set_env(env)

    if isinstance(agent, RLAgent):
        agent.load_rl_model()

    env.set_ohlc_feed(feed_data)
    obs, info = env.reset()
    done = False
    step = 0
    backtest_metrics = {}
    while not done:
        step += 1
        curr_idx = env.curr_idx
        agent_resp = agent.act(curr_idx, obs)
        obs, reward, done, truncated, info = env.step(agent_resp)

        backtest_metrics = {
            'total_reward': info['total_reward'],
            'win_rate': info['win_rate'],
            'closed_trans': info['closed_trans'],
        }

        if tracker is not None and tracker.log_steps:
            tracker.log_metrics(backtest_metrics, step=step)
            tracker.log_metric('step_reward', info['step_reward'], step=step)

        env.render()

    logging.info(backtest_metrics)

    # track experiment
    if tracker is not None:
        tracker.log_param('agent', str(agent.__class__))

        if agent.indicators is not None:
            indicators_names = [i.name() for i in agent.indicators]
            tracker.log_param('indicators', indicators_names)

        if symbol is not None:
            tracker.log_param('symbol', symbol)

        tracker.log_metrics(backtest_metrics)

    return backtest_metrics

def rl_train(agent: RLAgent, feed: pandas.DataFrame, tracker: TrackingBase = None):
    assert isinstance(agent, (AgentBase, RLAgent)), 'agent does not support RL'
    logging.info(f'RL Training, agent: {str(agent.__class__)}')
    env = TradingEnv()
    agent.set_env(env)
    agent.rl_train(feed)

    # todo: track RL
    return