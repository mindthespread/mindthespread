from abc import ABC, abstractmethod
from typing import Any, Dict


class TrackingBase(ABC):
    def __init__(self, experiment_group: str, log_steps: bool):
        self.experiment_group = experiment_group
        self.log_steps = log_steps

    def __enter__(self):
        self.start_run(self.experiment_group)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_run()
        # Returning False ensures exceptions are re-raised
        return False

    @abstractmethod
    def start_run(self, experiment_group):
        raise NotImplementedError

    @abstractmethod
    def end_run(self):
        raise NotImplementedError

    @abstractmethod
    def log_param(self, key: str, value: Any):
        raise NotImplementedError

    @abstractmethod
    def log_params(self, params: Dict):
        raise NotImplementedError

    @abstractmethod
    def log_metrics(self, metrics: Dict, step: int | None):
        raise NotImplementedError

    @abstractmethod
    def log_metric(self, key: str, value: float, step: int | None):
        raise NotImplementedError