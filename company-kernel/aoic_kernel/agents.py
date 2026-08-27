from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aoic_kernel.models import AgentCharter, Authority, DecisionProposal, DecisionStatus, Dissent
from aoic_kernel.kernel import CompanyKernel


class ExecutiveAgent:
    """Base wrapper for an AOIC executive agent."""

    def __init__(self, kernel: CompanyKernel, charter: AgentCharter) -> None:
        self.kernel = kernel
        self.charter = charter
        kernel.agents.register(charter)

    def propose(
        self,
        decision_id: str,
        objective: str,
        problem: str,
        recommendation: str,
        alternatives: list[str],
        required_authority: Authority,
        expected_value: dict[str, Any],
        cost: dict[str, Any],
        reversibility: str,
        regulatory_risk: str,
        rollback_plan: str,
        evidence: list[dict[str, Any]] | None = None,
        dissent: list[Dissent] | None = None,
    ) -> DecisionProposal:
        proposal = DecisionProposal(
            decision_id=decision_id,
            proposer=f"{self.charter.agent_id}@{self.charter.version}",
            objective=objective,
            problem=problem,
            recommendation=recommendation,
            alternatives=alternatives,
            evidence=evidence or [],
            expected_value=expected_value,
            cost=cost,
            reversibility=reversibility,
            regulatory_risk=regulatory_risk,
            rollback_plan=rollback_plan,
            required_authority=required_authority,
            dissent=dissent or [],
        )
        self.kernel.decisions.submit(self.charter, proposal)
        self.kernel.memory.store_decision(proposal)
        return proposal

    def can_execute(self, proposal: DecisionProposal) -> bool:
        try:
            self.kernel.authority.check(self.charter, proposal)
            return True
        except Exception:
            return False


class GlobalCEO(ExecutiveAgent):
    pass


class ProductCEO(ExecutiveAgent):
    pass


class BusinessCEO(ExecutiveAgent):
    pass


class CRCSO(ExecutiveAgent):
    """CRCSO can veto any proposal and lower global authority during incident."""

    def veto(self, proposal: DecisionProposal) -> None:
        proposal.status = DecisionStatus.REJECTED
        self.kernel.authority.set_global_risk_state("INCIDENT")
        self.kernel.audit.append(
            entry_id=f"AUD-{len(self.kernel.audit.entries)+1:06d}",
            event_type="CRCSO_VETO",
            actor=self.charter.agent_id,
            action="veto",
            target=proposal.decision_id,
            outcome="BLOCK",
            details={"reason": "CRCSO independent veto"},
        )
