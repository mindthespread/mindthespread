from functools import wraps
from typing import Dict
import pandas

def obs_to_pandas(method):
    @wraps(method)
    def _impl(self, curr_idx, obs: Dict):
        obs_dict = {
            'position': obs['position']
        }

        if 'signals' in obs:
            obs_dict['signals'] = pandas.Series(data=obs['signals'], index=self.cols)

        return method(self, curr_idx, obs_dict)

    return _impl