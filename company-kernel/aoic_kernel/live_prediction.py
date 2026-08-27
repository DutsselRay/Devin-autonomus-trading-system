from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import LivePrediction, LivePredictionStatus


class LivePredictionRegistry:
    """Sealed live predictions: released only after a declared wall-clock time."""

    def __init__(self) -> None:
        self._predictions: dict[str, LivePrediction] = {}

    def record(
        self,
        *,
        entity_id: str,
        feature_name: str,
        horizon: Any,
        predicted_value: Any,
        probability: float,
        evidence: list[str],
        release_at: datetime,
        audit_log_id: str | None = None,
    ) -> LivePrediction:
        if not evidence:
            raise ValueError("live prediction must include supporting evidence")
        prediction = LivePrediction(
            prediction_id=f"LP-{uuid.uuid4().hex[:12]}",
            entity_id=entity_id,
            feature_name=feature_name,
            horizon=horizon,
            predicted_value=predicted_value,
            probability=probability,
            evidence=evidence,
            created_at=datetime.now(timezone.utc),
            release_at=release_at,
            audit_log_id=audit_log_id,
        )
        self._predictions[prediction.prediction_id] = prediction
        return prediction

    def get(self, prediction_id: str, as_of: datetime | None = None) -> LivePrediction | None:
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            return None
        if prediction.status == LivePredictionStatus.SEALED:
            now = as_of or datetime.now(timezone.utc)
            if now < prediction.release_at:
                return None
            prediction.status = LivePredictionStatus.RELEASED
            prediction.released_at = now
        return prediction

    def list_released(self, as_of: datetime | None = None) -> list[LivePrediction]:
        now = as_of or datetime.now(timezone.utc)
        return [p for p in self._predictions.values() if p.release_at <= now]

    def list_sealed(self, as_of: datetime | None = None) -> list[LivePrediction]:
        now = as_of or datetime.now(timezone.utc)
        return [p for p in self._predictions.values() if p.release_at > now]

    def resolve(self, prediction_id: str, actual_value: Any) -> LivePrediction:
        prediction = self._get(prediction_id)
        prediction.actual_value = actual_value
        prediction.resolved_at = datetime.now(timezone.utc)
        prediction.status = LivePredictionStatus.RESOLVED
        return prediction

    def _get(self, prediction_id: str) -> LivePrediction:
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            raise KeyError(f"Unknown prediction {prediction_id}")
        return prediction
