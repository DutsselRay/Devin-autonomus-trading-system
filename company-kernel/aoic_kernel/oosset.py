from __future__ import annotations

from datetime import datetime
from typing import Any

from aoic_kernel.exceptions import ContaminationError, OOSAccessDenied


class SealedOOSSet:
    """Immutable holdout dataset that discovery agents may not access."""

    def __init__(
        self,
        oos_set_id: str,
        data: Any,
        owner: str = "auditor",
    ) -> None:
        self.oos_set_id = oos_set_id
        self.data = data
        self.owner = owner
        self.created_at = datetime.now()
        self.contaminated_by: set[str] = set()
        self.access_log: list[dict[str, Any]] = []

    def access(self, agent_id: str) -> Any:
        if agent_id in self.contaminated_by:
            raise ContaminationError(
                f"OOS set {self.oos_set_id} was contaminated by {agent_id}"
            )
        if agent_id != self.owner and not agent_id.endswith("_auditor"):
            raise OOSAccessDenied(
                f"Agent {agent_id} is not allowed to access sealed OOS set {self.oos_set_id}"
            )
        self.access_log.append({"agent_id": agent_id, "at": datetime.now()})
        return self.data

    def mark_contaminated(self, agent_id: str, reason: str) -> None:
        self.contaminated_by.add(agent_id)
        self.access_log.append(
            {"agent_id": agent_id, "at": datetime.now(), "reason": reason, "contaminated": True}
        )


class SealedOOSSetManager:
    def __init__(self) -> None:
        self._sets: dict[str, SealedOOSSet] = {}
        self._counter = 0

    def create(self, data: Any, owner: str = "auditor") -> str:
        self._counter += 1
        oos_set_id = f"OOS-{self._counter:06d}"
        self._sets[oos_set_id] = SealedOOSSet(oos_set_id, data, owner=owner)
        return oos_set_id

    def get(self, oos_set_id: str) -> SealedOOSSet | None:
        return self._sets.get(oos_set_id)

    def access(self, oos_set_id: str, agent_id: str) -> Any:
        oos = self._sets.get(oos_set_id)
        if oos is None:
            raise OOSAccessDenied(f"Unknown OOS set {oos_set_id}")
        return oos.access(agent_id)

    def mark_contaminated(self, oos_set_id: str, agent_id: str, reason: str) -> None:
        oos = self._sets.get(oos_set_id)
        if oos is None:
            return
        oos.mark_contaminated(agent_id, reason)

    def is_contaminated(self, oos_set_id: str, agent_id: str) -> bool:
        oos = self._sets.get(oos_set_id)
        if oos is None:
            return False
        return agent_id in oos.contaminated_by
