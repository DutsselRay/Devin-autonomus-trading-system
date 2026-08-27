from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from aoic_kernel.models import CanaryRun, RollbackRecord


class CanaryRollback:
    """Staged canary deployment with acceptance criteria and automatic rollback."""

    def __init__(self) -> None:
        self._canaries: dict[str, CanaryRun] = {}
        self._rollbacks: list[RollbackRecord] = []

    def start_canary(
        self,
        agent_id: str,
        previous_version: str | None,
        scope: str,
        acceptance_criteria: dict[str, Any],
    ) -> CanaryRun:
        run = CanaryRun(
            run_id=f"CAN-{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            previous_version=previous_version,
            scope=scope,
            start_time=datetime.now(timezone.utc),
            acceptance_criteria=acceptance_criteria,
            status="RUNNING",
        )
        self._canaries[run.run_id] = run
        return run

    def evaluate_canary(
        self,
        run_id: str,
        metrics: dict[str, Any],
        eval_fn: Callable[[dict[str, Any], dict[str, Any]], bool] | None = None,
    ) -> CanaryRun:
        run = self._get_canary(run_id)
        run.metrics = metrics
        run.end_time = datetime.now(timezone.utc)

        if eval_fn is None:
            passed = self._default_eval(run.acceptance_criteria, metrics)
        else:
            passed = eval_fn(run.acceptance_criteria, metrics)

        run.status = "PASSED" if passed else "FAILED"
        return run

    def rollback(
        self,
        agent_id: str,
        new_version: str,
        previous_version: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> RollbackRecord:
        record = RollbackRecord(
            rollback_id=f"RB-{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            triggered_at=datetime.now(timezone.utc),
            reason=reason,
            previous_version=previous_version,
            new_version=new_version,
            details=details or {},
        )
        self._rollbacks.append(record)
        return record

    def get_canary(self, run_id: str) -> CanaryRun | None:
        return self._canaries.get(run_id)

    def list_rollbacks(self, agent_id: str | None = None) -> list[RollbackRecord]:
        if agent_id is None:
            return list(self._rollbacks)
        return [r for r in self._rollbacks if r.agent_id == agent_id]

    @staticmethod
    def _default_eval(criteria: dict[str, Any], metrics: dict[str, Any]) -> bool:
        for key, threshold in criteria.items():
            if key not in metrics:
                return False
            value = metrics[key]
            if isinstance(value, (int, float)) and isinstance(threshold, (int, float)):
                if value < threshold:
                    return False
        return True

    def _get_canary(self, run_id: str) -> CanaryRun:
        run = self._canaries.get(run_id)
        if run is None:
            raise KeyError(f"Unknown canary run {run_id}")
        return run
