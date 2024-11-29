from typing import Dict, Any
import mlflow

from mindthespread.tracking.base import TrackingBase

class MLFlowWrapper(TrackingBase):
    def __init__(self, experiment_group='mindthespread', log_steps=True):
        super().__init__(experiment_group, log_steps)

    def start_run(self, experiment_group):
        mlflow.set_experiment(experiment_group)
        mlflow.start_run()

    def end_run(self):
        mlflow.end_run()

    def log_param(self, key: str, value: Any):
        mlflow.log_param(key, value)

    def log_params(self, params: Dict):
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict, step: int | None = None):
        mlflow.log_metrics(metrics=metrics, step=step)

    def log_metric(self, key: str, value: float, step: int | None = None):
        mlflow.log_metric(key=key, value=value, step=step)