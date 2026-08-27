from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aoic_kernel.live_prediction import LivePredictionRegistry
from aoic_kernel.models import LivePredictionStatus, TrackRecordEntry


class PublicTrackRecord:
    """Publishes a public, evidence-backed track record only for resolved predictions."""

    def __init__(self, live_predictions: LivePredictionRegistry | None = None) -> None:
        self._live_predictions = live_predictions
        self._entries: dict[str, TrackRecordEntry] = {}

    def build(
        self,
        *,
        live_predictions: LivePredictionRegistry | None = None,
        claim_template: str = "Prediction for {entity_id} resolved with {outcome}.",
        as_of: datetime | None = None,
    ) -> list[TrackRecordEntry]:
        registry = live_predictions or self._live_predictions
        if registry is None:
            raise ValueError("a LivePredictionRegistry is required")

        entries: list[TrackRecordEntry] = []
        for prediction in registry.list_released(as_of=as_of):
            if prediction.status != LivePredictionStatus.RESOLVED:
                continue
            if not prediction.evidence:
                continue
            entry = self._to_entry(prediction, claim_template)
            self._entries[entry.entry_id] = entry
            entries.append(entry)
        return entries

    @staticmethod
    def _to_entry(prediction: Any, claim_template: str) -> TrackRecordEntry:
        outcome = "hit" if _is_hit(prediction) else "miss"
        claim = claim_template.format(entity_id=prediction.entity_id, outcome=outcome)
        return TrackRecordEntry(
            entry_id=f"PTR-{uuid.uuid4().hex[:12]}",
            prediction_id=prediction.prediction_id,
            entity_id=prediction.entity_id,
            predicted_value=prediction.predicted_value,
            actual_value=prediction.actual_value,
            probability=prediction.probability,
            release_at=prediction.release_at,
            resolved_at=prediction.resolved_at or datetime.now(timezone.utc),
            evidence=prediction.evidence,
            claim=claim,
        )

    def list_entries(self) -> list[TrackRecordEntry]:
        return list(self._entries.values())


def _is_hit(prediction: Any) -> bool:
    if prediction.actual_value is None:
        return False
    try:
        return float(prediction.actual_value) >= float(prediction.predicted_value)
    except Exception:
        return prediction.actual_value == prediction.predicted_value
