from __future__ import annotations

from datetime import datetime
from typing import Callable

from aoic_kernel.entity_master import EntityMaster
from aoic_kernel.feature_store import TemporalFeatureStore


class SurvivorshipAwareUniverse:
    """Build a point-in-time universe excluding delisted and not-yet-listed entities."""

    def __init__(
        self,
        entity_master: EntityMaster,
        feature_store: TemporalFeatureStore,
    ) -> None:
        self.entity_master = entity_master
        self.feature_store = feature_store

    def build(
        self,
        as_of: datetime,
        filter_fn: Callable[[str, datetime], bool] | None = None,
    ) -> list[str]:
        active = self.entity_master.list_active(as_of)
        universe = [e.entity_id for e in active]
        if filter_fn is not None:
            universe = [eid for eid in universe if filter_fn(eid, as_of)]
        return sorted(universe)

    def member_at(self, entity_id: str, as_of: datetime) -> bool:
        entity = self.entity_master.get(entity_id)
        if entity is None:
            return False
        return entity.is_active_as_of(as_of)
