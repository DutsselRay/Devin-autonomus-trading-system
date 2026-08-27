from __future__ import annotations

from datetime import datetime, timezone

from aoic_kernel.exceptions import CharterInvalid
from aoic_kernel.models import AgentCharter


class AgentRegistry:
    """Identity, versions, status, owner and permissions."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentCharter] = {}
        self._history: dict[str, list[AgentCharter]] = {}

    def register(self, charter: AgentCharter) -> None:
        if charter.expiry < datetime.now(timezone.utc):
            raise CharterInvalid(f"Charter {charter.agent_id}@{charter.version} expired")
        self._history.setdefault(charter.agent_id, []).append(charter)
        if charter.status != "RETIRED":
            self._agents[charter.agent_id] = charter

    def get(self, agent_id: str) -> AgentCharter:
        if agent_id not in self._agents:
            raise CharterInvalid(f"Agent {agent_id} not found or retired")
        return self._agents[agent_id]

    def retire(self, agent_id: str) -> None:
        if agent_id in self._agents:
            self._agents[agent_id].status = "RETIRED"
            del self._agents[agent_id]

    def credentials_active(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def lineage(self, agent_id: str) -> list[AgentCharter]:
        return list(self._history.get(agent_id, []))
