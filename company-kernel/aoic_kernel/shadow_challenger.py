from __future__ import annotations

import inspect
import uuid
from typing import Any, Callable

from aoic_kernel.models import ShadowChallenge


class ShadowChallenger:
    """Run a challenger against the incumbent on a fixed benchmark and baseline."""

    def __init__(self, eval_engine: Any | None = None) -> None:
        self._challenges: dict[str, ShadowChallenge] = {}
        self.eval_engine = eval_engine

    def challenge(
        self,
        *,
        incumbent_id: str,
        challenger_id: str,
        benchmark_id: str,
        metric: str,
        runner: Callable[..., float],
        baseline_runner: Callable[[], float] | None = None,
        incumbent_version: str | None = None,
        challenger_version: str | None = None,
    ) -> ShadowChallenge:
        """Run the same benchmark for incumbent and challenger.

        `runner` may be `runner(agent_id)` or `runner(agent_id, version)`.
        `baseline_runner()` returns the simple baseline score.
        """
        incumbent_score = self._run_agent(incumbent_id, incumbent_version, runner)
        challenger_score = self._run_agent(challenger_id, challenger_version, runner)
        baseline_score = baseline_runner() if baseline_runner else 0.0

        scores = {
            "incumbent": incumbent_score,
            "challenger": challenger_score,
            "baseline": baseline_score,
        }
        winner = max(scores, key=scores.get)

        status_map = {
            "incumbent": "INCUMBENT_WINS",
            "challenger": "CHALLENGER_WINS",
            "baseline": "TIE",
        }
        status = status_map.get(winner, "TIE")

        challenge = ShadowChallenge(
            challenge_id=f"SC-{uuid.uuid4().hex[:12]}",
            incumbent_id=incumbent_id,
            challenger_id=challenger_id,
            benchmark_id=benchmark_id,
            metric=metric,
            incumbent_score=incumbent_score,
            challenger_score=challenger_score,
            baseline_score=baseline_score,
            winner=winner,
            status=status,
        )
        self._challenges[challenge.challenge_id] = challenge
        return challenge

    def get(self, challenge_id: str) -> ShadowChallenge | None:
        return self._challenges.get(challenge_id)

    @staticmethod
    def _run_agent(
        agent_id: str,
        version: str | None,
        runner: Callable[..., float],
    ) -> float:
        sig = inspect.signature(runner)
        if version is not None and len(sig.parameters) > 1:
            return runner(agent_id, version)
        return runner(agent_id)
