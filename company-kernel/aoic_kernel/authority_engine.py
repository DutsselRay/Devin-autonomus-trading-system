from __future__ import annotations

from aoic_kernel.models import AgentCharter, Authority, DecisionProposal
from aoic_kernel.exceptions import AuthorityDenied


_AUTHORITY_ORDER = ["A0", "A1", "A2", "A3", "A4", "A5"]


class AuthorityEngine:
    """Resolves required authority and separation of duties."""

    def __init__(self) -> None:
        self._risk_state: str = "NORMAL"

    def set_global_risk_state(self, state: str) -> None:
        self._risk_state = state

    def required_authority_for(self, proposal: DecisionProposal) -> Authority:
        return proposal.required_authority

    def check(
        self,
        charter: AgentCharter,
        proposal: DecisionProposal,
        current_authority: Authority | None = None,
    ) -> Authority:
        required = self.required_authority_for(proposal)
        effective = current_authority or charter.authority_level

        if self._risk_state == "INCIDENT" and effective != Authority.A0:
            raise AuthorityDenied("Global risk state lowered to A0 during incident")

        if _AUTHORITY_ORDER.index(effective.value) < _AUTHORITY_ORDER.index(required.value):
            raise AuthorityDenied(
                f"Agent {charter.agent_id} has authority {effective} but {required} is required"
            )

        return effective

    def is_human_reserved(self, proposal: DecisionProposal) -> bool:
        return proposal.required_authority == Authority.A5

    def can_self_modify_authority(self, agent_id: str, target: str) -> bool:
        return False
