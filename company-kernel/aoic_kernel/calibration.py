from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import CalibrationRun


class CalibrationEngine:
    """Versioned calibration pipeline for probabilities."""

    MIN_SAMPLE_SIZE = 30

    def __init__(self, min_sample_size: int = 30) -> None:
        self.min_sample_size = min_sample_size
        self._runs: dict[str, CalibrationRun] = {}

    def fit(
        self,
        calibration_id: str,
        model_version: str,
        scores: list[tuple[float, float]],
    ) -> CalibrationRun:
        """Fit calibration on (predicted_probability, observed_outcome) pairs."""
        run = CalibrationRun(
            calibration_id=calibration_id,
            model_version=model_version,
            fitted_at=datetime.now(timezone.utc),
            scores=scores,
        )

        if len(scores) < self.min_sample_size:
            run.status = "INSUFFICIENT"
            run.brier_score = None
            run.expected_calibration_error = None
            run.log_loss = None
        else:
            probs = [p for p, _ in scores]
            outcomes = [o for _, o in scores]

            run.brier_score = self._brier(probs, outcomes)
            run.log_loss = self._log_loss(probs, outcomes)
            run.expected_calibration_error = self._expected_calibration_error(
                probs, outcomes
            )
            run.status = "VALID"

        self._runs[calibration_id] = run
        return run

    def get(self, calibration_id: str) -> CalibrationRun | None:
        return self._runs.get(calibration_id)

    def calibrate(
        self,
        raw_probability: float,
        calibration_id: str,
    ) -> tuple[float, dict[str, Any]]:
        """Return a calibrated probability and metadata; may widen or abstain."""
        run = self._runs.get(calibration_id)
        if run is None:
            return 0.0, {"abstain": True, "reason": "missing calibration run"}

        if run.status == "INSUFFICIENT":
            return raw_probability, {
                "abstain": True,
                "reason": f"insufficient samples ({len(run.scores)} < {self.min_sample_size})",
            }

        if run.status == "DRIFT":
            return max(0.0, raw_probability - 0.1), {
                "abstain": True,
                "reason": "calibration drift detected",
            }

        # Simple isotonic-style recalibration: shrink toward base rate.
        base_rate = sum(o for _, o in run.scores) / len(run.scores)
        calibrated = 0.5 * raw_probability + 0.5 * base_rate
        return calibrated, {
            "brier_score": run.brier_score,
            "expected_calibration_error": run.expected_calibration_error,
            "log_loss": run.log_loss,
            "abstain": False,
        }

    def mark_drift(self, calibration_id: str) -> CalibrationRun:
        run = self._get_or_raise(calibration_id)
        run.status = "DRIFT"
        return run

    @staticmethod
    def _brier(probs: list[float], outcomes: list[float]) -> float:
        return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)

    @staticmethod
    def _log_loss(probs: list[float], outcomes: list[float]) -> float:
        eps = 1e-9
        total = 0.0
        for p, o in zip(probs, outcomes):
            p = max(eps, min(1 - eps, p))
            total += -(o * math.log(p) + (1 - o) * math.log(1 - p))
        return total / len(probs)

    @staticmethod
    def _expected_calibration_error(
        probs: list[float], outcomes: list[float], n_bins: int = 10
    ) -> float:
        if not probs:
            return 0.0
        bin_edges = [i / n_bins for i in range(n_bins + 1)]
        ece = 0.0
        for low, high in zip(bin_edges[:-1], bin_edges[1:]):
            indices = [
                i for i, p in enumerate(probs) if low <= p < high or (high == 1.0 and p == 1.0)
            ]
            if not indices:
                continue
            bin_acc = sum(outcomes[i] for i in indices) / len(indices)
            bin_conf = sum(probs[i] for i in indices) / len(indices)
            ece += abs(bin_acc - bin_conf) * (len(indices) / len(probs))
        return ece

    def _get_or_raise(self, calibration_id: str) -> CalibrationRun:
        run = self._runs.get(calibration_id)
        if run is None:
            raise KeyError(f"Unknown calibration run {calibration_id}")
        return run
