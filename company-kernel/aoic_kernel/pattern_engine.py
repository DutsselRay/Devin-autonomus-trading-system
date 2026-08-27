from __future__ import annotations

from typing import Any

from aoic_kernel.models import Pattern, PatternStatus


class PatternEngine:
    """Lifecycle, genealogy and validation for falsifiable patterns."""

    VALID_PROMOTIONS: dict[PatternStatus, set[PatternStatus]] = {
        PatternStatus.IDEA: {PatternStatus.DISCOVERED, PatternStatus.RETIRED},
        PatternStatus.DISCOVERED: {PatternStatus.REPLICATED, PatternStatus.RETIRED},
        PatternStatus.REPLICATED: {PatternStatus.SEALED_OOS, PatternStatus.RETIRED},
        PatternStatus.SEALED_OOS: {PatternStatus.SHADOW_LIVE, PatternStatus.RETIRED},
        PatternStatus.SHADOW_LIVE: {PatternStatus.ELIGIBLE, PatternStatus.RETIRED},
        PatternStatus.ELIGIBLE: {PatternStatus.RETIRED},
        PatternStatus.RETIRED: set(),
    }

    def __init__(self) -> None:
        self._patterns: dict[str, Pattern] = {}

    def register(self, pattern: Pattern) -> None:
        self._patterns[pattern.pattern_id] = pattern

    def get(self, pattern_id: str) -> Pattern | None:
        return self._patterns.get(pattern_id)

    def promote(
        self,
        pattern_id: str,
        new_status: PatternStatus,
        experiment_id: str | None = None,
    ) -> Pattern:
        pattern = self._get_or_raise(pattern_id)
        if new_status not in self.VALID_PROMOTIONS.get(pattern.status, set()):
            raise ValueError(f"Invalid promotion {pattern.status.value} -> {new_status.value}")
        pattern.status = new_status
        if experiment_id:
            pattern.experiment_ids.append(experiment_id)
        return pattern

    def retire(self, pattern_id: str, reason: str) -> Pattern:
        pattern = self._get_or_raise(pattern_id)
        pattern.status = PatternStatus.RETIRED
        pattern.metadata["retired_reason"] = reason
        return pattern

    def eligible_for_entity(self, pattern_id: str, entity_id: str) -> bool:
        pattern = self._get_or_raise(pattern_id)
        if pattern.status == PatternStatus.RETIRED:
            return False
        return entity_id in pattern.eligible_universe

    def list_active(self) -> list[Pattern]:
        return [p for p in self._patterns.values() if p.status != PatternStatus.RETIRED]

    def snapshot(self) -> dict[str, Any]:
        return {pid: p.model_dump() for pid, p in self._patterns.items()}

    def _get_or_raise(self, pattern_id: str) -> Pattern:
        pattern = self._patterns.get(pattern_id)
        if pattern is None:
            raise KeyError(f"Unknown pattern {pattern_id}")
        return pattern
