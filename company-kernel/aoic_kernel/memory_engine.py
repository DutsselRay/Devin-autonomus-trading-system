from __future__ import annotations

from typing import Any

from aoic_kernel.models import DecisionProposal, PITRecord


class MemoryEngine:
    """PIT facts, decisions, outcomes and durable learnings."""

    def __init__(self) -> None:
        self._facts: list[PITRecord] = []
        self._decisions: dict[str, DecisionProposal] = {}
        self._learnings: list[dict[str, Any]] = []

    def store_fact(self, record: PITRecord) -> None:
        self._facts.append(record)

    def get_fact_as_of(self, entity_id: str, as_of: Any) -> PITRecord | None:
        for record in reversed(self._facts):
            if record.entity_id == entity_id and record.is_available_at(as_of):
                return record
        return None

    def store_decision(self, proposal: DecisionProposal) -> None:
        self._decisions[proposal.decision_id] = proposal

    def get_decision(self, decision_id: str) -> DecisionProposal | None:
        return self._decisions.get(decision_id)

    def dump_restore(self) -> dict[str, Any]:
        """Return a compact snapshot for disaster recovery."""
        return {
            "facts": [f.model_dump() for f in self._facts],
            "decisions": {k: v.model_dump() for k, v in self._decisions.items()},
            "learnings": self._learnings,
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        self._facts = [PITRecord(**f) for f in snapshot["facts"]]
        self._decisions = {k: DecisionProposal(**v) for k, v in snapshot["decisions"].items()}
        self._learnings = snapshot["learnings"]
