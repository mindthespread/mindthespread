import joblib
from typing import List
import pandas

from mindthespread.ta import TABase
from mindthespread.agents.base import AgentBase
from mindthespread.entities.agent import AgentResponse


class DummyStableBaseline3Model:
    def __init__(self, env, policy, verbose):
        self.env = env

    def learn(self, total_timesteps):
        pass

    def save(self, path):
        joblib.dump(self, path)

    @staticmethod
    def load(path):
        return joblib.load(path)

    def predict(self, obs):
        return self.env.action_space.sample(), None

class RLAgent(AgentBase):
    def __init__(self, rl_model_path: str, rl_algo=DummyStableBaseline3Model, total_timesteps: int = None, policy: str = "MultiInputPolicy",
                 min_records_needed=1000, indicators: List[TABase] = None): # agent params
        super().__init__(min_records_needed=min_records_needed, indicators=indicators)

        self.rl_model_path = rl_model_path
        self.rl_algo = rl_algo
        self.total_timesteps = total_timesteps
        self.policy = policy
        self.rl_model = None

    def load_rl_model(self) -> None:
        self.rl_model = self.rl_algo.load(self.rl_model_path)

    def rl_train(self, feed: pandas.DataFrame):
        self.env.set_ohlc_feed(feed)
        rl_agent = self.rl_algo(env=self.env, policy=self.policy, verbose=2)
        rl_agent.learn(total_timesteps=self.total_timesteps)
        rl_agent.save(self.rl_model_path)

    def act(self, curr_idx, obs) -> AgentResponse:
        action, _states = self.rl_model.predict(obs)
        return AgentResponse(action=action)
