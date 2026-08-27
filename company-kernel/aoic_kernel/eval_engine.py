from __future__ import annotations

from typing import Any


class EvalEngine:
    """Offline, shadow, canary and production metrics."""

    def __init__(self) -> None:
        self._evals: dict[str, dict[str, Any]] = {}

    def register_baseline(self, eval_id: str, threshold: float) -> None:
        self._evals[eval_id] = {"threshold": threshold, "results": []}

    def record(self, eval_id: str, value: float, metadata: dict[str, Any] | None = None) -> bool:
        if eval_id not in self._evals:
            self._evals[eval_id] = {"threshold": None, "results": []}
        self._evals[eval_id]["results"].append({"value": value, "metadata": metadata or {}})
        if self._evals[eval_id]["threshold"] is not None:
            return value >= self._evals[eval_id]["threshold"]
        return True

    def passed(self, eval_id: str) -> bool:
        threshold = self._evals[eval_id].get("threshold")
        if threshold is None:
            return True
        return all(r["value"] >= threshold for r in self._evals[eval_id]["results"])
