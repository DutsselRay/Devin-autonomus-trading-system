from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.models import Experiment, ExperimentStatus
from aoic_kernel.oosset import SealedOOSSetManager


class ExperimentRegistry:
    """Preregistered experiments with sealed holdout and contamination tracking."""

    def __init__(self, oos_manager: SealedOOSSetManager | None = None) -> None:
        self._experiments: dict[str, Experiment] = {}
        self.oos_manager = oos_manager or SealedOOSSetManager()

    def preregister(self, experiment: Experiment) -> None:
        self._experiments[experiment.experiment_id] = experiment

    def get(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def start(self, experiment_id: str) -> Experiment:
        experiment = self._get_or_raise(experiment_id)
        if experiment.status != ExperimentStatus.PREREGISTERED:
            raise ValueError(f"Cannot start experiment in state {experiment.status}")
        experiment.status = ExperimentStatus.RUNNING
        return experiment

    def seal_oos(self, experiment_id: str, oos_set_id: str) -> Experiment:
        experiment = self._get_or_raise(experiment_id)
        if self.oos_manager.get(oos_set_id) is None:
            raise ValueError(f"Unknown OOS set {oos_set_id}")
        experiment.oos_set_id = oos_set_id
        experiment.status = ExperimentStatus.SEALED_OOS
        return experiment

    def complete(self, experiment_id: str, backtest_id: str) -> Experiment:
        experiment = self._get_or_raise(experiment_id)
        experiment.status = ExperimentStatus.COMPLETED
        experiment.backtest_id = backtest_id
        return experiment

    def fail(self, experiment_id: str, reason: str) -> Experiment:
        experiment = self._get_or_raise(experiment_id)
        experiment.status = ExperimentStatus.FAILED
        experiment.contamination_log.append(f"failed: {reason}")
        return experiment

    def log_contamination(
        self, experiment_id: str, agent_id: str, reason: str
    ) -> None:
        experiment = self._get_or_raise(experiment_id)
        experiment.contamination_log.append(f"{agent_id}: {reason}")
        if experiment.oos_set_id:
            self.oos_manager.mark_contaminated(
                experiment.oos_set_id, agent_id, reason
            )

    def _get_or_raise(self, experiment_id: str) -> Experiment:
        experiment = self._experiments.get(experiment_id)
        if experiment is None:
            raise KeyError(f"Unknown experiment {experiment_id}")
        return experiment

    def snapshot(self) -> dict[str, Any]:
        return {
            eid: exp.model_dump() for eid, exp in self._experiments.items()
        }
