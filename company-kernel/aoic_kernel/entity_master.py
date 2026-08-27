from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.models import Entity, PITRecord


class EntityMaster:
    """Registry of entities with listing/delisting and PIT fact lineage."""

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._pit_records: list[PITRecord] = []

    def register(self, entity: Entity) -> None:
        self._entities[entity.entity_id] = entity

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def list_active(self, as_of: datetime) -> list[Entity]:
        return [e for e in self._entities.values() if e.is_active_as_of(as_of)]

    def ingest(self, record: PITRecord) -> None:
        self._pit_records.append(record)

    def pit_history(
        self, entity_id: str, as_of: datetime | None = None
    ) -> list[PITRecord]:
        records = [r for r in self._pit_records if r.entity_id == entity_id]
        if as_of is not None:
            records = [r for r in records if r.is_available_at(as_of)]
        return sorted(records, key=lambda r: r.event_time)

    def snapshot(self) -> dict[str, Any]:
        return {
            "entities": [e.model_dump() for e in self._entities.values()],
            "pit_records": [r.model_dump() for r in self._pit_records],
        }
