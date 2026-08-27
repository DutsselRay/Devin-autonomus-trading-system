from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.models import FeatureRecord


class TemporalFeatureStore:
    """Event/delta storage for PIT features with explicit availability semantics."""

    def __init__(self) -> None:
        self._records: list[FeatureRecord] = []

    def store(self, record: FeatureRecord) -> None:
        self._records.append(record)

    def get(self, entity_id: str, feature_name: str, as_of: datetime) -> FeatureRecord | None:
        candidate: FeatureRecord | None = None
        for record in self._records:
            if record.entity_id == entity_id and record.feature_name == feature_name and record.is_available_at(as_of):
                key = (record.valid_from, record.released_at, record.ingested_at)
                if candidate is None or key > (
                    candidate.valid_from,
                    candidate.released_at,
                    candidate.ingested_at,
                ):
                    candidate = record
        return candidate

    def _record_key(self, record: FeatureRecord) -> tuple:
        return (record.valid_from, record.released_at, record.ingested_at)

    def get_features(self, entity_id: str, as_of: datetime) -> dict[str, Any]:
        latest: dict[str, FeatureRecord] = {}
        for record in self._records:
            if record.entity_id == entity_id and record.is_available_at(as_of):
                prev = latest.get(record.feature_name)
                if prev is None or self._record_key(record) > self._record_key(prev):
                    latest[record.feature_name] = record
        return {name: rec.value for name, rec in latest.items()}

    def series(
        self,
        entity_id: str,
        feature_name: str,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, Any]]:
        points = [
            (record.event_time, record.value)
            for record in self._records
            if (
                record.entity_id == entity_id
                and record.feature_name == feature_name
                and start <= record.event_time <= end
                and record.is_available_at(end)
            )
        ]
        return sorted(points, key=lambda p: p[0])
